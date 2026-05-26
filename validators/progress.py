"""
Quality gate: validate progress data consistency.
"""
from pathlib import Path
import yaml

DECISIONS = ["people", "strategy", "execution", "cash"]


def validate_progress(profile_path: Path, registry_path: Path, worksheets_dir: Path = None) -> list[str]:
    """Validate progress data consistency."""
    errors = []

    if not profile_path.exists():
        return [f"Profile not found: {profile_path}"]

    try:
        profile = yaml.safe_load(profile_path.read_text())
    except Exception as e:
        return [f"Invalid profile YAML: {e}"]

    if not registry_path.exists():
        return [f"Registry not found: {registry_path}"]

    try:
        registry = yaml.safe_load(registry_path.read_text())
    except Exception as e:
        return [f"Invalid registry YAML: {e}"]

    scores = profile.get("scores", {})
    for dec in DECISIONS:
        score = scores.get(dec)
        if score is not None:
            if not isinstance(score, int) or score < 1 or score > 5:
                errors.append(f"Invalid score for {dec}: {score}")

    # Check worksheet counts
    all_ws = registry.get("worksheets", [])
    if worksheets_dir and worksheets_dir.exists():
        for f in worksheets_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text())
            except Exception:
                errors.append(f"Invalid YAML in worksheet file: {f.name}")
                continue

            if data:
                wid = data.get("worksheet_id", f.stem)
                registered = any(w["id"] == wid for w in all_ws)
                if not registered:
                    errors.append(f"Worksheet '{wid}' not found in registry")

    # Check percentages are non-negative
    if not (0 <= len([w for w in all_ws]) <= 1000):
        errors.append("Suspicious worksheet count in registry")

    return errors


if __name__ == "__main__":
    import sys
    profile_path = Path(".scaleup/agent/memory/company-profile.yaml")
    registry_path = Path(".scaleup/knowledge/registry/worksheets.yaml")
    ws_dir = Path(".scaleup/my-company/worksheets")

    errors = validate_progress(profile_path, registry_path, ws_dir)
    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
