#!/bin/bash
# Push local commits and pull them into the clone that serves the live,
# symlinked skills (~/.claude/skills/escala-* -> <live_clone>/escala-skills/*).
#
# Two on-disk clones of the same remote can drift (S47.4/RAISE audit,
# 2026-08-10): fixes committed in the working clone never reach a coach
# until the live clone is updated. This script makes that step explicit
# and repeatable instead of a manually-remembered `git pull`.
set -euo pipefail

PATH="${PATH}:/usr/bin:/bin"

work_clone="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
live_clone="${1:-}"

if [[ -z "$live_clone" ]]; then
    echo "Uso: $0 <ruta-del-clon-que-sirve-los-symlinks-activos>" >&2
    echo "Ejemplo: $0 ~/Documents/GitHub/agente-de-escalamiento" >&2
    exit 2
fi

if [[ ! -d "$live_clone/.git" ]]; then
    echo "Error: '$live_clone' no es un repositorio git." >&2
    exit 1
fi

work_remote="$(git -C "$work_clone" remote get-url origin 2>/dev/null || true)"
live_remote="$(git -C "$live_clone" remote get-url origin 2>/dev/null || true)"

if [[ -z "$work_remote" || "$work_remote" != "$live_remote" ]]; then
    echo "Error: los remotos no coinciden — no son clones del mismo repo." >&2
    echo "  work_clone: $work_remote" >&2
    echo "  live_clone: $live_remote" >&2
    exit 1
fi

work_dirty="$(git -C "$work_clone" status --porcelain)"
if [[ -n "$work_dirty" ]]; then
    echo "Error: '$work_clone' tiene cambios sin commitear. Comitea o descarta antes de sincronizar." >&2
    exit 1
fi

live_dirty="$(git -C "$live_clone" status --porcelain)"
if [[ -n "$live_dirty" ]]; then
    echo "Error: '$live_clone' tiene cambios sin commitear. No se puede pull con seguridad." >&2
    exit 1
fi

work_branch="$(git -C "$work_clone" branch --show-current)"
live_branch="$(git -C "$live_clone" branch --show-current)"

echo "Push: $work_clone ($work_branch) -> origin"
git -C "$work_clone" push origin "$work_branch"

echo "Pull: origin -> $live_clone ($live_branch)"
git -C "$live_clone" pull --ff-only origin "$live_branch"

work_head="$(git -C "$work_clone" rev-parse HEAD)"
live_head="$(git -C "$live_clone" rev-parse HEAD)"

if [[ "$work_head" != "$live_head" ]]; then
    echo "Aviso: los HEADs no coinciden tras sincronizar ($work_branch != $live_branch, o divergencia real)." >&2
    echo "  $work_clone -> $work_head" >&2
    echo "  $live_clone -> $live_head" >&2
    exit 1
fi

echo "OK: ambos clones en $work_head"
