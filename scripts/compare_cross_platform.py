"""Compare normalized E68 activation observations from Codex and Claude."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validators.activation_evals import (  # noqa: E402
    ActivationEvalError,
    ActivationObservation,
    load_activation_suite,
)
from validators.cross_platform_evals import evaluate_cross_platform  # noqa: E402


def _load_observations(path: Path) -> tuple[ActivationObservation, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ActivationEvalError("observations_invalid")
    return tuple(ActivationObservation.model_validate(item) for item in raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare E68 platform routing.")
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--claude", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        result = evaluate_cross_platform(
            load_activation_suite(arguments.suite),
            _load_observations(arguments.codex),
            _load_observations(arguments.claude),
        )
    except (OSError, ValueError, ActivationEvalError) as exc:
        print(f"cross-platform evaluation failed: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "codex_precision": result.codex_precision,
                "codex_recall": result.codex_recall,
                "claude_precision": result.claude_precision,
                "claude_recall": result.claude_recall,
                "semantic_differences": result.semantic_differences,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
