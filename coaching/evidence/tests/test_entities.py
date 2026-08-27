from coaching.evidence import run
from coaching.evidence.entities import EntityCandidate, resolve_entities


def _candidate(**overrides):
    data = {
        "candidate_id": "a",
        "entity_type": "customer",
        "name": "Acme SA",
        "primary_id": "RFC-123",
        "source": "erp.csv",
    }
    data.update(overrides)
    return EntityCandidate(**data)


def test_primary_id_and_exact_name_resolve_but_name_difference_stays_ambiguous():
    resolved = resolve_entities(
        [_candidate(), _candidate(candidate_id="b", source="crm.csv")]
    )
    assert resolved[0].status == "resolved"

    ambiguous = resolve_entities(
        [_candidate(), _candidate(candidate_id="b", name="ACME Internacional")]
    )
    assert ambiguous[0].status == "ambiguous"


def test_name_only_never_merges():
    results = resolve_entities(
        [
            _candidate(candidate_id="a", primary_id=None),
            _candidate(candidate_id="b", primary_id=None, source="crm.csv"),
        ]
    )
    assert results[0].status == "unresolved"


def test_entity_resolution_action_returns_ambiguity_to_caller():
    result = run(
        {
            "action": "entity_resolution",
            "candidates": [
                _candidate().model_dump(),
                _candidate(candidate_id="b", name="ACME Internacional").model_dump(),
            ],
        }
    )
    assert result["errors"] == []
    assert result["artifacts"]["resolutions"][0]["status"] == "ambiguous"
