from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path
import yaml
from validators.ontology_v2 import OntologyDocument


def document_hash(document: OntologyDocument) -> str:
    return hashlib.sha256(
        json.dumps(
            document.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode()
    ).hexdigest()


def render_yaml_view(document: OntologyDocument) -> str:
    data = {
        "schema_version": 2,
        "generated_from_sha256": document_hash(document),
        "generator": "ontology-v2",
        "nodes": [n.model_dump(mode="json") for n in document.nodes],
        "relations": [r.model_dump(mode="json") for r in document.relations],
        "aliases": [a.model_dump(mode="json") for a in document.aliases],
    }
    return yaml.safe_dump(data, allow_unicode=False, sort_keys=True)


def build_sqlite_view(document: OntologyDocument, path: Path) -> None:
    if path.exists():
        raise ValueError("derived SQLite output already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    try:
        con.executescript(
            "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL); CREATE TABLE nodes (id TEXT PRIMARY KEY, kind TEXT NOT NULL, canonical_name TEXT NOT NULL, origin TEXT NOT NULL, review_state TEXT NOT NULL); CREATE TABLE relations (source_id TEXT NOT NULL, target_id TEXT NOT NULL, relation_type TEXT NOT NULL); CREATE TABLE aliases (alias TEXT PRIMARY KEY, canonical_id TEXT NOT NULL);"
        )
        con.executemany(
            "INSERT INTO metadata VALUES (?,?)",
            [
                ("schema_version", "2"),
                ("generated_from_sha256", document_hash(document)),
                ("generator", "ontology-v2"),
            ],
        )
        con.executemany(
            "INSERT INTO nodes VALUES (?,?,?,?,?)",
            [
                (
                    n.id,
                    n.kind.value,
                    n.canonical_name,
                    n.origin.value,
                    n.review_state.value,
                )
                for n in document.nodes
            ],
        )
        con.executemany(
            "INSERT INTO relations VALUES (?,?,?)",
            [(r.source_id, r.target_id, r.relation_type) for r in document.relations],
        )
        con.executemany(
            "INSERT INTO aliases VALUES (?,?)",
            [(a.alias, a.canonical_id) for a in document.aliases],
        )
        con.commit()
    finally:
        con.close()
