"""SQLite schema for Escala Server — persistence layer for coaching data.

Schema version is tracked in the _meta table.
Tables: companies, worksheets, sessions, changes_log,
        memory_facts, entities, relationships.
"""

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

DDL_STATEMENTS = [
    # ── Meta / version tracking ──────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS _meta (
        key    TEXT PRIMARY KEY,
        value  TEXT NOT NULL
    )
    """,

    # ── companies ────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS companies (
        id         TEXT PRIMARY KEY,
        name       TEXT NOT NULL,
        industry   TEXT DEFAULT '',
        metadata   TEXT DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── worksheets (versioned — each save creates a new row) ─────────
    """
    CREATE TABLE IF NOT EXISTS worksheets (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        category    TEXT NOT NULL,
        tool        TEXT NOT NULL,
        data        TEXT NOT NULL DEFAULT '{}',
        session_id  TEXT DEFAULT NULL,
        version     INTEGER NOT NULL DEFAULT 1,
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── sessions ─────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id          TEXT PRIMARY KEY,
        company_id  TEXT DEFAULT NULL,
        status      TEXT DEFAULT 'active',
        metadata    TEXT DEFAULT '{}',
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── changes_log ──────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS changes_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id  TEXT DEFAULT NULL,
        session_id  TEXT DEFAULT NULL,
        category    TEXT DEFAULT NULL,
        tool        TEXT DEFAULT NULL,
        field       TEXT NOT NULL,
        old_value   TEXT DEFAULT NULL,
        new_value   TEXT DEFAULT NULL,
        diff_type   TEXT DEFAULT 'update',
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── memory_facts ─────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS memory_facts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        key         TEXT NOT NULL UNIQUE,
        value       TEXT NOT NULL DEFAULT '',
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── entities ─────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS entities (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        type        TEXT NOT NULL,
        name        TEXT NOT NULL,
        properties  TEXT DEFAULT '{}',
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,

    # ── relationships ────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS relationships (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        source_entity_id  INTEGER NOT NULL,
        target_entity_id  INTEGER NOT NULL,
        relation_type     TEXT NOT NULL,
        properties        TEXT DEFAULT '{}',
        created_at        TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
]

# ── Indexes (created separately after tables) ────────────────────────
INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_worksheets_category_tool ON worksheets(category, tool)",
    "CREATE INDEX IF NOT EXISTS idx_worksheets_category_version ON worksheets(category, version)",
    "CREATE INDEX IF NOT EXISTS idx_worksheets_session ON worksheets(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_sessions_company ON sessions(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_changes_log_session ON changes_log(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_changes_log_company ON changes_log(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_memory_facts_key ON memory_facts(key)",
    "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)",
    "CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relation_type)",
]


def _ensure_dir(db_path: str) -> None:
    """Create parent directories for the database file if needed."""
    parent = Path(db_path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def init_db(db_path: str) -> sqlite3.Connection:
    """Create/upgrade the Escala SQLite database and return a connection.

    Args:
        db_path: Path to the SQLite database file (e.g. 'data/escala.db')
                 or a URI like 'file:name?mode=memory&cache=shared'.

    Returns:
        An open sqlite3.Connection with WAL mode, foreign keys enabled,
        and the latest schema in place.
    """
    if db_path != ":memory:" and not db_path.startswith("file:"):
        _ensure_dir(db_path)

    uri = db_path.startswith("file:")
    conn = sqlite3.connect(db_path, uri=uri)

    # Recommended settings
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # ── Run DDL ──────────────────────────────────────────────────────
    for stmt in DDL_STATEMENTS:
        conn.execute(stmt)

    # ── Schema version check / upgrade ───────────────────────────────
    row = conn.execute(
        "SELECT value FROM _meta WHERE key = 'schema_version'"
    ).fetchone()

    if row is None:
        conn.execute(
            "INSERT INTO _meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
    else:
        current = int(row[0])
        if current < SCHEMA_VERSION:
            # Future: run migration steps here
            conn.execute(
                "UPDATE _meta SET value = ? WHERE key = 'schema_version'",
                (str(SCHEMA_VERSION),),
            )

    # ── Create indexes ───────────────────────────────────────────────
    for stmt in INDEX_STATEMENTS:
        conn.execute(stmt)

    conn.commit()
    return conn
