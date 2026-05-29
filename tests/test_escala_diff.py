"""Tests for escala_server.diff — dict_diff function."""

import pytest
from escala_server.diff import dict_diff


class TestDictDiff:
    """Test the dict_diff function with various scenarios."""

    def test_no_changes(self):
        """Identical dicts produce empty change list."""
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 2}
        changes = dict_diff(old, new)
        assert changes == []

    def test_simple_value_change(self):
        """Single field value change."""
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 3}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "b", "old_value": 2, "new_value": 3}

    def test_multiple_value_changes(self):
        """Multiple fields changed."""
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 10, "b": 2, "c": 30}
        changes = dict_diff(old, new)
        assert len(changes) == 2
        fields = {c["field"] for c in changes}
        assert fields == {"a", "c"}

    def test_added_key(self):
        """Key present in new but not in old."""
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "b", "old_value": None, "new_value": 2}

    def test_removed_key(self):
        """Key present in old but not in new."""
        old = {"a": 1, "b": 2}
        new = {"a": 1}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "b", "old_value": 2, "new_value": None}

    def test_added_and_removed_and_changed(self):
        """Mix of added, removed, and changed keys."""
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 1, "c": 30, "d": 4}
        changes = dict_diff(old, new)
        assert len(changes) == 3
        fields_found = set()
        for c in changes:
            fields_found.add(c["field"])
            if c["field"] == "b":
                assert c["old_value"] == 2
                assert c["new_value"] is None
            elif c["field"] == "c":
                assert c["old_value"] == 3
                assert c["new_value"] == 30
            elif c["field"] == "d":
                assert c["old_value"] is None
                assert c["new_value"] == 4
        assert fields_found == {"b", "c", "d"}

    def test_nested_dict_no_change(self):
        """Nested dicts with identical structure produce no changes."""
        old = {"a": {"x": 1, "y": 2}, "b": 3}
        new = {"a": {"x": 1, "y": 2}, "b": 3}
        changes = dict_diff(old, new)
        assert changes == []

    def test_nested_dict_value_change(self):
        """Change in nested dict value is reported with dotted path."""
        old = {"a": {"x": 1, "y": 2}}
        new = {"a": {"x": 1, "y": 20}}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "a.y", "old_value": 2, "new_value": 20}

    def test_nested_dict_added_key(self):
        """Added key inside nested dict."""
        old = {"a": {"x": 1}}
        new = {"a": {"x": 1, "y": 2}}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "a.y", "old_value": None, "new_value": 2}

    def test_nested_dict_removed_key(self):
        """Removed key inside nested dict."""
        old = {"a": {"x": 1, "y": 2}}
        new = {"a": {"x": 1}}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "a.y", "old_value": 2, "new_value": None}

    def test_deeply_nested_dict(self):
        """Dotted paths work for deeply nested structures."""
        old = {"a": {"b": {"c": {"d": 1}}}}
        new = {"a": {"b": {"c": {"d": 2}}}}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "a.b.c.d", "old_value": 1, "new_value": 2}

    def test_nested_dict_type_change(self):
        """When a value changes from dict to non-dict, it's a single change."""
        old = {"a": {"x": 1}}
        new = {"a": "string"}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "a", "old_value": {"x": 1}, "new_value": "string"}

    def test_non_dict_to_dict(self):
        """When a value changes from non-dict to dict."""
        old = {"a": "string"}
        new = {"a": {"x": 1}}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "a", "old_value": "string", "new_value": {"x": 1}}

    def test_empty_dicts(self):
        """Both empty dicts produce no changes."""
        changes = dict_diff({}, {})
        assert changes == []

    def test_empty_old_with_new(self):
        """All keys in new dict are reported as added."""
        old = {}
        new = {"a": 1, "b": 2}
        changes = dict_diff(old, new)
        assert len(changes) == 2
        for c in changes:
            assert c["old_value"] is None

    def test_old_with_empty_new(self):
        """All keys in old dict are reported as removed."""
        old = {"a": 1, "b": 2}
        new = {}
        changes = dict_diff(old, new)
        assert len(changes) == 2
        for c in changes:
            assert c["new_value"] is None

    def test_none_values(self):
        """None values are handled correctly."""
        old = {"a": None}
        new = {"a": "hello"}
        changes = dict_diff(old, new)
        assert len(changes) == 1
        assert changes[0] == {"field": "a", "old_value": None, "new_value": "hello"}
