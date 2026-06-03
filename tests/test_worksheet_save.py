"""Regresión: el save de worksheets debe aislar por base_path y nunca
sobrescribir en silencio (issue #4)."""
import pathlib
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from coaching.worksheet import run  # noqa: E402

REGISTRY = str(REPO_ROOT / "conocimiento" / "registry" / "worksheets.yaml")


def _save(base, wid, payload, **extra):
    ctx = {
        "action": "save",
        "base_path": str(base),
        "registry_path": REGISTRY,
        "data": {"worksheet_id": wid, **payload},
    }
    ctx.update(extra)
    return run(ctx)


def test_save_isola_por_base_path(tmp_path):
    a, b = tmp_path / "negocioA", tmp_path / "negocioB"
    _save(a, "core-customer", {"valor": "AAA"})
    _save(b, "core-customer", {"valor": "BBB"})

    fa = a / ".scaleup" / "my-company" / "worksheets" / "core-customer.yaml"
    fb = b / ".scaleup" / "my-company" / "worksheets" / "core-customer.yaml"
    assert fa.exists() and fb.exists()
    assert yaml.safe_load(fa.read_text())["valor"] == "AAA"
    assert yaml.safe_load(fb.read_text())["valor"] == "BBB"  # B no planchó a A


def test_save_respalda_antes_de_sobrescribir(tmp_path):
    _save(tmp_path, "face", {"valor": "viejo"})
    res = _save(tmp_path, "face", {"valor": "nuevo"})

    wdir = tmp_path / ".scaleup" / "my-company" / "worksheets"
    actual = wdir / "face.yaml"
    assert yaml.safe_load(actual.read_text())["valor"] == "nuevo"

    backups = list(wdir.glob("face.*.bak.yaml"))
    assert backups, "debe respaldar la version previa antes de sobrescribir"
    assert yaml.safe_load(backups[0].read_text())["valor"] == "viejo"
    assert res["artifacts"].get("backup_path")


def test_resave_identico_no_genera_respaldo(tmp_path):
    _save(tmp_path, "face", {"valor": "igual"})
    _save(tmp_path, "face", {"valor": "igual"})
    wdir = tmp_path / ".scaleup" / "my-company" / "worksheets"
    assert not list(wdir.glob("face.*.bak.yaml"))
