#!/usr/bin/env bash
# Emits tool_use signal to governance trail. Fire-and-forget, never blocks.
INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd','.'))" 2>/dev/null || echo ".")
TOOL=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
cd "$CWD" 2>/dev/null || exit 0
command -v rai &>/dev/null || exit 0
rai signal emit tool_use --tool "$TOOL" --quiet 2>/dev/null || true
exit 0
