"""Evaluate synthetic or externally captured activation observations locally."""

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
    evaluate_activation_suite,
    load_activation_suite,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate ESCALA activation routing.")
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        raw = json.loads(arguments.observations.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ActivationEvalError("observations_invalid")
        result = evaluate_activation_suite(
            load_activation_suite(arguments.suite),
            tuple(ActivationObservation.model_validate(item) for item in raw),
        )
    except (OSError, ValueError, ActivationEvalError) as exc:
        print(f"activation evaluation failed: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "precision": result.precision,
                "recall": result.recall,
                "true_positives": result.true_positives,
                "false_positives": result.false_positives,
                "false_negatives": result.false_negatives,
                "true_negatives": result.true_negatives,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
