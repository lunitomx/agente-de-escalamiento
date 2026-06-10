"""YAML migration — import .scaleup/ data into SQLite.

Reads existing YAML data from .scaleup/my-company/ and imports
into the Escala SQLite database. Idempotent — can be run multiple
times safely.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


# ─── Parse YAML/JSON file ──────────────────────────────────────


def read_yaml_file(path: Path) -> Any:
    """Read a .yaml or .json file and return parsed data.

    Uses PyYAML for .yaml files, json for .json.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text)
def migrate_from_yaml(db_path: str, yaml_root: str) -> dict[str, Any]:
    """Import .scaleup/ YAML data into SQLite database.

    Reads YAML files from yaml_root/my-company/ and imports:
    - Profile (profile.md) → companies table
    - Pulse history (pulse-history.yaml) → worksheet data
    - Session files (sessions/*.md) → sessions table
    - Context data (context/*.yaml) → worksheets

    Idempotent — uses INSERT OR IGNORE / ON CONFLICT to avoid duplicates.
    Writes a migration log to ~/.escala/migration.log.

    Args:
        db_path: Path to the SQLite database file
        yaml_root: Root of the .scaleup/ directory

    Returns:
        Summary dict with import counts and log path
    """
    import hashlib

    from .daos import init_db

    yaml_path = Path(yaml_root).expanduser().resolve()
    db_path_resolved = Path(db_path).expanduser().resolve()
    db_path_str = str(db_path_resolved)

    # Initialize database schema
    init_db(db_path_str)

    log_entries: list[str] = []
    now = datetime.now().isoformat()
    log_entries.append(f"=== Migration started at {now} ===")
    log_entries.append(f"Source: {yaml_path}")
    log_entries.append(f"Target: {db_path_str}")

    counts = {
        "companies": 0,
        "worksheets": 0,
        "sessions": 0,
        "skipped": 0,
        "errors": 0,
    }

    conn = sqlite3.connect(db_path_str)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        company_dir = yaml_path / "my-company"
        if not company_dir.is_dir():
            log_entries.append(f"WARNING: {company_dir} not found, no company data imported")
        else:
            # Import profile
            profile_path = company_dir / "profile.md"
            if profile_path.exists():
                try:
                    profile_text = profile_path.read_text(encoding="utf-8")
                    # Derive a stable ID from the file path
                    company_id = hashlib.md5(str(profile_path).encode()).hexdigest()[:8]
                    profile_data = {
                        "name": "My Company",
                        "profile": profile_text,
                        "source": "profile.md",
                    }
                    data_json = json.dumps(profile_data, ensure_ascii=False)
                    conn.execute(
                        "INSERT OR IGNORE INTO companies (id, data_json) VALUES (?, ?)",
                        (company_id, data_json),
                    )
                    if conn.total_changes > 0:
                        counts["companies"] += 1
                        log_entries.append(f"OK: Imported profile.md → company {company_id}")
                    else:
                        counts["skipped"] += 1
                        log_entries.append(f"SKIP: profile.md already exists")
                except Exception as e:
                    counts["errors"] += 1
                    log_entries.append(f"ERROR: profile.md: {e}")

            # Import pulse history as worksheet
            pulse_path = company_dir / "pulse-history.yaml"
            if pulse_path.exists():
                try:
                    data = read_yaml_file(pulse_path)
                    data_json = json.dumps(data, ensure_ascii=False)
                    conn.execute(
                        """INSERT OR REPLACE INTO worksheets (category, tool, data_json)
                           VALUES (?, ?, ?)""",
                        ("company", "pulse-history", data_json),
                    )
                    counts["worksheets"] += 1
                    log_entries.append("OK: Imported pulse-history.yaml")
                except Exception as e:
                    counts["errors"] += 1
                    log_entries.append(f"ERROR: pulse-history.yaml: {e}")

            # Import context YAML files as worksheets
            context_dir = company_dir / "context"
            if context_dir.is_dir():
                for ctx_file in sorted(context_dir.glob("*.yaml")):
                    try:
                        data = read_yaml_file(ctx_file)
                        tool_name = ctx_file.stem
                        data_json = json.dumps(data, ensure_ascii=False)
                        conn.execute(
                            """INSERT OR REPLACE INTO worksheets (category, tool, data_json)
                               VALUES (?, ?, ?)""",
                            ("context", tool_name, data_json),
                        )
                        counts["worksheets"] += 1
                        log_entries.append(f"OK: Imported context/{ctx_file.name}")
                    except Exception as e:
                        counts["errors"] += 1
                        log_entries.append(f"ERROR: context/{ctx_file.name}: {e}")

            # Import quarterly focus and annual goal
            for fname, tool in [("quarterly-focus.md", "quarterly-focus"), ("annual-goal.md", "annual-goal")]:
                fpath = company_dir / fname
                if fpath.exists():
                    try:
                        text = fpath.read_text(encoding="utf-8")
                        data = {"content": text}
                        data_json = json.dumps(data, ensure_ascii=False)
                        conn.execute(
                            """INSERT OR REPLACE INTO worksheets (category, tool, data_json)
                               VALUES (?, ?, ?)""",
                            ("company", tool, data_json),
                        )
                        counts["worksheets"] += 1
                        log_entries.append(f"OK: Imported {fname}")
                    except Exception as e:
                        counts["errors"] += 1
                        log_entries.append(f"ERROR: {fname}: {e}")

            # Import task board
            tasks_path = company_dir / "tasks.md"
            if tasks_path.exists():
                try:
                    text = tasks_path.read_text(encoding="utf-8")
                    data = {"content": text}
                    data_json = json.dumps(data, ensure_ascii=False)
                    conn.execute(
                        """INSERT OR REPLACE INTO worksheets (category, tool, data_json)
                           VALUES (?, ?, ?)""",
                        ("company", "tasks", data_json),
                    )
                    counts["worksheets"] += 1
                    log_entries.append("OK: Imported tasks.md")
                except Exception as e:
                    counts["errors"] += 1
                    log_entries.append(f"ERROR: tasks.md: {e}")

            # Import sessions
            sessions_dir = company_dir / "sessions"
            if sessions_dir.is_dir():
                for session_file in sorted(sessions_dir.glob("*.md")):
                    try:
                        text = session_file.read_text(encoding="utf-8")
                        # Extract frontmatter if present
                        session_data = {"raw": text}
                        if text.startswith("---"):
                            parts = text.split("---", 2)
                            if len(parts) >= 3:
                                session_data["frontmatter"] = parts[1].strip()
                                session_data["body"] = parts[2].strip()
                        data_json = json.dumps(session_data, ensure_ascii=False)
                        session_id = hashlib.md5(str(session_file).encode()).hexdigest()[:8]
                        conn.execute(
                            "INSERT OR IGNORE INTO sessions (id, data_json) VALUES (?, ?)",
                            (session_id, data_json),
                        )
                        if conn.total_changes > 0:
                            counts["sessions"] += 1
                            log_entries.append(f"OK: Imported sessions/{session_file.name}")
                        else:
                            counts["skipped"] += 1
                            log_entries.append(f"SKIP: sessions/{session_file.name} already exists")
                    except Exception as e:
                        counts["errors"] += 1
                        log_entries.append(f"ERROR: sessions/{session_file.name}: {e}")

        # Import knowledge base worksheets
        knowledge_dir = yaml_path / "knowledge"
        if knowledge_dir.is_dir():
            for decision in ["strategy", "people", "execution", "cash"]:
                ws_dir = knowledge_dir / decision / "worksheets"
                if ws_dir.is_dir():
                    for ws_file in sorted(ws_dir.glob("*.yaml")):
                        try:
                            data = read_yaml_file(ws_file)
                            tool_name = ws_file.stem
                            data_json = json.dumps(data, ensure_ascii=False)
                            conn.execute(
                                """INSERT OR REPLACE INTO worksheets (category, tool, data_json)
                                   VALUES (?, ?, ?)""",
                                (decision, tool_name, data_json),
                            )
                            counts["worksheets"] += 1
                            log_entries.append(
                                f"OK: Imported knowledge/{decision}/worksheets/{ws_file.name}"
                            )
                        except Exception as e:
                            counts["errors"] += 1
                            log_entries.append(
                                f"ERROR: knowledge/{decision}/worksheets/{ws_file.name}: {e}"
                            )

        conn.commit()

    except Exception as e:
        log_entries.append(f"FATAL: {e}")
        counts["errors"] += 1
    finally:
        conn.close()

    log_entries.append(f"=== Migration complete: {counts} ===")

    # Write migration log
    log_dir = Path.home() / ".escala"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "migration.log"
    log_text = "\n".join(log_entries) + "\n"
    if log_path.exists():
        log_text = log_path.read_text() + log_text
    log_path.write_text(log_text)

    return {
        "status": "ok",
        "counts": counts,
        "log_path": str(log_path),
    }
