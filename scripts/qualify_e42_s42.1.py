#!/usr/bin/env python3
"""Run the E42 S42.1 entrepreneur journey qualification with synthetic/local data.

This script exercises the end-to-end ESCALA flow on the current development
machine, records a per-platform matrix, and runs a set of safe negative cases.
It does NOT replace validation on clean macOS/Windows hardware or human
acceptance; those are recorded separately.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from escala_server.lifecycle import (  # noqa: E402
    InstallRequest,
    LifecycleError,
    LifecycleRuntime,
    build_install_bundle,
    install_package,
)
from escala_server.business_advisor import BusinessAdvisorHandler  # noqa: E402
from escala_server.workspace.authority import WorkspaceConfig, validate_workspace  # noqa: E402


Platform = Literal["macos", "windows"]
PLATFORMS: tuple[Platform, Platform] = ("macos", "windows")
VERSION = "1.0.0"


def main() -> int:
    source_commit = _source_commit()
    evidence_dir = (
        ROOT / "work/epics/e42-product-qualification-and-functional-catalog/evidence"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    evidence: dict[str, Any] = {
        "schema_version": 1,
        "story": "S42.1",
        "epic": "E42",
        "source_commit": source_commit,
        "environment": "local-synthetic",
        "platform_matrix": {},
        "requirements": [
            {
                "id": "REQ-E42-001",
                "description": "Recorrido completo probado de instalación a seguimiento",
                "status": "pending",
                "evidence": "",
            },
            {
                "id": "REQ-E42-003",
                "description": "Aceptación en macOS y Windows limpios",
                "status": "pending",
                "evidence": "",
            },
        ],
        "notes": [
            "Evidencia sintética/local. El hardware limpio y la aceptación humana se registran aparte.",
            "Las validaciones de Windows se ejecutan en la máquina de desarrollo actual mediante rutas sintéticas.",
        ],
        "external_validation": {
            "clean_macos_hardware": "pending",
            "clean_windows_hardware": "pending",
            "human_acceptance": "pending",
            "reason": "Requieren máquina física o virtual dedicada y revisión con el dueño del producto.",
        },
    }

    with tempfile.TemporaryDirectory(prefix="e42-s42.1-") as temporary:
        root = Path(temporary)
        journey_steps: list[dict[str, Any]] = []
        platform_matrix: dict[str, dict[str, Any]] = {}

        # Positive journey: installation and runtime on each platform.
        for platform in PLATFORMS:
            matrix_entry = _run_install_and_runtime(
                root, platform, journey_steps, source_commit
            )
            platform_matrix[platform] = matrix_entry

        # Local workspace with synthetic company data.
        db_path = root / "data-macos" / "escala.sqlite"
        _seed_database(db_path)
        _record_step(
            journey_steps,
            "workspace_seed",
            "Crear espacio local con datos sintéticos de empresa",
            "macos",
            "Base de datos local contiene empresa y hecho de memoria",
            f"Se insertaron datos en {db_path.name}",
            "pass",
        )

        advisor = BusinessAdvisorHandler(str(db_path))

        # Business-advisor positive cases covering Cash / Strategy / Execution.
        _run_advisor_ask(
            advisor,
            "cash",
            "¿cómo mejoro mi flujo de efectivo?",
            journey_steps,
        )
        _run_advisor_ask(
            advisor,
            "strategy",
            "¿deberíamos expandirnos a otro mercado?",
            journey_steps,
        )
        _run_advisor_daily(
            advisor,
            "ayer vendí 5, hoy voy a cobrar, no tengo maíz",
            journey_steps,
        )
        _run_advisor_debate(
            advisor,
            decision="deberíamos abrir un nuevo local",
            context="empresa de alimentos, crecimiento en 20% anual",
            journey_steps=journey_steps,
        )

        # Negative / safe-failure cases.
        negative_cases: list[dict[str, Any]] = []
        negative_cases.extend(_run_negative_install_cases(root))
        negative_cases.extend(_run_negative_authority_cases())
        negative_cases.extend(_run_negative_advisor_cases(advisor))
        negative_cases.append(_run_negative_corrupted_bundle(root))

        # Blockers are any positive step that did not pass or any negative case
        # that did not reject the bad input as expected.
        blockers = _collect_blockers(journey_steps, negative_cases)

        positive_pass = all(step["status"] == "pass" for step in journey_steps)
        negative_pass = all(case["status"] == "pass" for case in negative_cases)
        overall_status = "pass" if positive_pass and negative_pass else "fail"

        # Update requirement evidence.
        for requirement in evidence["requirements"]:
            if requirement["id"] == "REQ-E42-001":
                requirement["status"] = overall_status
                requirement["evidence"] = (
                    "Recorrido local ejecutado con instalación, espacio de trabajo, "
                    "asesoría Cash/Strategy/Ejecución y debate de board."
                )
            elif requirement["id"] == "REQ-E42-003":
                requirement["status"] = "partial"
                requirement["evidence"] = (
                    "Matriz de plataforma sintética generada para macOS y Windows; "
                    "faltan recibos de hardware limpio."
                )

        evidence["platform_matrix"] = platform_matrix
        evidence["journey_steps"] = journey_steps
        evidence["negative_cases"] = negative_cases
        evidence["blockers"] = blockers
        evidence["overall_status"] = overall_status

    evidence_path = evidence_dir / "s42.1-local-journey.json"
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    markdown_path = evidence_dir / "s42.1-local-journey.md"
    markdown_path.write_text(
        _render_markdown(evidence, source_commit),
        encoding="utf-8",
    )

    status = evidence["overall_status"]
    print(f"S42.1 local qualification: {status.upper()}")
    print(f"Evidence JSON: {evidence_path}")
    print(f"Evidence MD:   {markdown_path}")
    print(
        f"Journey steps: {len(journey_steps)} | Negative cases: {len(negative_cases)}"
    )
    print(f"Blockers: {len(blockers)}")
    for blocker in blockers:
        print(f"  - {blocker}")
    return 0 if status == "pass" else 1


def _run_install_and_runtime(
    root: Path,
    platform: Platform,
    journey_steps: list[dict[str, Any]],
    source_commit: str,
) -> dict[str, Any]:
    """Install, start and stop one platform, recording matrix and steps."""
    bundle = build_install_bundle(ROOT, root / "packages", VERSION, platform)
    request = InstallRequest(
        platform=platform,  # type: ignore[arg-type]
        version=VERSION,
        install_root=root / f"install-{platform}",
        data_root=root / f"data-{platform}",
        database_path=root / f"data-{platform}" / "escala.sqlite",
        exchange_root=root / f"exchange-{platform}",
    )
    receipt = install_package(bundle, request)
    runtime = LifecycleRuntime(request)
    start_result = runtime.start()
    stop_result = runtime.stop()

    install_ok = receipt.status == "pass"
    start_ok = start_result.status == "healthy"
    stop_ok = stop_result.status == "stopped"
    overall = "pass" if install_ok and start_ok and stop_ok else "fail"

    _record_step(
        journey_steps,
        f"install_{platform}",
        f"Instalación local en {platform}",
        platform,
        "Paquete instala sin layout de repositorio ni red",
        f"receipt={receipt.status}, checks={len(receipt.checks)}",
        "pass" if install_ok else "fail",
    )
    _record_step(
        journey_steps,
        f"runtime_start_{platform}",
        f"Arranque del runtime en {platform}",
        platform,
        "Runtime reporta estado healthy local",
        f"status={start_result.status}, hosted_service={start_result.hosted_service}",
        "pass" if start_ok else "fail",
    )
    _record_step(
        journey_steps,
        f"runtime_stop_{platform}",
        f"Detención del runtime en {platform}",
        platform,
        "Runtime se detiene sin dejar servicio hospedado",
        f"status={stop_result.status}",
        "pass" if stop_ok else "fail",
    )

    return {
        "platform": platform,
        "version": VERSION,
        "source_commit": source_commit,
        "environment": "local-synthetic",
        "install_status": receipt.status,
        "runtime_start_status": start_result.status,
        "runtime_stop_status": stop_result.status,
        "network_required": receipt.network_required,
        "hosted_service": start_result.hosted_service,
        "authoritative_sqlite_sync": receipt.authoritative_sqlite_sync,
        "overall_status": overall,
    }


def _run_advisor_ask(
    advisor: BusinessAdvisorHandler,
    category: str,
    question: str,
    journey_steps: list[dict[str, Any]],
) -> None:
    result = advisor.ask(question)
    ok = result.get("status") == "ok" and result.get("category") == category
    _record_step(
        journey_steps,
        f"advisor_ask_{category}",
        f"Asesoría {category}: {question}",
        "macos",
        f"Respuesta categorizada como {category} sin usar datos reales",
        f"category={result.get('category')}, status={result.get('status')}",
        "pass" if ok else "fail",
    )


def _run_advisor_daily(
    advisor: BusinessAdvisorHandler,
    daily_text: str,
    journey_steps: list[dict[str, Any]],
) -> None:
    result = advisor.review_daily(daily_text)
    ok = result.get("status") == "ok" and result.get("observations")
    _record_step(
        journey_steps,
        "advisor_review_daily",
        "Revisión de daily huddle",
        "macos",
        "Daily es calificado y se generan observaciones",
        f"score={result.get('score')}/{result.get('score_max')}",
        "pass" if ok else "fail",
    )


def _run_advisor_debate(
    advisor: BusinessAdvisorHandler,
    decision: str,
    context: str,
    journey_steps: list[dict[str, Any]],
) -> None:
    result = advisor.board_debate(decision=decision, context=context)
    ok = result.get("status") == "ok" and result.get("response")
    _record_step(
        journey_steps,
        "advisor_debate",
        "Debate de board sobre decisión estratégica",
        "macos",
        "Se genera análisis con las 4 Decisiones y siguientes preguntas",
        f"next_questions={len(result.get('next_questions', []))}",
        "pass" if ok else "fail",
    )


def _run_negative_install_cases(root: Path) -> list[dict[str, Any]]:
    """Negative cases that exercise the installer rejection paths."""
    cases: list[dict[str, Any]] = []

    # Cross-platform mismatch: Windows bundle + macOS request.
    windows_bundle = build_install_bundle(ROOT, root / "packages", VERSION, "windows")
    macos_request = InstallRequest(
        platform="macos",  # type: ignore[arg-type]
        version=VERSION,
        install_root=root / "bad-install-macos",
        data_root=root / "bad-data-macos",
        database_path=root / "bad-data-macos" / "escala.sqlite",
        exchange_root=root / "bad-exchange-macos",
    )
    cases.append(
        _expect_lifecycle_error(
            "platform_mismatch_rejected",
            "Bundle de Windows rechazado cuando se solicita instalar en macOS",
            lambda: install_package(windows_bundle, macos_request),
            "platform_mismatch",
        )
    )

    # Version mismatch: correct platform, wrong requested version.
    macos_bundle = build_install_bundle(ROOT, root / "packages", VERSION, "macos")
    bad_version_request = InstallRequest(
        platform="macos",  # type: ignore[arg-type]
        version="9.9.9",
        install_root=root / "bad-version-install",
        data_root=root / "bad-version-data",
        database_path=root / "bad-version-data" / "escala.sqlite",
        exchange_root=root / "bad-version-exchange",
    )
    cases.append(
        _expect_lifecycle_error(
            "version_mismatch_rejected",
            "Versión solicitada distinta a la del bundle es rechazada",
            lambda: install_package(macos_bundle, bad_version_request),
            "version_mismatch",
        )
    )

    return cases


def _run_negative_authority_cases() -> list[dict[str, Any]]:
    """Negative cases for workspace authority boundaries."""
    cases: list[dict[str, Any]] = []

    # Exchange root inside data_root creates an ambiguous authority boundary.
    data_root = Path("/tmp/e42-authority-data")
    exchange_inside_data = data_root / "exchange"
    config = WorkspaceConfig(
        platform="macos",  # type: ignore[arg-type]
        data_root=data_root,
        database_path=data_root / "escala.sqlite",
        exchange_root=exchange_inside_data,
    )
    receipt = validate_workspace(config)
    cases.append(
        {
            "id": "exchange_inside_data_root_rejected",
            "description": "Exchange dentro de data_root rechazado por autoridad ambigua",
            "expected": "workspace receipt con finding ambiguous_root",
            "observed": f"status={receipt.status}, findings={[f.code for f in receipt.findings]}",
            "status": "pass"
            if receipt.status == "fail"
            and any(f.code == "ambiguous_root" for f in receipt.findings)
            else "fail",
        }
    )

    # Database inside the exchange root rejects authoritative SQLite sync.
    exchange_root = Path("/tmp/e42-authority-exchange")
    config = WorkspaceConfig(
        platform="windows",  # type: ignore[arg-type]
        data_root=Path("/tmp/e42-authority-data2"),
        database_path=exchange_root / "shared.sqlite",
        exchange_root=exchange_root,
    )
    receipt = validate_workspace(config)
    cases.append(
        {
            "id": "database_in_exchange_rejected",
            "description": "Base de datos dentro del exchange rechazada: sync autoritativo prohibido",
            "expected": "workspace receipt con finding authoritative_sqlite_sync_forbidden",
            "observed": f"status={receipt.status}, findings={[f.code for f in receipt.findings]}",
            "status": "pass"
            if receipt.status == "fail"
            and any(
                f.code == "authoritative_sqlite_sync_forbidden"
                for f in receipt.findings
            )
            else "fail",
        }
    )

    return cases


def _run_negative_advisor_cases(
    advisor: BusinessAdvisorHandler,
) -> list[dict[str, Any]]:
    """Negative cases that show safe handling of bad advisor input."""
    cases: list[dict[str, Any]] = []

    empty_ask = advisor.ask("")
    cases.append(
        {
            "id": "empty_question_rejected",
            "description": "Pregunta vacía al asesor devuelve error sin lanzar excepción",
            "expected": "status=error y mensaje explicativo",
            "observed": f"status={empty_ask.get('status')}, message={empty_ask.get('message')}",
            "status": "pass"
            if empty_ask.get("status") == "error" and empty_ask.get("message")
            else "fail",
        }
    )

    empty_daily = advisor.review_daily("")
    cases.append(
        {
            "id": "empty_daily_review_recoverable",
            "description": "Daily vacío se califica como 0 puntos sin romper el flujo",
            "expected": "status=ok y observaciones explicativas",
            "observed": f"status={empty_daily.get('status')}, score={empty_daily.get('score')}",
            "status": "pass"
            if empty_daily.get("status") == "ok" and empty_daily.get("observations")
            else "fail",
        }
    )

    return cases


def _run_negative_corrupted_bundle(root: Path) -> dict[str, Any]:
    """A corrupted archive must be rejected before any installation."""
    corrupted = root / "corrupted.zip"
    corrupted.write_bytes(b"this is not a zip file")
    request = InstallRequest(
        platform="macos",  # type: ignore[arg-type]
        version=VERSION,
        install_root=root / "corrupted-install",
        data_root=root / "corrupted-data",
        database_path=root / "corrupted-data" / "escala.sqlite",
        exchange_root=root / "corrupted-exchange",
    )
    try:
        install_package(corrupted, request)
    except LifecycleError as exc:
        return {
            "id": "corrupted_bundle_rejected",
            "description": "Bundle corrupto o inválido rechazado antes de escribir en disco",
            "expected": "LifecycleError con código bundle_invalid o bundle_manifest_invalid",
            "observed": f"LifecycleError code={exc.code}",
            "status": "pass"
            if exc.code in {"bundle_invalid", "bundle_manifest_invalid"}
            else "fail",
        }
    return {
        "id": "corrupted_bundle_rejected",
        "description": "Bundle corrupto o inválido rechazado antes de escribir en disco",
        "expected": "LifecycleError con código bundle_invalid o bundle_manifest_invalid",
        "observed": "install_package aceptó el bundle corrupto",
        "status": "fail",
    }


def _expect_lifecycle_error(
    case_id: str,
    description: str,
    callable_: Any,
    expected_code: str,
) -> dict[str, Any]:
    try:
        callable_()
    except LifecycleError as exc:
        return {
            "id": case_id,
            "description": description,
            "expected": f"LifecycleError code={expected_code}",
            "observed": f"LifecycleError code={exc.code}",
            "status": "pass" if exc.code == expected_code else "fail",
        }
    return {
        "id": case_id,
        "description": description,
        "expected": f"LifecycleError code={expected_code}",
        "observed": "no se lanzó LifecycleError",
        "status": "fail",
    }


def _record_step(
    steps: list[dict[str, Any]],
    step_id: str,
    description: str,
    platform: str,
    expected: str,
    observed: str,
    status: str,
) -> None:
    steps.append(
        {
            "id": step_id,
            "description": description,
            "platform": platform,
            "expected": expected,
            "observed": observed,
            "status": status,
        }
    )


def _collect_blockers(
    journey_steps: list[dict[str, Any]],
    negative_cases: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    for step in journey_steps:
        if step.get("status") != "pass":
            blockers.append(f"{step['id']}: {step.get('observed')}")
    for case in negative_cases:
        if case.get("status") != "pass":
            blockers.append(f"{case['id']}: {case.get('observed')}")
    return blockers


def _seed_database(db_path: Path) -> None:
    """Seed a local SQLite database with synthetic company data."""
    import uuid

    from escala_server.schema import init_db

    conn = init_db(str(db_path))
    company_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO companies (id, name, industry, metadata) VALUES (?, ?, ?, ?)",
        (company_id, "Nopal Foods S.A. de C.V.", "Alimentos", '{"size":"pyme"}'),
    )
    conn.execute(
        "INSERT INTO memory_facts (key, value) VALUES (?, ?)",
        ("company/annual_growth", "20"),
    )
    conn.commit()
    conn.close()


def _source_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _render_markdown(evidence: dict[str, Any], source_commit: str) -> str:
    lines = [
        "# S42.1 — Viaje completo e instalaciones limpias (evidencia local)",
        "",
        f"- **status:** {evidence['overall_status']}",
        f"- **story:** {evidence['story']}",
        f"- **epic:** {evidence['epic']}",
        f"- **source_commit:** `{source_commit}`",
        f"- **environment:** {evidence['environment']}",
        "",
        "## Requisitos",
        "",
    ]
    for requirement in evidence["requirements"]:
        lines.append(
            f"- **{requirement['id']}** ({requirement['status']}): {requirement['description']}"
        )
        lines.append(f"  - {requirement['evidence']}")
    lines.extend(["", "## Matriz de plataforma", ""])
    for platform, matrix in evidence["platform_matrix"].items():
        lines.append(f"### {platform}")
        lines.append(f"- version: {matrix['version']}")
        lines.append(f"- install_status: {matrix['install_status']}")
        lines.append(f"- runtime_start_status: {matrix['runtime_start_status']}")
        lines.append(f"- runtime_stop_status: {matrix['runtime_stop_status']}")
        lines.append(f"- network_required: {matrix['network_required']}")
        lines.append(f"- hosted_service: {matrix['hosted_service']}")
        lines.append(
            f"- authoritative_sqlite_sync: {matrix['authoritative_sqlite_sync']}"
        )
        lines.append(f"- overall_status: {matrix['overall_status']}")
        lines.append("")
    lines.extend(["", "## Pasos del recorrido", ""])
    for step in evidence["journey_steps"]:
        lines.append(f"### {step['id']} ({step['status']})")
        lines.append(f"- plataforma: {step['platform']}")
        lines.append(f"- descripción: {step['description']}")
        lines.append(f"- esperado: {step['expected']}")
        lines.append(f"- observado: {step['observed']}")
    lines.extend(["", "## Casos negativos", ""])
    for case in evidence["negative_cases"]:
        lines.append(f"### {case['id']} ({case['status']})")
        lines.append(f"- descripción: {case['description']}")
        lines.append(f"- esperado: {case['expected']}")
        lines.append(f"- observado: {case['observed']}")
    lines.extend(["", "## Validación externa pendiente", ""])
    external = evidence["external_validation"]
    lines.append(f"- clean_macos_hardware: {external['clean_macos_hardware']}")
    lines.append(f"- clean_windows_hardware: {external['clean_windows_hardware']}")
    lines.append(f"- human_acceptance: {external['human_acceptance']}")
    lines.append(f"- razón: {external['reason']}")
    if evidence["blockers"]:
        lines.extend(["", "## Bloqueos", ""])
        for blocker in evidence["blockers"]:
            lines.append(f"- {blocker}")
    lines.extend(["", "## Notas", ""])
    for note in evidence["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
