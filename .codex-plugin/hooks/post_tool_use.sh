#!/usr/bin/env bash
# PostToolUse — governance trail signal + MCP staleness detection.
# Fire-and-forget on all paths: never blocks the agent.
INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd','.'))" 2>/dev/null || echo ".")
TOOL=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
cd "$CWD" 2>/dev/null || exit 0
command -v rai &>/dev/null || exit 0

# 1. Emit governance signal.
rai signal emit tool_use --tool "$TOOL" --quiet 2>/dev/null || true

# 2. MCP staleness check (same logic as Claude Code's PostToolUse/Bash hook).
# Warns when a git merge/pull/rebase changes MCP server source files and the
# running server is now stale. RAISE_CC_SESSION_ID is unavailable in Codex v1
# but the staleness module is session-agnostic and works without it.
echo "$INPUT" | uv run python -m raise_cli.hooks.posttooluse 2>/dev/null || true

exit 0
