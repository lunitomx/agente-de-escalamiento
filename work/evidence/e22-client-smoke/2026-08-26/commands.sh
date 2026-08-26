#!/usr/bin/env bash
# Reproducible commands used to collect this evidence. Each client gets a
# disposable installation and a separate fictitious project.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
run_root="${RUN_ROOT:?Set RUN_ROOT to a writable temporary directory}"
client="${1:?claude or codex}"
project="${run_root}/${client}-project"
install_root="${run_root}/${client}-home"

rm -rf "$project" "$install_root"
mkdir -p "$project"
bash "$repo_root/.scaleup/install.sh" --target "$client" --destination-root "$install_root"

# The installer produces the platform's actual discovery directory. Claude Code
# accepts project .claude/skills; Codex discovers project .agents/skills. These
# copies are verbatim installed public skills, not source-checkout skills.
if [[ "$client" == "claude" ]]; then
  mkdir -p "$project/.claude/skills"
  cp -a "$install_root/.claude/skills/scaleup" "$project/.claude/skills/scaleup"
  runtime="$install_root/.claude/scaleup"
  allowed="Bash($runtime/bin/scaleup-frontdoor conversation *)"
  (
    cd "$project"
    claude --print --verbose --output-format stream-json --max-budget-usd 1.00 \
      --allowedTools "$allowed" -- \
      "Usa únicamente la skill pública scaleup que descubras en este proyecto. Sin explicar herramientas ni rutas, realiza esta secuencia llamando su comando fijo una vez por frase: 'quiero pausar'; 'Abriremos ventas en Mérida en octubre'; 'sí'; y, como sesión nueva, 'retomemos'. Devuelve al final sólo las cuatro respuestas del coach, etiquetadas 1 a 4." \
      > "$run_root/claude.raw.jsonl"
  )
else
  mkdir -p "$project/.agents/skills"
  cp -a "$install_root/.codex/skills/scaleup" "$project/.agents/skills/scaleup"
  codex exec --ephemeral --json --approve-for-me --skip-git-repo-check -C "$project" \
    "Usa únicamente la skill pública scaleup que descubras en este proyecto. Sin explicar herramientas ni rutas, realiza esta secuencia llamando su comando fijo una vez por frase: 'quiero pausar'; 'Abriremos ventas en Mérida en octubre'; 'sí'; y, como sesión nueva, 'retomemos'. Devuelve al final sólo las cuatro respuestas del coach, etiquetadas 1 a 4." \
    > "$run_root/codex.raw.jsonl"
fi

find "$install_root" -type f -name SKILL.md | sort
find "$project/.scaleup/memory" -maxdepth 1 -type f -printf '%f %s\\n' | sort
