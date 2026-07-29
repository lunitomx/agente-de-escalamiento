#!/usr/bin/env python3
"""Run the E42 S42.1 entrepreneur journey qualification with synthetic/local data.

This script exercises the end-to-end ESCALA flow on the current development
machine. It does NOT replace validation on clean macOS/Windows hardware or
human acceptance; those are recorded separately.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from escala_server.lifecycle import (  # noqa: E402
    InstallRequest,
    LifecycleRuntime,
    build_install_bundle,
    install_package,
)
from escala_server.business_advisor import BusinessAdvisorHandler  # noqa: E402


def main() -> int:
    source_commit = _source_commit()
    evidence: dict[str, object] = {
        "schema_version": 1,
        "story": "S42.1",
        "epic": "E42",
        "source_commit": source_commit,
        "environment": "local-synthetic",
        "platform_matrix": ["macos", "windows"],
        "notes": [
            "This is synthetic/local evidence. Clean hardware and human acceptance are separate.",
        ],
    }

    with tempfile.TemporaryDirectory(prefix="e42-s42.1-") as temporary:
        root = Path(temporary)
        journey_results: dict[str, object] = {}

        # 1. Installation for both platforms (simulated).
        for platform in ("macos", "windows"):
            bundle = build_install_bundle(ROOT, root / "packages", "1.0.0", platform)
            request = InstallRequest(
                platform=platform,  # type: ignore[arg-type]
                version="1.0.0",
                install_root=root / f"install-{platform}",
                data_root=root / f"data-{platform}",
                database_path=root / f"data-{platform}" / "escala.sqlite",
                exchange_root=root / f"exchange-{platform}",
            )
            receipt = install_package(bundle, request)
            runtime = LifecycleRuntime(request)
            start_result = runtime.start()
            stop_result = runtime.stop()
            journey_results[f"install_{platform}"] = {
                "status": "pass"
                if start_result.status == "healthy" and stop_result.status == "stopped"
                else "fail",
                "install_receipt": receipt.model_dump(mode="json"),
                "start_result": start_result.model_dump(mode="json"),
                "stop_result": stop_result.model_dump(mode="json"),
            }

        # 2. Local workspace with synthetic company data.
        db_path = root / "data-macos" / "escala.sqlite"
        _seed_database(db_path)

        # 3. Advisor journey.
        advisor = BusinessAdvisorHandler(str(db_path))
        ask_result = advisor.ask("¿cómo mejoro mi flujo de efectivo?")
        daily_result = advisor.review_daily(
            "ayer vendí 5, hoy voy a cobrar, no tengo maíz"
        )
        debate_result = advisor.board_debate(
            decision="deberíamos abrir un nuevo local",
            context="empresa de alimentos, crecimiento en 20% anual",
        )
        journey_results["advisor_ask"] = {
            "status": "pass" if ask_result.get("answer") else "fail",
            "category": ask_result.get("category"),
        }
        journey_results["advisor_review_daily"] = {
            "status": "pass" if daily_result.get("observations") else "fail",
        }
        journey_results["advisor_debate"] = {
            "status": "pass" if debate_result.get("response") else "fail",
            "next_questions_count": len(debate_result.get("next_questions", [])),
        }

        # 4. Blockers / questions observed.
        blockers = _collect_blockers(journey_results)

        evidence["journey"] = journey_results
        evidence["blockers"] = blockers
        evidence["overall_status"] = (
            "pass" if all(r.get("status") == "pass" for r in journey_results.values()) else "fail"
        )

    evidence_dir = ROOT / "work/epics/e42-product-qualification-and-functional-catalog/evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "s42.1-local-journey.json"
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    status = evidence["overall_status"]
    print(f"S42.1 local qualification: {status.upper()}")
    print(f"Evidence: {evidence_path}")
    print(f"Blockers: {len(blockers)}")
    for blocker in blockers:
        print(f"  - {blocker}")
    return 0 if status == "pass" else 1


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


def _collect_blockers(journey_results: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    for step, result in journey_results.items():
        if isinstance(result, dict) and result.get("status") != "pass":
            blockers.append(f"{step}: {result.get('status')}")
    return blockers


def _source_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
