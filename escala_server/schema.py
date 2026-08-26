"""SQLite schema for Escala Server — persistence layer for coaching data.

Schema version is tracked in the _meta table.
Tables: companies, worksheets, sessions, changes_log,
        memory_facts, entities, relationships.
"""

import hashlib
import json
import re
import sqlite3
from functools import lru_cache
from pathlib import Path

SCHEMA_VERSION = 12

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
    """
    CREATE TABLE IF NOT EXISTS migration_sources (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        relative_path  TEXT NOT NULL,
        content_sha256 TEXT NOT NULL,
        import_schema  INTEGER NOT NULL,
        source_kind    TEXT NOT NULL,
        migrated_at    TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(relative_path, content_sha256, import_schema)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS migration_applications (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        relative_path  TEXT NOT NULL,
        content_sha256 TEXT NOT NULL,
        import_schema  INTEGER NOT NULL,
        source_kind    TEXT NOT NULL,
        applied_at     TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS migration_fact_applications (
        id                       INTEGER PRIMARY KEY AUTOINCREMENT,
        fact_key                 TEXT NOT NULL,
        value_sha256             TEXT NOT NULL,
        migration_application_id INTEGER NOT NULL,
        applied_at               TEXT NOT NULL,
        UNIQUE(fact_key, migration_application_id),
        FOREIGN KEY(migration_application_id) REFERENCES migration_applications(id)
    )
    """,
    # ── Explicitly confirmed session memory (v5) ─────────────────────
    """
    CREATE TABLE IF NOT EXISTS project_memory_sessions (
        id           TEXT PRIMARY KEY,
        status       TEXT NOT NULL CHECK(status IN ('open', 'closed')),
        opened_at    TEXT NOT NULL DEFAULT (datetime('now')),
        closed_at    TEXT DEFAULT NULL,
        close_reason TEXT DEFAULT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS session_memory_proposals (
        id                TEXT PRIMARY KEY,
        fingerprint       TEXT NOT NULL UNIQUE,
        session_id        TEXT NOT NULL,
        kind              TEXT NOT NULL CHECK(kind IN ('fact', 'decision', 'pattern')),
        statement         TEXT NOT NULL,
        origin            TEXT NOT NULL CHECK(origin = 'explicit_user_statement'),
        observation_ids   TEXT NOT NULL,
        replaces_entry_id TEXT DEFAULT NULL,
        response_state    TEXT NOT NULL CHECK(response_state IN ('proposed', 'confirmed', 'rejected')),
        created_at        TEXT NOT NULL DEFAULT (datetime('now')),
        responded_at      TEXT DEFAULT NULL,
        provenance_format_version INTEGER NOT NULL DEFAULT 1 CHECK(provenance_format_version = 1),
        FOREIGN KEY(session_id) REFERENCES project_memory_sessions(id),
        FOREIGN KEY(replaces_entry_id) REFERENCES confirmed_memory_entries(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS confirmed_memory_entries (
        id                      TEXT PRIMARY KEY,
        proposal_id             TEXT NOT NULL UNIQUE,
        session_id              TEXT NOT NULL,
        kind                    TEXT NOT NULL CHECK(kind IN ('fact', 'decision', 'pattern')),
        statement               TEXT NOT NULL,
        source                  TEXT NOT NULL,
        confirmation_confidence REAL NOT NULL CHECK(confirmation_confidence = 1.0),
        confidence_reason       TEXT NOT NULL CHECK(confidence_reason = 'explicit_confirmation'),
        status                  TEXT NOT NULL CHECK(status IN ('active', 'superseded')),
        replaces_entry_id       TEXT DEFAULT NULL,
        confirmed_at            TEXT NOT NULL DEFAULT (datetime('now')),
        entry_format_version    INTEGER NOT NULL DEFAULT 1 CHECK(entry_format_version = 1),
        provenance_format_version INTEGER NOT NULL DEFAULT 1 CHECK(provenance_format_version = 1),
        FOREIGN KEY(proposal_id) REFERENCES session_memory_proposals(id),
        FOREIGN KEY(session_id) REFERENCES project_memory_sessions(id),
        FOREIGN KEY(replaces_entry_id) REFERENCES confirmed_memory_entries(id)
    )
    """,
    # ── Shared workspace index (v7, always local) ───────────────────
    """
    CREATE TABLE IF NOT EXISTS workspace_documents (
        workspace_id   TEXT NOT NULL,
        relative_path  TEXT NOT NULL,
        content_sha256 TEXT NOT NULL,
        document_kind  TEXT NOT NULL,
        lifecycle      TEXT NOT NULL CHECK(lifecycle IN ('active', 'removed', 'invalid', 'conflict')),
        owner          TEXT DEFAULT NULL,
        base_sha256    TEXT DEFAULT NULL,
        content_json   TEXT NOT NULL DEFAULT '{}',
        indexed_at     TEXT NOT NULL DEFAULT (datetime('now')),
        removed_at     TEXT DEFAULT NULL,
        PRIMARY KEY(workspace_id, relative_path)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workspace_facts (
        workspace_id  TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        fact_key      TEXT NOT NULL,
        value         TEXT NOT NULL,
        confirmed     INTEGER NOT NULL CHECK(confirmed IN (0, 1)),
        PRIMARY KEY(workspace_id, relative_path, fact_key)
    )
    """,
    # ── Human context (v8, local and explicit-consent only) ───────
    """
    CREATE TABLE IF NOT EXISTS human_context_entries (
        id          TEXT PRIMARY KEY,
        field       TEXT NOT NULL,
        value       TEXT NOT NULL,
        purpose     TEXT NOT NULL,
        source      TEXT NOT NULL CHECK(source = 'explicit_user_statement'),
        status      TEXT NOT NULL CHECK(status IN ('active', 'superseded', 'deleted')),
        consented_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        deleted_at  TEXT DEFAULT NULL,
        replaces_entry_id TEXT DEFAULT NULL,
        format_version INTEGER NOT NULL DEFAULT 1 CHECK(format_version = 1),
        FOREIGN KEY(replaces_entry_id) REFERENCES human_context_entries(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS human_context_accesses (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id    TEXT NOT NULL,
        consumer    TEXT NOT NULL CHECK(consumer IN ('coaching', 'cadence', 'board')),
        purpose     TEXT NOT NULL,
        accessed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(entry_id) REFERENCES human_context_entries(id)
    )
    """,
    # ── Weekly GTD cadence (v9, local and opt-in only) ─────────────
    """
    CREATE TABLE IF NOT EXISTS weekly_cadences (
        id              TEXT PRIMARY KEY,
        status          TEXT NOT NULL CHECK(status IN ('active', 'paused')),
        weekday         INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6),
        timezone        TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL CHECK(duration_minutes BETWEEN 10 AND 180),
        owner           TEXT NOT NULL,
        next_review_on  TEXT NOT NULL,
        created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS weekly_commitments (
        id              TEXT PRIMARY KEY,
        cadence_id      TEXT NOT NULL,
        priority        TEXT NOT NULL,
        project         TEXT NOT NULL,
        desired_outcome TEXT NOT NULL,
        next_action     TEXT NOT NULL,
        owner           TEXT NOT NULL,
        status          TEXT NOT NULL CHECK(status IN ('active', 'done', 'blocked', 'deferred', 'renegotiated')),
        created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(cadence_id) REFERENCES weekly_cadences(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS weekly_reviews (
        id              TEXT PRIMARY KEY,
        commitment_id   TEXT NOT NULL,
        outcome         TEXT NOT NULL CHECK(outcome IN ('done', 'blocked', 'deferred', 'renegotiated')),
        result          TEXT NOT NULL,
        blocker         TEXT DEFAULT NULL,
        reviewed_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(commitment_id) REFERENCES weekly_commitments(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cadence_automation_preferences (
        id              TEXT PRIMARY KEY,
        kind            TEXT NOT NULL,
        purpose         TEXT NOT NULL,
        frequency_months INTEGER NOT NULL CHECK(frequency_months BETWEEN 1 AND 12),
        data_minimum    TEXT NOT NULL,
        host_capability TEXT NOT NULL,
        manual_alternative TEXT NOT NULL,
        state           TEXT NOT NULL CHECK(state IN ('accepted', 'rejected', 'paused', 'removed')),
        host_state      TEXT NOT NULL CHECK(host_state IN ('not_configured', 'configured_by_user')),
        created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # ── Accountability Group longitudinal record (v10) ───────────
    """
    CREATE TABLE IF NOT EXISTS accountability_sessions (
        id             TEXT PRIMARY KEY,
        held_on        TEXT NOT NULL,
        source_type    TEXT NOT NULL CHECK(source_type IN ('manual', 'imported_document', 'drive_connector')),
        source_ref     TEXT NOT NULL,
        worksheet_json TEXT NOT NULL,
        decision_area  TEXT DEFAULT NULL CHECK(decision_area IS NULL OR decision_area IN ('people', 'strategy', 'execution', 'cash')),
        confidence     INTEGER DEFAULT NULL CHECK(confidence IS NULL OR confidence BETWEEN 0 AND 100),
        tags_json      TEXT NOT NULL DEFAULT '[]',
        status         TEXT NOT NULL CHECK(status IN ('draft', 'ready', 'reviewed')),
        included       INTEGER NOT NULL DEFAULT 1 CHECK(included IN (0, 1)),
        consented_at   TEXT NOT NULL,
        created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS accountability_commitments (
        id                     TEXT PRIMARY KEY,
        session_id             TEXT NOT NULL,
        statement              TEXT NOT NULL,
        owner                  TEXT NOT NULL,
        due_on                 TEXT NOT NULL,
        success_measure        TEXT NOT NULL,
        status                 TEXT NOT NULL CHECK(status IN ('planned', 'done', 'partial', 'not_done', 'renegotiated')),
        evidence               TEXT DEFAULT NULL,
        result                 TEXT DEFAULT NULL,
        blocker                TEXT DEFAULT NULL,
        learning               TEXT DEFAULT NULL,
        reviewed_on            TEXT DEFAULT NULL,
        rubric_json            TEXT DEFAULT NULL,
        follow_through_percent INTEGER DEFAULT NULL CHECK(follow_through_percent IS NULL OR follow_through_percent BETWEEN 0 AND 100),
        created_at             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES accountability_sessions(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS accountability_exclusions (
        id         TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        state      TEXT NOT NULL CHECK(state IN ('excluded', 'included')),
        reason     TEXT NOT NULL,
        changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES accountability_sessions(id)
    )
    """,
    # ── Methodology evidence (v11, local/confirmed fields only) ───────
    """
    CREATE TABLE IF NOT EXISTS evidence_sources (
        id             TEXT PRIMARY KEY,
        source_type    TEXT NOT NULL CHECK(source_type IN ('manual', 'file_preview', 'host_connector')),
        source_ref     TEXT NOT NULL,
        observed_at    TEXT NOT NULL,
        allowed_scope  TEXT NOT NULL CHECK(allowed_scope IN ('people', 'strategy', 'execution', 'cash')),
        content_sha256 TEXT DEFAULT NULL,
        created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence_proposals (
        id          TEXT PRIMARY KEY,
        source_id   TEXT NOT NULL,
        methodology TEXT NOT NULL,
        field       TEXT NOT NULL,
        value_json  TEXT DEFAULT NULL,
        sensitivity TEXT NOT NULL CHECK(sensitivity IN ('none', 'secret', 'personal_data')),
        state       TEXT NOT NULL CHECK(state IN ('accepted', 'rejected', 'superseded')),
        decided_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(source_id) REFERENCES evidence_sources(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS methodology_values (
        id          TEXT PRIMARY KEY,
        methodology TEXT NOT NULL,
        field       TEXT NOT NULL,
        value_json  TEXT NOT NULL,
        source_id   TEXT NOT NULL,
        observed_at TEXT NOT NULL,
        confidence  REAL NOT NULL DEFAULT 1.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
        version     INTEGER NOT NULL,
        status      TEXT NOT NULL CHECK(status IN ('active', 'superseded')),
        created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(source_id) REFERENCES evidence_sources(id),
        UNIQUE(methodology, field, version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS portable_evidence_imports (
        document_id     TEXT PRIMARY KEY,
        relative_path   TEXT NOT NULL,
        content_sha256  TEXT NOT NULL,
        imported_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
]

# The v4 read-only bridge accepts only the exact historical v4 contract. The
# first eleven tables and first fourteen indexes are the frozen v4 DDL; later
# consent-memory objects are deliberately excluded. Building the fingerprint
# from that DDL keeps column properties and indexes tied to their authority.
_V4_DDL_STATEMENTS = tuple(DDL_STATEMENTS[:11])

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
    "CREATE INDEX IF NOT EXISTS idx_migration_sources_path ON migration_sources(relative_path)",
    "CREATE INDEX IF NOT EXISTS idx_migration_applications_path ON migration_applications(relative_path, import_schema, id)",
    "CREATE INDEX IF NOT EXISTS idx_migration_fact_applications_fact ON migration_fact_applications(fact_key, migration_application_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_memory_sessions_status ON project_memory_sessions(status)",
    "CREATE INDEX IF NOT EXISTS idx_session_memory_proposals_session_state ON session_memory_proposals(session_id, response_state)",
    "CREATE INDEX IF NOT EXISTS idx_confirmed_memory_entries_session ON confirmed_memory_entries(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_confirmed_memory_entries_kind_status ON confirmed_memory_entries(kind, status)",
    "CREATE INDEX IF NOT EXISTS idx_workspace_documents_lifecycle ON workspace_documents(workspace_id, lifecycle)",
    "CREATE INDEX IF NOT EXISTS idx_workspace_facts_path ON workspace_facts(workspace_id, relative_path)",
    "CREATE INDEX IF NOT EXISTS idx_human_context_entries_field_status ON human_context_entries(field, status, consented_at)",
    "CREATE INDEX IF NOT EXISTS idx_human_context_accesses_entry ON human_context_accesses(entry_id, accessed_at)",
    "CREATE INDEX IF NOT EXISTS idx_weekly_cadences_status_due ON weekly_cadences(status, next_review_on)",
    "CREATE INDEX IF NOT EXISTS idx_weekly_commitments_cadence_status ON weekly_commitments(cadence_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_weekly_reviews_commitment ON weekly_reviews(commitment_id, reviewed_at)",
    "CREATE INDEX IF NOT EXISTS idx_cadence_automation_state ON cadence_automation_preferences(state, kind)",
    "CREATE INDEX IF NOT EXISTS idx_accountability_sessions_date ON accountability_sessions(included, held_on)",
    "CREATE INDEX IF NOT EXISTS idx_accountability_sessions_decision ON accountability_sessions(included, decision_area)",
    "CREATE INDEX IF NOT EXISTS idx_accountability_commitments_session_status ON accountability_commitments(session_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_accountability_commitments_due ON accountability_commitments(status, due_on)",
    "CREATE INDEX IF NOT EXISTS idx_accountability_exclusions_session ON accountability_exclusions(session_id, changed_at)",
    "CREATE INDEX IF NOT EXISTS idx_evidence_sources_scope_observed ON evidence_sources(allowed_scope, observed_at)",
    "CREATE INDEX IF NOT EXISTS idx_evidence_proposals_source_state ON evidence_proposals(source_id, state)",
    "CREATE INDEX IF NOT EXISTS idx_methodology_values_active ON methodology_values(methodology, field, status)",
    "CREATE INDEX IF NOT EXISTS idx_portable_evidence_imports_path ON portable_evidence_imports(relative_path)",
]

_V4_INDEX_STATEMENTS = tuple(INDEX_STATEMENTS[:14])


def _normalized_sql(sql: str) -> str:
    """Compare SQLite DDL structurally, ignoring formatting-only differences."""
    compact = re.sub(r"\s*([(),])\s*", r"\1", sql)
    return re.sub(r"\s+", " ", compact).strip().casefold()


def _check_constraints(sql: str) -> tuple[str, ...]:
    """Extract normalized CHECK expressions, including nested parentheses."""
    checks: list[str] = []
    start = 0
    while (match := re.search(r"check\(", sql[start:], re.IGNORECASE)) is not None:
        cursor = start + match.end()
        depth = 1
        expression_start = cursor
        while cursor < len(sql) and depth:
            depth += (sql[cursor] == "(") - (sql[cursor] == ")")
            cursor += 1
        if depth:
            return ()
        checks.append(_normalized_sql(sql[expression_start : cursor - 1]))
        start = cursor
    return tuple(checks)


def _contract_fingerprint(
    connection: sqlite3.Connection, table_names: frozenset[str]
) -> tuple:
    """Return the full SQLite-visible structural contract for managed tables."""
    tables = []
    for table in sorted(table_names):
        columns = tuple(
            (row[1], row[2].upper(), row[3], row[4], row[5])
            for row in connection.execute(f"PRAGMA table_info({table})")
        )
        indexes = []
        for index in connection.execute(f"PRAGMA index_list({table})"):
            name, unique, origin, partial = index[1], index[2], index[3], index[4]
            columns_in_index = tuple(
                (row[0], row[1], row[2], row[3], row[5])
                for row in connection.execute(f"PRAGMA index_xinfo({name})")
                if row[5]
            )
            indexes.append((name, unique, origin, partial, columns_in_index))
        sql_row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
        ).fetchone()
        table_sql = _normalized_sql(sql_row[0]) if sql_row and sql_row[0] else ""
        foreign_keys = tuple(
            (row[2], row[3], row[4], row[5].upper(), row[6].upper(), row[7].upper())
            for row in connection.execute(f"PRAGMA foreign_key_list({table})")
        )
        tables.append(
            (
                table,
                columns,
                tuple(sorted(indexes)),
                table_sql,
                foreign_keys,
                _check_constraints(table_sql),
            )
        )
    return tuple(tables)


@lru_cache(maxsize=1)
def _expected_schema_contract() -> tuple[frozenset[str], tuple]:
    """Build the health-check contract from the DDL that creates this schema."""
    with sqlite3.connect(":memory:") as connection:
        for statement in DDL_STATEMENTS:
            connection.execute(statement)
        for statement in INDEX_STATEMENTS:
            connection.execute(statement)
        tables = frozenset(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
        )
        return tables, _contract_fingerprint(connection, tables)


def schema_contract_is_valid(connection: sqlite3.Connection) -> bool:
    """Whether *connection* has exactly the DDL-derived managed-table contract.

    The fingerprint covers column type, NOT NULL, defaults, primary keys and all
    SQLite indexes (including the automatic index created for UNIQUE columns).
    Keeping it here means creation and validation share one authority: the DDL.
    """
    expected_tables, expected = _expected_schema_contract()
    return schema_contract_tables_are_present(connection) and (
        _contract_fingerprint(connection, expected_tables) == expected
    )


def schema_contract_tables_are_present(connection: sqlite3.Connection) -> bool:
    """Whether every table owned by the DDL is present in *connection*."""
    expected_tables, _ = _expected_schema_contract()
    present = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    return expected_tables.issubset(present)


def context_read_schema_is_valid(connection: sqlite3.Connection) -> bool:
    """Validate the frozen v4 contract without upgrading or repairing it."""
    try:
        version = connection.execute(
            "SELECT value FROM _meta WHERE key = 'schema_version'"
        ).fetchone()
        if version is None or int(version[0]) != 4:
            return False
        expected_tables, expected = _expected_v4_context_contract()
        actual_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
        }
        # E26 adds two local-only index tables. A database deliberately held
        # at v4 by the read-only bridge may retain those known tables after a
        # later runtime was opened; they are not consulted by context recovery.
        # Keep every v4-owned table/index exact and reject any other extra.
        allowed_local_index_tables = {
            "workspace_documents",
            "workspace_facts",
            "human_context_entries",
            "human_context_accesses",
            "weekly_cadences",
            "weekly_commitments",
            "weekly_reviews",
            "cadence_automation_preferences",
            "accountability_sessions",
            "accountability_commitments",
            "accountability_exclusions",
            "evidence_sources",
            "evidence_proposals",
            "methodology_values",
            "portable_evidence_imports",
        }
        if not expected_tables.issubset(actual_tables) or (
            actual_tables - expected_tables - allowed_local_index_tables
        ):
            return False
        if _contract_fingerprint(connection, expected_tables) != expected:
            return False
    except (sqlite3.Error, TypeError, ValueError):
        return False
    return True


@lru_cache(maxsize=1)
def _expected_v4_context_contract() -> tuple[frozenset[str], tuple]:
    """Build the immutable v4 read-only contract from its historical DDL."""
    with sqlite3.connect(":memory:") as connection:
        for statement in _V4_DDL_STATEMENTS:
            connection.execute(statement)
        for statement in _V4_INDEX_STATEMENTS:
            connection.execute(statement)
        tables = frozenset(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
        )
        return tables, _contract_fingerprint(connection, tables)


def _ensure_v6_format_columns(connection: sqlite3.Connection) -> None:
    """Add immutable format markers to pre-v6 consent tables once."""
    required = (
        (
            "session_memory_proposals",
            "provenance_format_version",
            (
                "ALTER TABLE session_memory_proposals ADD COLUMN provenance_format_version "
                "INTEGER NOT NULL DEFAULT 1 CHECK(provenance_format_version = 1)"
            ),
        ),
        (
            "confirmed_memory_entries",
            "entry_format_version",
            (
                "ALTER TABLE confirmed_memory_entries ADD COLUMN entry_format_version "
                "INTEGER NOT NULL DEFAULT 1 CHECK(entry_format_version = 1)"
            ),
        ),
        (
            "confirmed_memory_entries",
            "provenance_format_version",
            (
                "ALTER TABLE confirmed_memory_entries ADD COLUMN provenance_format_version "
                "INTEGER NOT NULL DEFAULT 1 CHECK(provenance_format_version = 1)"
            ),
        ),
    )
    for table, column, statement in required:
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            connection.execute(statement)


def _profile_fact_values(metadata: object) -> dict[str, str]:
    """Return the exact profile facts a S22.3 migration would have stored.

    The v3 -> v4 upgrade derives provenance from the persisted profile payload
    rather than trusting arbitrary ``memory_facts`` rows.
    """
    if not isinstance(metadata, str):
        return {}
    try:
        payload = json.loads(metadata)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}

    company = payload.get("company")
    groups = (
        ("profile", company if isinstance(company, dict) else {}),
        ("diagnosis", payload.get("scores", {})),
        ("profile.focus", payload.get("focus", {})),
    )
    facts: dict[str, str] = {}
    for prefix, values in groups:
        if not isinstance(values, dict):
            continue
        for key, value in values.items():
            if value not in (None, "", [], {}, 0):
                facts[f"{prefix}.{key}"] = json.dumps(value, sort_keys=True)
    return facts


def _backfill_fact_applications(connection: sqlite3.Connection) -> None:
    """Link only current, source-derived profile facts during the v4 upgrade."""
    application = connection.execute(
        """SELECT applications.id, applications.applied_at
        FROM migration_applications AS applications
        JOIN migration_sources AS sources
          ON sources.relative_path = applications.relative_path
         AND sources.content_sha256 = applications.content_sha256
         AND sources.import_schema = applications.import_schema
         AND sources.source_kind = applications.source_kind
        WHERE applications.relative_path = ?
          AND applications.source_kind = ?
          AND applications.import_schema = ?
        ORDER BY applications.id DESC LIMIT 1""",
        (".scaleup/agent/memory/company-profile.yaml", "company-profile", 1),
    ).fetchone()
    if application is None:
        return

    expected: dict[str, str] = {}
    for (metadata,) in connection.execute("SELECT metadata FROM companies"):
        expected.update(_profile_fact_values(metadata))
    if not expected:
        return

    application_id, applied_at = application
    for fact_key, fact_value in expected.items():
        row = connection.execute(
            "SELECT value FROM memory_facts WHERE key = ?", (fact_key,)
        ).fetchone()
        if row is None or row[0] != fact_value:
            continue
        connection.execute(
            """INSERT OR IGNORE INTO migration_fact_applications (
                fact_key, value_sha256, migration_application_id, applied_at
            ) VALUES (?, ?, ?, ?)""",
            (
                fact_key,
                hashlib.sha256(fact_value.encode()).hexdigest(),
                application_id,
                applied_at,
            ),
        )


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
    try:
        conn.execute("BEGIN")

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
                if current < 3:
                    conn.execute(
                        """INSERT INTO migration_applications (
                            relative_path, content_sha256, import_schema, source_kind
                        )
                        SELECT relative_path, content_sha256, import_schema, source_kind
                        FROM migration_sources
                        WHERE NOT EXISTS (SELECT 1 FROM migration_applications)
                        ORDER BY id ASC"""
                    )
                if current < 4:
                    _backfill_fact_applications(conn)
                if current < 6:
                    _ensure_v6_format_columns(conn)
                conn.execute(
                    "UPDATE _meta SET value = ? WHERE key = 'schema_version'",
                    (str(SCHEMA_VERSION),),
                )

        # ── Create indexes ───────────────────────────────────────────────
        for stmt in INDEX_STATEMENTS:
            conn.execute(stmt)

        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        conn.close()
        raise
    return conn
