# pyright: strict
"""Enable ``python -m coaching.tracker`` (JSON in on stdin, JSON out)."""

from __future__ import annotations

import json
import sys
from typing import cast

from coaching.tracker.flow import run


def main() -> None:
    try:
        raw: object = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        raw = {}
    context = cast(dict[str, object], raw) if isinstance(raw, dict) else {}
    print(run(context).model_dump_json())


main()
