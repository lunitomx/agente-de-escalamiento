#!/usr/bin/env bash
# Offline verifier: validates recorded hashes, assertions, and transcript
# semantics only; it never calls a model, installer, network, or runtime.
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import hashlib
import json
import re
from pathlib import Path

root = Path('.')
assertions = json.loads((root / 'assertions.json').read_text())
environment = json.loads((root / 'environment.json').read_text())
assert environment['bundle_version'] == '1.0.0'
assert environment['clients'] == {'claude_code': '2.1.241', 'codex_cli': '0.149.0'}
assert assertions['response_policy'] == {'no_paths': True, 'no_sqlite': True, 'no_skill_internals': True}
attestation = json.loads((root / 'attestation.json').read_text())
assert attestation['format'] == 'e22-client-smoke-attestation/v1'
assert attestation['provenance']['source'] == 'recorded disposable client runs'
assert attestation['redaction']['runtime_placeholder'] == '<RUNTIME>'
assert attestation['redaction']['raw_transcripts_retained'] is False
assert attestation['scope']['clients'] == ['claude', 'codex']
for filename, expected in attestation['sha256'].items():
    actual = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    assert actual == expected, f'hash mismatch: {filename}'

statement = 'Abriremos ventas en Mérida en octubre'
expected_outputs = [
    'Antes de pausar, ¿qué decisión o dato concreto quieres que recuerde para la próxima vez?',
    f'Entendí: {statement}. ¿Quieres que lo recuerde para la próxima vez? (sí/no)',
    'Listo. La próxima vez podremos retomar esa decisión.',
]
resume_prefix = f'La última vez dejamos como foco: {statement}.'
for client, expected_name in (('claude', 'Claude Code 2.1.241'), ('codex', 'Codex CLI 0.149.0')):
    records = [json.loads(line) for line in (root / f'{client}.jsonl').read_text().splitlines() if line]
    assert [record['event'] for record in records] == [
        'discovery', 'tool_call', 'tool_call', 'tool_call', 'new_session_tool_call', 'result'
    ], f'{client}: unexpected event sequence'
    discovery, *calls, result = records
    assert discovery == {
        'event': 'discovery', 'client': expected_name,
        'installed_public_skills': ['scaleup'], 'selected_skill': 'scaleup'
    }, f'{client}: discovery is not limited to scaleup'
    assert [call['output'] for call in calls[:3]] == expected_outputs, f'{client}: pause/confirm outputs differ'
    assert calls[3]['output'].startswith(resume_prefix), f'{client}: new session does not resume confirmed statement'
    assert all('<RUNTIME>/bin/scaleup-frontdoor conversation' in call['command'] for call in calls), f'{client}: wrong front door'
    assert result['event'] == 'result' and result['status'] == 'pass', f'{client}: did not pass'
    serialized = '\n'.join(json.dumps(record, ensure_ascii=False) for record in records).lower()
    assert '<runtime>' in serialized, f'{client}: missing required redaction'
    assert not re.search(r'/(tmp|home|var|etc)/|\b(sqlite|memory_facts|project_memory|session[_ -]?id|token|password|credential)\b', serialized), f'{client}: internal data leaked'
    record = assertions['clients'][client]
    assert record['status'] == 'pass' and record['evidence_file'] == f'{client}.jsonl'
print('e22 client-smoke evidence hashes, attestation, and semantics: OK')
PY
