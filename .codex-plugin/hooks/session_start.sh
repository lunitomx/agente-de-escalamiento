#!/usr/bin/env bash
# Injects RaiSE constitutional context at session start.
# Codex CLI injects stdout from SessionStart hooks as system context.
INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('cwd','.'))" 2>/dev/null || echo ".")
cd "$CWD" 2>/dev/null || exit 0
command -v rai &>/dev/null || exit 0

# --- Identity ---
printf "## RaiSE Context\n\n"
printf "You are Rai, the RaiSE AI governance agent. "
printf "RaiSE (Reliable AI Software Engineering) is a methodology and CLI framework "
printf "that adds governance, pipelines, gates, and patterns to AI-assisted development.\n\n"

# --- Developer profile (parse YAML with grep — no deps) ---
PROFILE_FILE="${RAI_HOME:-$HOME/.rai}/developer.yaml"
if [ -f "$PROFILE_FILE" ]; then
    DEV_NAME=$(grep "^name:" "$PROFILE_FILE" | head -1 | sed 's/name: *//')
    DEV_LEVEL=$(grep "^experience_level:" "$PROFILE_FILE" | head -1 | sed 's/experience_level: *//')
    DEV_LANG=$(grep "^  language:" "$PROFILE_FILE" | head -1 | sed 's/ *language: *//')
    [ -n "$DEV_NAME" ] && printf "Developer: %s | Level: %s | Language: %s\n\n" "$DEV_NAME" "${DEV_LEVEL:-ha}" "${DEV_LANG:-en}"
fi

# --- Active story + phase ---
STORY=$(rai session state --field active_story 2>/dev/null || true)
PHASE=$(rai session state --field phase 2>/dev/null || true)
[ -n "$STORY" ] && printf "Active story: %s (phase: %s)\n\n" "$STORY" "${PHASE:-unknown}"

# --- Skills ---
printf "Skills available: ask Codex to use any rai-* skill by name (e.g. rai-session-start, rai-story-implement).\n"
printf "Skills location: .agent/skills/\n"
exit 0
