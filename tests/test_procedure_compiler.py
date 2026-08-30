from __future__ import annotations

import json
from pathlib import Path

import pytest

import validators.procedure_compiler as compiler
from validators.procedure_compiler import (
    MVP_PROCEDURE_IDS,
    build_mvp_procedure_files,
    compile_mvp_procedures,
    render_mvp_procedure_files,
)
from validators.procedure_contract import load_procedure_contract


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "procedures/mvp/templates.json"


def _projection() -> dict[str, object]:
    return json.loads(TEMPLATES.read_text(encoding="utf-8"))


def _use_projection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, payload: dict[str, object]
) -> None:
    path = tmp_path / "templates.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(compiler, "_template_path", lambda _root: path)


def test_compiles_exactly_the_six_mvp_contracts_with_node_traceability() -> None:
    compiled = compile_mvp_procedures()

    assert tuple(contract.id for contract in compiled.contracts) == tuple(
        sorted(MVP_PROCEDURE_IDS)
    )
    assert {trace.procedure_id for trace in compiled.release.procedures} == set(
        MVP_PROCEDURE_IDS
    )
    assert compiled.release.node_to_procedures
    for trace in compiled.release.procedures:
        assert trace.node_ids
        assert trace.evidence_refs
        assert set(trace.input_node_refs).issubset(
            {
                item.id
                for contract in compiled.contracts
                if contract.id == trace.procedure_id
                for item in contract.required_inputs + contract.optional_inputs
            }
        )


def test_compiled_contracts_keep_complete_unknown_safe_output_contract() -> None:
    for contract in compile_mvp_procedures().contracts:
        output = contract.output_contract
        assert output.open_questions
        assert output.artifact.status == "unknown"
        assert output.owner.status == "unknown"
        assert output.kpi.status == "unknown"
        assert output.who_what_when.status == "unknown"
        assert output.review_cadence.status == "unknown"
        assert contract.handoff.next_procedure_id in MVP_PROCEDURE_IDS
        assert all(update.mode == "proposed" for update in contract.state_updates)


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda payload: (
                payload["templates"][0].__setitem__(  # type: ignore[index]
                    "node_ids", ["candidate.cash.procedure.cash-tool"]
                ),
                payload["templates"][0].__setitem__(  # type: ignore[index]
                    "input_node_refs",
                    {
                        "input.company-context": ["candidate.cash.procedure.cash-tool"],
                        "input.decision-evidence": [
                            "candidate.cash.procedure.cash-tool"
                        ],
                    },
                ),
            ),
            "denied candidate reference",
        ),
        (
            lambda payload: (
                payload["templates"][0].__setitem__(  # type: ignore[index]
                    "node_ids", ["tool.unapproved-private-cash"]
                ),
                payload["templates"][0].__setitem__(  # type: ignore[index]
                    "input_node_refs",
                    {
                        "input.company-context": ["tool.unapproved-private-cash"],
                        "input.decision-evidence": ["tool.unapproved-private-cash"],
                    },
                ),
            ),
            "outside canonical release",
        ),
        (
            lambda payload: payload["templates"][0]["contract"].__setitem__(  # type: ignore[index]
                "evidence_refs", ["digest.sha256." + "f" * 64]
            ),
            "template projection invalid",
        ),
        (
            lambda payload: payload["templates"][0].__setitem__(  # type: ignore[index]
                "input_node_refs",
                {"input.company-context": ["tool.unapproved-private-cash"]},
            ),
            "template projection invalid",
        ),
    ],
)
def test_compiler_fails_closed_for_unapproved_candidate_node_evidence_or_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutate: object,
    match: str,
) -> None:
    payload = _projection()
    mutate(payload)  # type: ignore[operator]
    _use_projection(monkeypatch, tmp_path, payload)

    with pytest.raises(ValueError, match=match):
        compile_mvp_procedures()


def test_compiler_rejects_missing_cash_exclusion_boundary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    release = json.loads((ROOT / "ontology/v2/releases/s64.1.json").read_text())
    release["exclusions"] = release["exclusions"][:2]
    release_path = tmp_path / "s64.1.json"
    release_path.write_text(json.dumps(release), encoding="utf-8")
    monkeypatch.setattr(compiler, "_release_path", lambda _root: release_path)

    with pytest.raises(ValueError, match="cash exclusions are incomplete"):
        compile_mvp_procedures()


def test_compiler_rejects_candidate_hidden_in_step_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = _projection()
    payload["templates"][0]["contract"]["steps"][0]["produces"] = [  # type: ignore[index]
        "candidate.cash.procedure.cash-tool"
    ]
    _use_projection(monkeypatch, tmp_path, payload)

    with pytest.raises(ValueError, match="denied candidate reference"):
        compile_mvp_procedures()


@pytest.mark.parametrize("handoff", ["procedure.cash-tool", "procedure.unreviewed"])
def test_compiler_rejects_handoff_outside_the_mvp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, handoff: str
) -> None:
    payload = _projection()
    payload["templates"][0]["contract"]["handoff"]["next_procedure_id"] = handoff  # type: ignore[index]
    _use_projection(monkeypatch, tmp_path, payload)

    with pytest.raises(
        ValueError, match="handoff references a procedure outside the MVP"
    ):
        compile_mvp_procedures()


def test_generated_files_are_deterministic_and_validate_as_contracts() -> None:
    assert build_mvp_procedure_files()
    assert build_mvp_procedure_files(check=True)
    rendered = render_mvp_procedure_files(compile_mvp_procedures())
    for relative_path, contents in rendered.items():
        path = ROOT / "procedures/mvp" / relative_path
        assert path.read_text(encoding="utf-8") == contents
        if relative_path.endswith(".yaml"):
            assert load_procedure_contract(path).id in MVP_PROCEDURE_IDS


def test_generated_release_contains_no_raw_source_or_candidate_queue_fields() -> None:
    payload = json.loads((ROOT / "procedures/mvp/release.json").read_text())
    serialized = json.dumps(payload, sort_keys=True)
    assert "candidate_id" not in serialized
    assert "source_ids" not in serialized
    assert "source_text" not in serialized
    assert "cash-tool" not in serialized
