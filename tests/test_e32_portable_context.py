from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from coaching.router.conversation import run
from escala_server.evidence import AttachmentEnvelope, EvidenceStore
from escala_server.human_context import HumanContextStore
from escala_server.workspace import (
    WorkspaceIndexer,
    create_workspace,
    reconcile_canonical_document,
)


def test_host_authorized_attachment_uses_preview_without_user_file_path(
    tmp_path: Path,
) -> None:
    source = tmp_path / "cash.csv"
    source.write_text("precio,volumen\n100,20\n", encoding="utf-8")
    envelope = AttachmentEnvelope(
        "cash.csv",
        "text/csv",
        source,
        datetime.now(timezone.utc).date().isoformat(),
        True,
    )
    root = tmp_path / "company"
    root.mkdir()
    assert "elige una ruta" in run("quiero cuantificar cash", base_path=root).lower()
    assert "comparte un archivo" in run("archivo", base_path=root).lower()
    reply = run("te comparto el archivo", base_path=root, attachment=envelope)
    assert "vista previa lista" in reply.lower()
    assert str(source) not in reply
    rejected = EvidenceStore(root).preview_attachment(
        AttachmentEnvelope(
            "cash.csv",
            "text/csv",
            source,
            datetime.now(timezone.utc).date().isoformat(),
            False,
        ),
        "cash",
    )
    assert not rejected.ready and "autorización" in (rejected.reason or "")


def test_portable_evidence_rebuilds_only_after_explicit_reconciliation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "shared"
    assert create_workspace(workspace, "Lumen Casa").ready
    machine_a, machine_b = tmp_path / "machine-a", tmp_path / "machine-b"
    evidence = EvidenceStore(workspace, local_state_root=machine_a)
    saved = evidence.confirm_value(
        decision="cash",
        field="price",
        value="125",
        source_type="manual",
        source_ref="captura agregada",
    )
    assert saved.ready
    contribution = evidence.export_confirmed(
        workspace,
        decision="cash",
        author="Sofía",
        role="dirección",
        explicit_confirmation=True,
    )
    assert contribution.ready
    raw = contribution.path.read_text(encoding="utf-8")
    assert "escala.db" not in raw and "machine-a" not in raw and "cash.csv" not in raw
    # Another collaborator cannot use an unresolved contribution as a panel fact.
    assert WorkspaceIndexer(workspace, local_state_root=machine_b).rebuild().ready
    assert (
        EvidenceStore(workspace, local_state_root=machine_b).snapshot("cash")["fields"][
            "price"
        ]["state"]
        == "pending"
    )
    payload = yaml.safe_load(contribution.path.read_text(encoding="utf-8"))
    reconciled = reconcile_canonical_document(
        workspace,
        target="areas/cash/evidence.yaml",
        owner="Sofía",
        content={"content": payload["content"]},
        resolved_contribution_ids=(contribution.contribution_id,),
        confirm=True,
    )
    assert reconciled.ready
    index = WorkspaceIndexer(workspace, local_state_root=machine_b).rebuild()
    assert index.ready
    snapshot = EvidenceStore(workspace, local_state_root=machine_b).snapshot("cash")
    assert snapshot["fields"]["price"]["value"] == 125.0
    # Rebuilding a second time is idempotent and does not create another version.
    WorkspaceIndexer(workspace, local_state_root=machine_b).rebuild()
    assert (
        EvidenceStore(workspace, local_state_root=machine_b).snapshot("cash")["fields"][
            "price"
        ]["value"]
        == 125.0
    )


def test_board_uses_confirmed_company_context_and_only_board_human_projection(
    tmp_path: Path,
) -> None:
    store = EvidenceStore(tmp_path)
    assert store.confirm_value(
        decision="execution",
        field="kpi",
        value="entregas semanales",
        source_type="manual",
        source_ref="reunión semanal",
    ).ready
    human = HumanContextStore(tmp_path)
    assert human.confirm("role", "Directora general", explicit_confirmation=True).ready
    answer = run("opinión del board: el KPI de ejecución", base_path=tmp_path)
    assert "dato confirmado" in answer.lower()
    assert (
        "contexto humano autorizado" not in answer.lower()
    )  # preference is bounded, never rendered as accountability/private notes
