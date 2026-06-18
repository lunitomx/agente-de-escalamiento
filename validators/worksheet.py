"""
Quality gate: validate worksheet completion.
"""

from pathlib import Path
import yaml


def validate_worksheet(path: Path) -> list[str]:
    """Validate a completed worksheet file."""
    errors = []

    if not path.exists():
        return [f"Worksheet not found: {path}"]

    try:
        data = yaml.safe_load(path.read_text())
    except Exception as e:
        return [f"Invalid YAML: {e}"]

    if not isinstance(data, dict):
        return ["Worksheet is not a valid YAML dictionary"]

    required = ["worksheet_id", "worksheet_name", "decision", "status"]
    for key in required:
        if key not in data:
            errors.append(f"Missing required key: {key}")

    if data.get("status") == "completed" and "completed" not in data:
        errors.append("Status is 'completed' but no completion date found")

    if data.get("status") == "completed" and not data.get("fields"):
        errors.append("Status is 'completed' but no fields data found")

    if data.get("status") not in ("in_progress", "completed"):
        errors.append(f"Invalid status: {data.get('status')}")

    return errors


def validate_registry_consistency(
    registry_path: Path, worksheets_dir: Path
) -> list[str]:
    """Check that all completed worksheets correspond to registry entries."""
    errors = []

    if not registry_path.exists():
        return [f"Registry not found: {registry_path}"]

    try:
        registry = yaml.safe_load(registry_path.read_text())
    except Exception as e:
        return [f"Invalid registry YAML: {e}"]

    registered_ids = {w["id"] for w in registry.get("worksheets", [])}

    if worksheets_dir.exists():
        for f in worksheets_dir.glob("*.yaml"):
            data = yaml.safe_load(f.read_text())
            wid = data.get("worksheet_id") if data else f.stem
            if wid not in registered_ids:
                errors.append(f"Worksheet '{wid}' not found in registry")

    return errors


if __name__ == "__main__":
    import sys

    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".scaleup/my-company/worksheets")
    )
    if path.is_dir():
        all_ok = True
        for f in sorted(path.glob("*.yaml")):
            errors = validate_worksheet(f)
            if errors:
                print(f"FAILED: {f.name}")
                for err in errors:
                    print(f"  - {err}")
                all_ok = False
        if all_ok:
            print("VALIDATION PASSED — all worksheets valid")
    else:
        errors = validate_worksheet(path)
        if errors:
            print("VALIDATION FAILED:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("VALIDATION PASSED")
