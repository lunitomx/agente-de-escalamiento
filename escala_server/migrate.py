"""YAML migration — import .scaleup/ data into SQLite.

Reads existing YAML data from .scaleup/my-company/ and imports
into the Escala SQLite database. Idempotent — can be run multiple
times safely.

Since PyYAML is not available, this module includes a simple
YAML parser that handles the subset of YAML used in .scaleup/.
"""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── Simple YAML parser ────────────────────────────────────────


def _parse_simple_yaml(text: str) -> Any:
    """Parse a simple YAML document.

    Handles the subset of YAML used in .scaleup/ files:
    - Comments (#)
    - Key: value pairs (bare, quoted, or numeric values)
    - Nested dicts via indentation (2 or 4 spaces)
    - Lists with - items
    - Folded block scalars with >
    - Empty lists: []
    """
    lines = text.split("\n")
    return _parse_yaml_value(lines, 0, -1)[0]


def _parse_yaml_value(lines: list[str], start: int, indent: int) -> tuple[Any, int]:
    """Parse a YAML value starting at `start`, with parent `indent`.

    Returns (value, next_line_index).
    """
    idx = start
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # Skip blank lines and comment-only lines
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue

        current_indent = len(line) - len(line.lstrip(" "))

        # If we're inside a block and indent is less than parent, we're done
        if indent >= 0 and current_indent < indent:
            return _make_default(indent), idx

        # List item
        if stripped.startswith("- "):
            return _parse_yaml_list(lines, idx, indent)

        # Key: value or Key:
        key_match = re.match(r"^([\w_-]+)\s*:(.*)$", stripped)
        if key_match:
            return _parse_yaml_mapping(lines, idx, indent)

        # Bare value (shouldn't normally happen at top level)
        idx += 1

    return None, idx


def _make_default(indent: int) -> Any:
    """Return a sensible default for an empty block."""
    return {}


def _parse_yaml_list(
    lines: list[str], start: int, parent_indent: int
) -> tuple[list[Any], int]:
    """Parse a YAML list starting at `start`."""
    result = []
    idx = start

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            idx += 1
            continue

        current_indent = len(line) - len(line.lstrip(" "))

        if current_indent < parent_indent:
            break

        if stripped.startswith("- "):
            item_text = stripped[2:]
            parent_indent + 2

            if ":" in item_text and not item_text.startswith(("{", "[", '"', "'")):
                # Inline mapping: "- key: value"
                # Check next line for indented content or parse inline
                next_idx = idx + 1
                if next_idx < len(lines):
                    next_stripped = lines[next_idx].strip()
                    next_indent = (
                        len(lines[next_idx]) - len(lines[next_idx].lstrip(" "))
                        if next_stripped
                        else 0
                    )
                    if next_stripped and next_indent > current_indent:
                        # Sub-block following list item
                        sub_val, idx = _parse_yaml_value(lines, idx + 1, current_indent)
                        if isinstance(sub_val, dict) and item_text.strip():
                            # Merge inline key-value into sub-block
                            parts = item_text.split(":", 1)
                            inline_key = _strip_quotes(parts[0].strip())
                            inline_value = (
                                _parse_scalar(parts[1].strip())
                                if len(parts) > 1
                                else None
                            )
                            sub_val[inline_key] = inline_value
                        result.append(sub_val)
                        continue

                # Try inline mapping
                inline = _parse_inline_mapping(item_text)
                if inline is not None:
                    result.append(inline)
                else:
                    result.append(_parse_scalar(item_text.strip()))
            else:
                # Value (scalar) or sub-block
                next_idx = idx + 1
                if next_idx < len(lines):
                    next_stripped = lines[next_idx].strip()
                    next_indent = (
                        len(lines[next_idx]) - len(lines[next_idx].lstrip(" "))
                        if next_stripped
                        else 0
                    )
                    if (
                        next_stripped
                        and next_indent > current_indent
                        and not next_stripped.startswith("- ")
                    ):
                        # Sub-block
                        sub_val, idx = _parse_yaml_value(lines, idx + 1, current_indent)
                        result.append(sub_val)
                        continue

                # Bare scalar value
                result.append(_parse_scalar(item_text.strip()))
            idx += 1
        else:
            idx += 1

    return result, idx


def _parse_yaml_mapping(
    lines: list[str], start: int, parent_indent: int
) -> tuple[dict[str, Any], int]:
    """Parse a YAML mapping (key: value pairs) at same indent level."""
    result: dict[str, Any] = {}
    idx = start
    base_indent: int | None = None  # Indent of first key, used to detect siblings

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            idx += 1
            continue

        current_indent = len(line) - len(line.lstrip(" "))

        # If indent is less than parent, we're done with this block
        if current_indent < parent_indent:
            break

        # A line shallower than the first key belongs to the parent block.
        if base_indent is not None and current_indent < base_indent:
            break

        # If we've established a base indent, skip lines that are deeper (sub-blocks)
        if base_indent is not None and current_indent > base_indent:
            idx += 1
            continue

        # List item at this level — let caller handle it
        if stripped.startswith("- "):
            break

        # Key: value
        key_match = re.match(r"^([\w_-]+)\s*:\s*(.*)$", stripped)
        if key_match:
            # Set base indent from first key
            if base_indent is None:
                base_indent = current_indent

            key = key_match.group(1)
            value_part = key_match.group(2).strip()

            if not value_part:
                # Empty value (key:) — check for sub-block or list
                next_idx = idx + 1
                if next_idx < len(lines):
                    next_line = lines[next_idx]
                    next_stripped = next_line.strip()
                    next_indent = (
                        len(next_line) - len(next_line.lstrip(" "))
                        if next_stripped
                        else 0
                    )
                    has_indented_child = next_indent > current_indent
                    has_indentless_sequence = (
                        next_indent == current_indent and next_stripped.startswith("- ")
                    )
                    if next_stripped and (
                        has_indented_child or has_indentless_sequence
                    ):
                        sub_val, idx = _parse_yaml_value(lines, idx + 1, current_indent)
                        result[key] = sub_val
                        continue
                result[key] = None
                idx += 1
                continue

            # Inline value
            if value_part == "[]":
                result[key] = []
                idx += 1
                continue

            if value_part.startswith((">", "|")):
                # Multi-line string — collect continuation lines
                result[key] = _collect_block_string(lines, idx, current_indent)
                idx += 1
                while idx < len(lines):
                    l = lines[idx]
                    ls = l.strip()
                    li = len(l) - len(l.lstrip(" "))
                    if not ls or ls.startswith("#") or li > current_indent:
                        idx += 1
                    else:
                        break
                continue

            # Check if next line is indented (sub-block for non-scalar values)
            next_idx = idx + 1
            has_sub_block = False
            if next_idx < len(lines):
                next_line = lines[next_idx]
                next_stripped = next_line.strip()
                next_indent = (
                    len(next_line) - len(next_line.lstrip(" ")) if next_stripped else 0
                )
                if (
                    next_stripped
                    and next_indent > current_indent
                    and not next_stripped.startswith("- ")
                ):
                    has_sub_block = True

            if has_sub_block:
                # Sub-mapping or sub-list
                sub_val, idx = _parse_yaml_value(lines, idx + 1, current_indent)
                result[key] = sub_val
                continue

            result[key] = _parse_scalar(value_part)
            idx += 1
        else:
            idx += 1

    return result, idx


def _collect_block_string(lines: list[str], start: int, parent_indent: int) -> str:
    """Collect continuation lines of a > or | block scalar."""
    parts = []
    idx = start + 1
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue
        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent > parent_indent:
            parts.append(stripped)
            idx += 1
        else:
            break
    return " ".join(parts)


def _parse_inline_mapping(text: str) -> dict[str, Any] | None:
    """Try to parse text like 'key: value' as a 1-key mapping."""
    match = re.match(r"^([\w_-]+)\s*:\s*(.*)$", text.strip())
    if match:
        return {match.group(1): _parse_scalar(match.group(2).strip())}
    return None


def _parse_scalar(text: str) -> Any:
    """Parse a YAML scalar value."""
    text = text.strip()

    # Remove trailing comments
    if " #" in text:
        text = text[: text.rindex(" #")].strip()

    # Quoted strings
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]

    # Booleans
    if text.lower() in ("true", "yes", "on"):
        return True
    if text.lower() in ("false", "no", "off"):
        return False

    # Null
    if text.lower() in ("null", "none", "~"):
        return None

    # Integers
    try:
        return int(text)
    except ValueError:
        pass

    # Floats
    try:
        return float(text)
    except ValueError:
        pass

    return text


def _strip_quotes(text: str) -> str:
    """Remove surrounding quotes from a string."""
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    return text


# ─── Parse YAML/JSON file ──────────────────────────────────────


def read_yaml_file(path: Path) -> Any:
    """Read a .yaml or .json file and return parsed data.

    Uses simple YAML parser for .yaml files, json for .json.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return _parse_simple_yaml(text)


# ─── Migration ─────────────────────────────────────────────────


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
    now = datetime.now().isoformat()  # noqa: DTZ005 - preserves legacy local log timestamps
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
            log_entries.append(
                f"WARNING: {company_dir} not found, no company data imported"
            )
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
                        log_entries.append(
                            f"OK: Imported profile.md → company {company_id}"
                        )
                    else:
                        counts["skipped"] += 1
                        log_entries.append("SKIP: profile.md already exists")
                except Exception as e:  # noqa: BLE001 - migration records and continues per artifact
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
                except Exception as e:  # noqa: BLE001 - migration records and continues per artifact
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
                    except Exception as e:  # noqa: BLE001 - migration records and continues per artifact
                        counts["errors"] += 1
                        log_entries.append(f"ERROR: context/{ctx_file.name}: {e}")

            # Import quarterly focus and annual goal
            for fname, tool in [
                ("quarterly-focus.md", "quarterly-focus"),
                ("annual-goal.md", "annual-goal"),
            ]:
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
                    except Exception as e:  # noqa: BLE001 - migration records and continues per artifact
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
                except Exception as e:  # noqa: BLE001 - migration records and continues per artifact
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
                        session_id = hashlib.md5(
                            str(session_file).encode()
                        ).hexdigest()[:8]
                        conn.execute(
                            "INSERT OR IGNORE INTO sessions (id, data_json) VALUES (?, ?)",
                            (session_id, data_json),
                        )
                        if conn.total_changes > 0:
                            counts["sessions"] += 1
                            log_entries.append(
                                f"OK: Imported sessions/{session_file.name}"
                            )
                        else:
                            counts["skipped"] += 1
                            log_entries.append(
                                f"SKIP: sessions/{session_file.name} already exists"
                            )
                    except Exception as e:  # noqa: BLE001 - migration records and continues per artifact
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
                        except Exception as e:  # noqa: BLE001 - migration records and continues per artifact
                            counts["errors"] += 1
                            log_entries.append(
                                f"ERROR: knowledge/{decision}/worksheets/{ws_file.name}: {e}"
                            )

        conn.commit()

    except Exception as e:  # noqa: BLE001 - migration records and continues per artifact
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
