"""dict_diff — recursive dictionary diff engine for Escala.

Returns a list of {field, old_value, new_value} change entries.
Handles nested dicts recursively with dotted path notation.
Detects added and removed keys.
"""

from typing import Any


def dict_diff(old_dict: dict[str, Any], new_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute the diff between two dictionaries.

    Returns a list of change entries, each with:
        field: str       — dotted path to the changed field (e.g., "a.b.c")
        old_value: Any   — previous value (None for added keys)
        new_value: Any   — new value (None for removed keys)
    """
    changes: list[dict[str, Any]] = []
    _dict_diff_recursive(old_dict, new_dict, "", changes)
    return changes


def _dict_diff_recursive(
    old: dict[str, Any],
    new: dict[str, Any],
    prefix: str,
    changes: list[dict[str, Any]],
) -> None:
    """Recursively compute diffs, appending to `changes`."""

    # Collect all keys from both dicts
    all_keys = set(old.keys()) | set(new.keys())

    for key in all_keys:
        field = f"{prefix}.{key}" if prefix else key
        in_old = key in old
        in_new = key in new

        if not in_old:
            # Key was added
            changes.append({
                "field": field,
                "old_value": None,
                "new_value": new[key],
            })
        elif not in_new:
            # Key was removed
            changes.append({
                "field": field,
                "old_value": old[key],
                "new_value": None,
            })
        elif isinstance(old[key], dict) and isinstance(new[key], dict):
            # Both are dicts — recurse
            _dict_diff_recursive(old[key], new[key], field, changes)
        elif old[key] != new[key]:
            # Values differ
            changes.append({
                "field": field,
                "old_value": old[key],
                "new_value": new[key],
            })
