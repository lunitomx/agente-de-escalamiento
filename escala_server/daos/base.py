"""Base DAO class providing a shared SQLite connection.

All DAO subclasses inherit get_connection() which returns a
connection to the configured database path.  Callers are responsible
for committing (or rolling back) at the appropriate granularity.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..schema import init_db

# Shared in-memory connections keyed by db_path so that multiple DAOs
# targeting the same :memory: path share a single database.
_shared_conns: dict[str, sqlite3.Connection] = {}


class BaseDAO:
    """Base class for Escala DAOs — owns the db_path and
    provides get_connection() + a context manager for sessions.

    On construction, the schema is created/upgraded via ``init_db``
    and the returned connection is kept alive in a module-level
    cache.  All subsequent ``get_connection()`` calls return the
    cached connection so that ``:memory:`` databases work correctly.

    The ``connection()`` context manager wraps operations in an
    explicit transaction (BEGIN/COMMIT) so that rollback works on
    exceptions.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        # Resolve file paths to absolute (skip URI-style and :memory:)
        if db_path != ":memory:" and not db_path.startswith("file:"):
            self._db_path = str(Path(db_path).resolve())
        # Create tables (or reuse cached connection)
        if self._db_path not in _shared_conns:
            _shared_conns[self._db_path] = init_db(self._db_path)

    # raw connection (for advanced use)

    def get_connection(self) -> sqlite3.Connection:
        return _shared_conns[self._db_path]

    # context manager (explicit transaction with rollback)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = _shared_conns[self._db_path]
        conn.execute("BEGIN")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
