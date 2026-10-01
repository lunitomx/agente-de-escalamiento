# pyright: strict
"""Enable ``python -m coaching.journey`` (JSON in on stdin, JSON out)."""

from __future__ import annotations

import json
import sys
from typing import cast

from coaching.core.failsafe import run_safely


def main() -> None:
    # Imported here so a broken import also gets the fixed answer (S86.3).
    from coaching.journey.flow import run

    try:
        raw: object = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        raw = {}
    context = cast(dict[str, object], raw) if isinstance(raw, dict) else {}
    print(run(context).model_dump_json())


run_safely(main)
