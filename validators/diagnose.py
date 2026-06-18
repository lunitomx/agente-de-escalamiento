"""
Quality gate: validate diagnosis scores.
"""

from pathlib import Path
from typing import Optional
import yaml

VALID_DECISIONS = ["people", "strategy", "execution", "cash"]


def validate_diagnosis_scores(
    profile_path: Path, required_decisions: Optional[list[str]] = None
) -> list[str]:
    """
    Validate diagnosis scores in company profile.
    Returns list of errors (empty = valid).
    """
    if required_decisions is None:
        required_decisions = VALID_DECISIONS

    errors = []

    if not profile_path.exists():
        return [f"Profile not found: {profile_path}"]

    try:
        data = yaml.safe_load(profile_path.read_text())
    except Exception as e:
        return [f"Invalid YAML: {e}"]

    scores = data.get("scores", {}) if isinstance(data, dict) else {}
    if not scores:
        return ["No scores found in profile. Run /scaleup-diagnose first."]

    for dec in required_decisions:
        score = scores.get(dec)
        if score is None:
            errors.append(f"Missing score for: {dec}")
        elif not isinstance(score, int):
            errors.append(f"{dec} score is not an integer: {score}")
        elif score < 1 or score > 5:
            errors.append(f"{dec} score out of range (1-5): {score}")

    focus = data.get("focus", {})
    if not focus.get("last_diagnosis"):
        errors.append("Missing diagnosis date (focus.last_diagnosis)")

    return errors


if __name__ == "__main__":
    import sys

    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".scaleup/agent/memory/company-profile.yaml")
    )
    errors = validate_diagnosis_scores(path)
    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
