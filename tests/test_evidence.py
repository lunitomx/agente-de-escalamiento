from __future__ import annotations

import sqlite3
import zipfile
from pathlib import Path

from escala_server.evidence import EvidenceStore
from escala_server.project_memory import ProjectMemoryRuntime


def test_csv_preview_never_creates_memory_until_a_field_is_confirmed(
    tmp_path: Path,
) -> None:
    project = tmp_path / "company"
    project.mkdir()
    source = tmp_path / "cash.csv"
    source.write_text(
        "precio,volumen,cogs,gastos operativos,dias cobranza,dias inventario,dias pago\n"
        "100,50,40,1200,30,20,15\n",
        encoding="utf-8",
    )
    store = EvidenceStore(project)

    preview = store.preview_file(source, "cash")

    assert preview.ready
    assert preview.proposed == {
        "price": 100.0,
        "volume": 50.0,
        "cogs": 40.0,
        "overheads": 1200.0,
        "ar_days": 30.0,
        "inv_days": 20.0,
        "ap_days": 15.0,
    }
    assert not (project / ".scaleup" / "memory" / "escala.db").exists()

    result = store.confirm_value(
        decision="cash",
        field="price",
        value=preview.proposed["price"],
        source_type="file_preview",
        source_ref=preview.source_ref or "cash.csv",
        content_sha256=preview.content_sha256,
    )

    assert result.ready and result.source_id
    snapshot = store.snapshot("cash")
    assert snapshot["fields"]["price"]["state"] == "confirmed"
    assert snapshot["fields"]["price"]["source"]["label"] == "cash.csv"
    assert snapshot["fields"]["volume"]["state"] == "pending"
    with sqlite3.connect(ProjectMemoryRuntime(project).db_path) as db:
        assert db.execute("SELECT COUNT(*) FROM methodology_values").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM evidence_sources").fetchone()[0] == 1


def test_secret_or_personal_content_is_stopped_before_preview_or_storage(
    tmp_path: Path,
) -> None:
    project = tmp_path / "company"
    project.mkdir()
    source = tmp_path / "unsafe.csv"
    source.write_text("api_key,precio\nsk-live-not-safe,100\n", encoding="utf-8")
    store = EvidenceStore(project)

    preview = store.preview_file(source, "cash")

    assert not preview.ready
    assert preview.sensitivity == "secret"
    assert not (project / ".scaleup" / "memory" / "escala.db").exists()
    blocked = store.confirm_value(
        decision="people",
        field="role_coverage",
        value="ana@example.com",
        source_type="manual",
        source_ref="captura manual",
    )
    assert not blocked.ready
    assert "delicado" in (blocked.reason or "")


def test_host_content_uses_same_preview_and_supersedes_without_erasing_history(
    tmp_path: Path,
) -> None:
    project = tmp_path / "company"
    project.mkdir()
    store = EvidenceStore(project)
    preview = store.preview_host_content(
        "precio,volumen\n100,50\n", "cash", source_ref="Drive autorizado"
    )

    assert preview.ready and preview.proposed == {"price": 100.0, "volume": 50.0}
    first = store.confirm_value(
        decision="cash",
        field="price",
        value=100,
        source_type="host_connector",
        source_ref="Drive autorizado",
        content_sha256=preview.content_sha256,
    )
    second = store.confirm_value(
        decision="cash",
        field="price",
        value=120,
        source_type="manual",
        source_ref="captura manual",
    )

    assert first.ready and second.ready
    snapshot = store.snapshot("cash")
    assert snapshot["fields"]["price"]["value"] == 120.0
    with sqlite3.connect(ProjectMemoryRuntime(project).db_path) as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM methodology_values WHERE field='price' AND status='superseded'"
            ).fetchone()[0]
            == 1
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM methodology_values WHERE field='price' AND status='active'"
            ).fetchone()[0]
            == 1
        )


def test_rejection_records_no_raw_value(tmp_path: Path) -> None:
    project = tmp_path / "company"
    project.mkdir()
    store = EvidenceStore(project)

    assert store.reject_value(
        decision="cash",
        field="price",
        source_type="manual",
        source_ref="captura manual",
    )
    with sqlite3.connect(ProjectMemoryRuntime(project).db_path) as db:
        proposal = db.execute(
            "SELECT value_json, state FROM evidence_proposals"
        ).fetchone()
    assert proposal == (None, "rejected")


def test_cash_panel_api_exposes_confirmed_source_and_pending_fields(
    tmp_path: Path,
) -> None:
    from escala_server.handlers import WorksheetsHandler

    project = tmp_path / "company"
    project.mkdir()
    store = EvidenceStore(project)
    assert store.confirm_value(
        decision="cash",
        field="price",
        value=100,
        source_type="manual",
        source_ref="captura manual",
    ).ready

    response = WorksheetsHandler(
        str(ProjectMemoryRuntime(project).db_path)
    ).get_worksheets("cash", "power-of-one")

    assert response["meta"]["source"].startswith("Evidencia confirmada")
    assert response["meta"]["pending_fields"]
    assert "volumen" in " ".join(response["meta"]["pending_fields"]).lower()


def test_xlsx_preview_and_each_decision_have_a_confirmed_or_actionable_method(
    tmp_path: Path,
) -> None:
    project = tmp_path / "company"
    project.mkdir()
    source = tmp_path / "cash.xlsx"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<?xml version=\"1.0\"?><worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData><row r=\"1\"><c r=\"A1\" t=\"inlineStr\"><is><t>precio</t></is></c><c r=\"B1\" t=\"inlineStr\"><is><t>volumen</t></is></c></row><row r=\"2\"><c r=\"A2\"><v>100</v></c><c r=\"B2\"><v>50</v></c></row></sheetData></worksheet>""",
        )
    store = EvidenceStore(project)

    preview = store.preview_file(source, "cash")

    assert preview.ready and preview.proposed == {"price": 100.0, "volume": 50.0}
    for decision, field, value in (
        (
            "people",
            "role_coverage",
            "Ventas y operaciones cubiertos; finanzas pendiente",
        ),
        ("strategy", "core_customer", "dueños de hogar que remodelan"),
        ("execution", "quarterly_priority", "reducir atrasos de entrega a 5%"),
    ):
        assert store.confirm_value(
            decision=decision,
            field=field,
            value=value,
            source_type="manual",
            source_ref="captura manual",
        ).ready
        snapshot = store.snapshot(decision)
        assert snapshot["fields"][field]["state"] == "confirmed"
        assert any(item["state"] == "pending" for item in snapshot["fields"].values())


def test_personal_columns_are_blocked_before_a_preview_is_persisted(
    tmp_path: Path,
) -> None:
    project = tmp_path / "company"
    project.mkdir()
    source = tmp_path / "with-clients.csv"
    source.write_text("cliente,precio\nAcme,100\n", encoding="utf-8")

    preview = EvidenceStore(project).preview_file(source, "cash")

    assert not preview.ready and preview.sensitivity == "personal_data"
    assert not (project / ".scaleup" / "memory" / "escala.db").exists()


def test_old_evidence_is_visible_as_stale_instead_of_a_false_current_value(
    tmp_path: Path,
) -> None:
    project = tmp_path / "company"
    project.mkdir()
    result = EvidenceStore(project).confirm_value(
        decision="cash",
        field="price",
        value=100,
        source_type="manual",
        source_ref="captura manual",
        observed_at="2020-01-01",
    )

    assert result.ready
    field = EvidenceStore(project).snapshot("cash")["fields"]["price"]
    assert field["state"] == "stale"
    assert field["confidence"] == 1.0
    assert field["observed_at"] == "2020-01-01"
