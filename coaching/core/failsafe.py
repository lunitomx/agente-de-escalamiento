# pyright: strict
"""One fixed answer when a module breaks (S86.3, A1).

Every ``python -m coaching.<module>`` runs through :func:`run_safely`. If
anything raises, the owner-facing JSON says one fixed sentence with a way out;
the traceback goes to stderr for the bug report and the exit code is 1, the
same as an uncaught error. Normal output is untouched.
"""

from __future__ import annotations

import json
import sys
import traceback
from collections.abc import Callable

SOMETHING_FAILED = (
    "No pude abrir esa parte de ESCALA en tu computadora. No se perdió nada. "
    "Escribe 'reportar problema' y preparo un aviso para el equipo."
)
INTERNAL_ERROR = "internal_error"


def failure_result() -> dict[str, object]:
    """The JSON printed instead of a traceback (``output`` for dict modules)."""
    return {
        "message": SOMETHING_FAILED,
        "output": SOMETHING_FAILED,
        "artifacts": {},
        "errors": [INTERNAL_ERROR],
    }


def run_safely(entry: Callable[[], object]) -> None:
    """Run a module entry point; on any error print the fixed answer and exit 1."""
    try:
        entry()
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps(failure_result(), ensure_ascii=False))
        sys.exit(1)
