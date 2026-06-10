"""Tests para la acción `save` del módulo worksheet.

Cubre el endurecimiento anti-sobrescritura silenciosa (issue #4): un re-save
sobre un worksheet YA finalizado debe respaldar la versión previa, mientras que
el flujo normal step→save no genera respaldos. También verifica el aislamiento
por base_path entre negocios.
"""
from pathlib import Path

from coaching.worksheet import run
from coaching.core import read_yaml, write_yaml, ensure_dir


def _seed_registry(base: Path) -> None:
    """Crea un registry mínimo con un solo worksheet."""
    registry_path = base / ".scaleup" / "knowledge" / "registry" / "worksheets.yaml"
    ensure_dir(registry_path.parent)
    write_yaml(
        registry_path,
        {"worksheets": [{"id": "worksheet-face", "name": "FACE Worksheet", "decision": "people"}]},
    )


def _state_path(base: Path) -> Path:
    return base / ".scaleup" / "my-company" / "worksheets" / "worksheet-face.yaml"


def _backups(base: Path) -> list[Path]:
    wdir = base / ".scaleup" / "my-company" / "worksheets"
    return sorted(wdir.glob("worksheet-face.*.bak.yaml"))


def test_first_save_creates_no_backup(tmp_path):
    """Un save fresco (sin archivo previo) no debe generar respaldo."""
    _seed_registry(tmp_path)
    result = run({"action": "save", "worksheet_name": "worksheet-face", "base_path": str(tmp_path)})

    assert result["errors"] == []
    assert _state_path(tmp_path).exists()
    assert _backups(tmp_path) == []
    assert "backup_path" not in result["artifacts"]


def test_resave_over_completed_backs_up(tmp_path):
    """Re-save sobre un worksheet ya 'completed' respalda la versión previa."""
    _seed_registry(tmp_path)
    state_path = _state_path(tmp_path)
    ensure_dir(state_path.parent)
    write_yaml(state_path, {"status": "completed", "fields": {"answer": "DATA_VIEJA"}})

    result = run({"action": "save", "worksheet_name": "worksheet-face", "base_path": str(tmp_path)})

    backups = _backups(tmp_path)
    assert len(backups) == 1, "debió crearse exactamente un respaldo timestamped"
    assert read_yaml(backups[0])["fields"]["answer"] == "DATA_VIEJA"
    assert result["artifacts"].get("backup_path") == str(backups[0])
    assert "♻️" in result["output"]
    # El archivo vivo quedó finalizado de nuevo.
    assert read_yaml(state_path)["status"] == "completed"


def test_save_isolates_by_base_path(tmp_path):
    """Dos negocios con distinto base_path no se pisan entre sí."""
    neg_a = tmp_path / "negA"
    neg_b = tmp_path / "negB"
    for base, payload in ((neg_a, "A"), (neg_b, "B")):
        _seed_registry(base)
        sp = _state_path(base)
        ensure_dir(sp.parent)
        write_yaml(sp, {"status": "in_progress", "fields": {"answer": payload}})
        run({"action": "save", "worksheet_name": "worksheet-face", "base_path": str(base)})

    assert read_yaml(_state_path(neg_a))["fields"]["answer"] == "A"
    assert read_yaml(_state_path(neg_b))["fields"]["answer"] == "B"
