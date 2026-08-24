"""Quality gate for the canonical work/strategy/opsp.md artifact."""
from __future__ import annotations

import sys
from pathlib import Path

def _runtime_root() -> Path:
    """Find the source or installed ScaleUp runtime owning ``coaching``."""
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "coaching" / "opsp.py").is_file():
            return ancestor
    raise ModuleNotFoundError(
        "ScaleUp coaching runtime was not found next to this OPSP validator. "
        "Reinstall ScaleUp and try again."
    )


runtime_root = _runtime_root()
if str(runtime_root) not in sys.path:
    sys.path.insert(0, str(runtime_root))

from coaching.opsp import validate_opsp


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("work/strategy/opsp.md")
    errors = validate_opsp(path)
    if errors:
        print("VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("VALIDATION PASSED — OPSP artifact is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
