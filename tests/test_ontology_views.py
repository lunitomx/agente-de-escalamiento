from __future__ import annotations
import sqlite3
from pathlib import Path
import yaml
from validators.ontology_v2 import OntologyDocument
from validators.ontology_views import build_sqlite_view, document_hash, render_yaml_view


def _document():
    return OntologyDocument.model_validate(
        {
            "schema_version": 2,
            "nodes": [
                {
                    "id": "tool.example",
                    "kind": "tool",
                    "canonical_name": "Example",
                    "origin": "company-local",
                    "review_state": "approved",
                }
            ],
            "relations": [],
            "aliases": [{"alias": "example", "canonical_id": "tool.example"}],
        }
    )


def test_views_are_derived_and_self_identifying(tmp_path: Path) -> None:
    d = _document()
    view = yaml.safe_load(render_yaml_view(d))
    assert view["generated_from_sha256"] == document_hash(d)
    assert view["generator"] == "ontology-v2"
    db = tmp_path / "ontology.sqlite"
    build_sqlite_view(d, db)
    con = sqlite3.connect(db)
    assert dict(con.execute("SELECT key,value FROM metadata"))[
        "generated_from_sha256"
    ] == document_hash(d)
    assert con.execute("SELECT count(*) FROM nodes").fetchone()[0] == 1
    con.close()


def test_sqlite_view_refuses_overwrite(tmp_path: Path) -> None:
    db = tmp_path / "ontology.sqlite"
    build_sqlite_view(_document(), db)
    try:
        build_sqlite_view(_document(), db)
    except ValueError as e:
        assert "already exists" in str(e)
    else:
        raise AssertionError("expected overwrite refusal")
