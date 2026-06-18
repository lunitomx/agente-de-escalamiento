"""Memory Engine — CRUD for memory_facts with trust-score decay.

Each fact is stored in the ``memory_facts`` table with a unique ``key``
and a JSON ``value`` containing::

    {
        "content":     str,       # the actual fact text
        "category":    str,       # optional category (e.g. "strategy", "people")
        "tags":        list[str], # searchable tags
        "source":      str,       # where the fact came from
        "trust_score": float,     # 0.0 – 1.0, decays over time
    }

Trust-score decay:  each call to ``get_relevant_facts`` applies a 0.01
decay to facts older than 7 days, and facts whose trust drops below 0.1
are excluded from results.

Usage::

    eng = MemoryEngine("data/escala.db")
    fid = eng.add_fact("Revenue grew 20% in Q1", "finance", ["q1","revenue"], "session-xyz")
    results = eng.search_facts("revenue", category="finance")
    context = eng.get_relevant_facts({"industry": "Tech", "stage": "growth"})
    eng.update_trust(fid, 0.1)

    # Backup / restore
    dump = eng.export_facts()
    eng.import_facts(dump)
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sqlite3

_TRUST_DECAY_RATE = 0.01  # per week since last update
_TRUST_MIN_VISIBLE = 0.1
_DECAY_SECONDS = 7 * 86400  # one week in seconds


class MemoryEngine:
    """Manage memory_facts with trust-score semantics."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = _resolve_path(db_path)
        # Ensure tables exist (uses shared connection cache)
        from .schema import init_db

        if self._db_path not in _conn_cache:
            _conn_cache[self._db_path] = init_db(self._db_path)

    # ── connection helpers ───────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        return _conn_cache[self._db_path]

    # ── add_fact ─────────────────────────────────────────────────────

    def add_fact(
        self,
        content: str,
        category: str = "",
        tags: list[str] | None = None,
        source: str = "",
    ) -> int:
        """Insert a new fact. Returns the new row id.

        Args:
            content:  The fact text.
            category: Optional grouping (e.g. "strategy", "people").
            tags:     Optional list of searchable tags.
            source:   Where the fact originated (session id, etc.).
        """
        key = f"fact:{uuid.uuid4().hex[:12]}"
        tags = tags or []
        value = json.dumps(
            {
                "content": content,
                "category": category,
                "tags": tags,
                "source": source,
                "trust_score": 1.0,
            },
            ensure_ascii=False,
        )
        conn = self._conn()
        conn.execute(
            "INSERT INTO memory_facts (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM memory_facts WHERE key = ?", (key,)
        ).fetchone()
        assert row is not None
        return row["id"]

    # ── search_facts ─────────────────────────────────────────────────

    def search_facts(
        self,
        query: str,
        category: str | None = None,
        tags: list[str] | None = None,
        min_trust: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Return facts matching *query* (keyword search on content).

        Args:
            query:     Substring to look for in fact content.
            category:  If given, only match facts in this category.
            tags:      If given, facts must have at least one matching tag.
            min_trust: Only return facts with trust_score >= this value.
        """
        conn = self._conn()
        rows = conn.execute(
            "SELECT id, key, value, created_at, updated_at FROM memory_facts"
        ).fetchall()

        results: list[dict[str, Any]] = []
        query_lower = query.lower()
        tag_set = {t.lower() for t in tags} if tags else None

        for row in rows:
            try:
                data = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                continue
            content = data.get("content", "")
            fact_cat = data.get("category", "")
            fact_tags = [t.lower() for t in data.get("tags", [])]
            trust = data.get("trust_score", 1.0)

            if trust < min_trust:
                continue
            if category is not None and fact_cat.lower() != category.lower():
                continue
            if tag_set is not None and not tag_set.intersection(fact_tags):
                continue
            if query_lower not in content.lower():
                continue

            results.append(_fact_row_to_dict(row, data))

        return results

    # ── get_relevant_facts ───────────────────────────────────────────

    def get_relevant_facts(
        self,
        company_context: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return the most relevant facts for context injection.

        Applies trust-score decay to facts older than 7 days before
        ranking.  Facts that have decayed below the visibility threshold
        are excluded.

        Ranking:  trust_score DESC, then updated_at DESC.
        """
        _ = company_context  # reserved for future semantic matching
        self._apply_decay()

        conn = self._conn()
        rows = conn.execute(
            "SELECT id, key, value, created_at, updated_at FROM memory_facts"
        ).fetchall()

        scored: list[dict[str, Any]] = []
        for row in rows:
            try:
                data = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                continue
            if data.get("trust_score", 1.0) < _TRUST_MIN_VISIBLE:
                continue
            scored.append(_fact_row_to_dict(row, data))

        # Sort by trust_score DESC, then updated_at DESC
        scored.sort(
            key=lambda f: (f.get("trust_score", 0), f.get("updated_at", "")),
            reverse=True,
        )
        return scored[:limit]

    # ── update_trust ─────────────────────────────────────────────────

    def update_trust(self, fact_id: int, delta: float) -> dict[str, Any] | None:
        """Adjust a fact's trust_score by *delta* (positive or negative).

        Clamped to [0.0, 1.0].  Returns the updated fact dict or None.
        """
        conn = self._conn()
        row = conn.execute(
            "SELECT id, key, value FROM memory_facts WHERE id = ?", (fact_id,)
        ).fetchone()
        if row is None:
            return None

        try:
            data = json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return None

        old_trust = data.get("trust_score", 1.0)
        new_trust = max(0.0, min(1.0, old_trust + delta))
        data["trust_score"] = new_trust

        conn.execute(
            "UPDATE memory_facts SET value = ?, updated_at = datetime('now') WHERE id = ?",
            (json.dumps(data, ensure_ascii=False), fact_id),
        )
        conn.commit()

        return _fact_row_to_dict(
            conn.execute(
                "SELECT id, key, value, created_at, updated_at FROM memory_facts WHERE id = ?",
                (fact_id,),
            ).fetchone(),
            data,
        )

    # ── export / import ──────────────────────────────────────────────

    def export_facts(self) -> list[dict[str, Any]]:
        """Export all facts as a JSON-serializable list of dicts."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT id, key, value, created_at, updated_at FROM memory_facts ORDER BY id"
        ).fetchall()
        return [_fact_row_to_dict(r, json.loads(r["value"])) for r in rows]

    def import_facts(self, json_data: list[dict[str, Any]]) -> int:
        """Import facts from a previously-exported JSON list.

        Existing facts with the same ``key`` are updated; new keys are
        inserted.  Returns the count of imported facts.
        """
        conn = self._conn()
        count = 0
        for item in json_data:
            key = item.get("key", "")
            if not key:
                key = f"fact:{uuid.uuid4().hex[:12]}"

            value_data: dict[str, Any] = {
                "content": item.get("content", ""),
                "category": item.get("category", ""),
                "tags": item.get("tags", []),
                "source": item.get("source", ""),
                "trust_score": item.get("trust_score", 1.0),
            }
            value_str = json.dumps(value_data, ensure_ascii=False)

            existing = conn.execute(
                "SELECT id FROM memory_facts WHERE key = ?", (key,)
            ).fetchone()

            if existing:
                conn.execute(
                    "UPDATE memory_facts SET value = ?, updated_at = datetime('now') WHERE key = ?",
                    (value_str, key),
                )
            else:
                conn.execute(
                    "INSERT INTO memory_facts (key, value) VALUES (?, ?)",
                    (key, value_str),
                )
            count += 1

        conn.commit()
        return count

    # ── internal ─────────────────────────────────────────────────────

    def _apply_decay(self) -> None:
        """Reduce trust_score for facts older than 7 days."""
        conn = self._conn()
        rows = conn.execute(
            "SELECT id, key, value, updated_at FROM memory_facts"
        ).fetchall()

        now_ts = time.time()
        updates: list[tuple[str, int]] = []

        for row in rows:
            try:
                data = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                continue
            updated_str = row["updated_at"]
            if not updated_str:
                continue
            try:
                # SQLite datetime → epoch seconds
                updated_dt = datetime.strptime(updated_str, "%Y-%m-%d %H:%M:%S")
                age_seconds = (
                    now_ts - updated_dt.replace(tzinfo=timezone.utc).timestamp()
                )
            except (ValueError, OSError):
                continue

            weeks_old = age_seconds / _DECAY_SECONDS
            decay = weeks_old * _TRUST_DECAY_RATE
            old_trust = data.get("trust_score", 1.0)
            new_trust = max(0.0, old_trust - decay)

            if abs(new_trust - old_trust) > 0.001:
                data["trust_score"] = new_trust
                new_value = json.dumps(data, ensure_ascii=False)
                updates.append((new_value, row["id"]))

        for new_value, fid in updates:
            conn.execute(
                "UPDATE memory_facts SET value = ?, updated_at = datetime('now') WHERE id = ?",
                (new_value, fid),
            )

        if updates:
            conn.commit()


# ── helpers ──────────────────────────────────────────────────────────

_conn_cache: dict[str, sqlite3.Connection] = {}


def _resolve_path(db_path: str) -> str:
    if db_path == ":memory:" or db_path.startswith("file:"):
        return db_path
    return str(Path(db_path).resolve())


def _fact_row_to_dict(row: sqlite3.Row, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "key": row["key"],
        "content": data.get("content", ""),
        "category": data.get("category", ""),
        "tags": data.get("tags", []),
        "source": data.get("source", ""),
        "trust_score": data.get("trust_score", 1.0),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
