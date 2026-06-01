"""
Quality gate: validate welcome/onboarding profile completeness.
"""
from pathlib import Path
import yaml

REQUIRED_COMPANY_FIELDS = ["name", "industry", "employees", "growth_stage"]
REQUIRED_PROFILE_KEYS = ["company", "scores", "focus"]


def validate_company_profile(profile_path: Path) -> list[str]:
    """
    Validate that a company profile has all required fields filled.
    Returns list of error messages (empty = valid).
    """
    errors = []

    if not profile_path.exists():
        return [f"Profile not found: {profile_path}"]

    try:
        data = yaml.safe_load(profile_path.read_text())
    except Exception as e:
        return [f"Invalid YAML in profile: {e}"]

    if not isinstance(data, dict):
        return ["Profile is not a valid YAML dictionary"]

    for key in REQUIRED_PROFILE_KEYS:
        if key not in data:
            errors.append(f"Missing required key: {key}")

    company = data.get("company", {})
    for field in REQUIRED_COMPANY_FIELDS:
        value = company.get(field)
        if not value:
            errors.append(f"company.{field} is empty or missing")

    return errors


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".scaleup/agent/memory/company-profile.yaml")
    errors = validate_company_profile(path)
    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
