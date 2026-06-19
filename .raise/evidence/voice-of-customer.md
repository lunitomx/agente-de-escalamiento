# Canonical Voice of Customer evidence contract

This is the source of truth for the local Voice of Customer evidence system.
Do not use old E19/E20 draft folders as the source of truth.

## Purpose

Voice of Customer evidence exists so ScaleUp strategy claims can cite real
customer language instead of relying on agent assumptions.

## Implemented API

The implementation lives in `validators/voice_of_customer.py`.

- `CustomerEvidenceRecord`: typed evidence record with source, context, date,
  quote, segment, tags, review status, and fixture marker.
- `load_evidence_records(path)`: loads YAML evidence records.
- `validate_evidence_file(path)`: returns readable validation errors.
- `normalize_raw_quotes(raw_quotes)`: turns raw quote dictionaries into
  evidence records while preserving missing provenance as review gaps.
- `map_evidence_to_strategy(records)`: maps approved evidence into cited
  strategy inputs, gaps, and contradictions.

## Fixture Location

Test fixtures live under `tests/fixtures/voice_of_customer/`.

Fixture data is for tests and examples. Fixture data is not real customer
evidence unless an operator replaces it with actual sourced customer records and
marks the record as real (`is_fixture: false`) after review.

## Future Production Storage

Until S34.5, production storage is intentionally not implemented. Future work
should add real customer evidence under a reviewed project evidence location
before claiming that strategic outputs are backed by real customers.

Recommended future convention:

- `.raise/evidence/voice-of-customer/records/*.yaml` for reviewed local records.
- `tests/fixtures/voice_of_customer/*.yaml` only for tests.

## Evidence IDs And Citations

Strategy outputs must cite evidence ids. A strategy input without evidence ids
is a gap, not a claim.

Example citation:

```text
Brand Promise input: weekly cash clarity for founder-led service companies
Evidence ids: voc-map-001, voc-map-002
```

## Loading Example

```python
from pathlib import Path
from validators.voice_of_customer import load_evidence_records

records = load_evidence_records(Path("tests/fixtures/voice_of_customer/valid.yaml"))
```

## Normalization Example

```python
from validators.voice_of_customer import normalize_raw_quotes

result = normalize_raw_quotes([
    {
        "quote": "The weekly cash review helped us decide faster.",
        "source_type": "interview",
        "source_label": "Founder interview with Maria",
        "captured_at": "2026-06-02",
        "context": "Cash acceleration follow-up.",
        "customer_segment": "founder-led services company",
        "evidence_tags": ["cash", "speed"],
    }
])
```

## Strategy Mapping Example

```python
from validators.voice_of_customer import map_evidence_to_strategy

mapping = map_evidence_to_strategy(records)
for item in mapping.inputs:
    print(item.category, item.evidence_ids)
for gap in mapping.gaps:
    print(gap.category, gap.reason)
```

## Gap Handling

If `map_evidence_to_strategy` returns gaps, strategy skills must ask for the
missing evidence one question at a time. They must not invent Core Customer,
Brand Promise, positioning, OPSP, 7 Strata, or Strategy Canvas claims.

## Closure Boundary

E34 delivers the local evidence contract, fixture-backed validation,
normalization, mapping, and strategy prompt hardening. It does not deliver CRM
ingestion, external review scraping, production evidence storage, or E35 golden
case drift gates.

