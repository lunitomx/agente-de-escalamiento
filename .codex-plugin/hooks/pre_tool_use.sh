#!/usr/bin/env bash
# Blocks tool execution when a RaiSE HITL gate is pending approval.
# Exits 2 (block) with reason on stderr; exits 0 (allow) otherwise.
INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd','.'))" 2>/dev/null || echo ".")
cd "$CWD" 2>/dev/null || exit 0
command -v rai &>/dev/null || exit 0
GATE=$(rai pipeline gate-check --quiet 2>/dev/null || true)
if [ -n "$GATE" ]; then
    printf "Gate pending: %s — approve with: rai pipeline approve\n" "$GATE" >&2
    exit 2
fi
exit 0
