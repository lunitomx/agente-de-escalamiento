#!/usr/bin/env bash
# Offline verifier: validates recorded hashes and assertions only; it never
# calls a model, installer, network, or project runtime.
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import hashlib, json
from pathlib import Path

root = Path('.')
assertions = json.loads((root / 'assertions.json').read_text())
for filename, expected in assertions['sha256'].items():
    actual = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    assert actual == expected, f'hash mismatch: {filename}'
for client in ('claude', 'codex'):
    record = assertions['clients'][client]
    assert record['status'] in {'pass', 'limited', 'fail'}
    assert record['evidence_file'] == f'{client}.jsonl'
    assert (root / record['evidence_file']).is_file()
print('e22 client-smoke evidence hashes and assertion schema: OK')
PY
