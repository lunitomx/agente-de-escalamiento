#!/usr/bin/env bash
# =============================================================
# Instalador del Agente de Escalamiento
# Detecta plataforma(s) disponible(s) y configura los skills
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_NAME="agente-de-escalamiento"
VERSION="1.0.0"

# E56: por defecto se instala una sola puerta conversacional.
SKILLS_ONLY=false
if [[ "${1:-}" == "--skills-only" ]]; then
    SKILLS_ONLY=true
elif [[ $# -gt 0 ]]; then
    echo "Uso: ./install.sh [--skills-only]" >&2
    exit 2
fi

# Colores
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║   Agente de Escalamiento — Instalador v${VERSION}  ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ----------------------
# Detecta plataformas
# ----------------------
PLATAFORMAS=()

if command -v claude &>/dev/null; then
    PLATAFORMAS+=("claude")
    echo -e "  ${VERDE}✓${NC} Claude Code detectado"
fi

if command -v hermes &>/dev/null; then
    PLATAFORMAS+=("hermes")
    echo -e "  ${VERDE}✓${NC} Hermes Agent detectado"
fi

if command -v codex &>/dev/null; then
    PLATAFORMAS+=("codex")
    echo -e "  ${VERDE}✓${NC} Codex CLI detectado"
fi

if [ ${#PLATAFORMAS[@]} -eq 0 ]; then
    echo -e "${AMARILLO}⚠ No se detectó ninguna plataforma compatible.${NC}"
    echo "  Instala Claude Code, Hermes Agent o Codex CLI primero."
    echo ""
    echo "  Claude Code: https://docs.anthropic.com/en/docs/claude-code"
    echo "  Hermes:      https://hermes-agent.nousresearch.com/docs"
    echo "  Codex CLI:   https://github.com/openai/codex"
    exit 1
fi

# ----------------------
# Función de instalación (SYMLINKS)
# ----------------------
instalar_en() {
    local plataforma="$1"
    local destino="$2"

    echo ""
    echo -e "  → Instalando en ${CYAN}${plataforma}${NC}..."

    mkdir -p "$destino"

    # Primero eliminar symlinks viejos (por si cambió la ruta del repo)
    for link in "$destino"/escala-*; do
        if [ -L "$link" ]; then
            rm "$link"
        fi
    done

    # E56: una puerta pública; las capacidades se cargan desde su catálogo.
    local skill_dir="$SCRIPT_DIR/escala-skills/escala"
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
        echo "Skill público ESCALA no encontrado: $skill_dir" >&2
        return 1
    fi
    ln -sfn "$skill_dir" "$destino/escala"
    local count=1

    echo -e "    ${VERDE}✓${NC} $count skills instalados (symlinks) en ${destino}"
}

# ----------------------
# Función de instalación para skills viejos (migración cp→symlink)
# ----------------------
echo ""
echo -e "  ${CYAN}Instalando skills como symlinks...${NC}"
for p in "${PLATAFORMAS[@]}"; do
    case "$p" in
        claude)  instalar_en "Claude Code" "$HOME/.claude/skills" ;;
        hermes)  instalar_en "Hermes Agent" "$HOME/.hermes/skills" ;;
        codex)   instalar_en "Codex CLI" "$HOME/.codex/skills" ;;
    esac
done

# ----------------------
if [[ "$SKILLS_ONLY" == true ]]; then
    echo "  Instalación de skill completada: habla con ESCALA en lenguaje natural."
    exit 0
fi

# Configurar RaiSE MCP para Codex (sin tocar el estado global del usuario)
# ----------------------
if [[ " ${PLATAFORMAS[*]} " == *" codex "* ]]; then
    echo ""
    echo -e "  ${CYAN}Configurando RaiSE MCP para Codex...${NC}"
    "$SCRIPT_DIR/scripts/configure_codex_mcp.sh" "$SCRIPT_DIR" || \
        echo -e "    ${AMARILLO}⚠ No se pudo configurar RaiSE MCP automáticamente.${NC}"
fi

# ----------------------
# Instalar paquete Python (coaching + validators)
# ----------------------
echo ""
echo -e "  ${CYAN}Instalando paquete Python...${NC}"

# Detectar pip (python3 -m pip es más portable que pip)
PYTHON_PIP="python3 -m pip"

# Verificar si ya está instalado y actualizar
if $PYTHON_PIP show escala-coaching &>/dev/null; then
    $PYTHON_PIP install -e "$SCRIPT_DIR" --quiet 2>&1 | tail -1 || true
    echo -e "    ${VERDE}✓${NC} Paquete Python actualizado: escala-coaching"
else
    $PYTHON_PIP install -e "$SCRIPT_DIR" --quiet 2>&1 | tail -1 || {
        echo -e "    ${AMARILLO}⚠ No se pudo instalar el paquete Python.${NC}"
        echo "      Puedes instalarlo manualmente con:"
        echo "      cd $SCRIPT_DIR && pip install -e ."
    }
    echo -e "    ${VERDE}✓${NC} Paquete Python instalado: escala-coaching"
fi

# Verificar que los módulos importan
python3 -c "
from coaching.diagnose import run as d
from coaching.level import run as l
from coaching.progress import run as p
from coaching.welcome import run as w
from coaching.worksheet import run as ws
from validators.tasks import find_overdue
from validators.session import validate_session_log
" 2>/dev/null && echo -e "    ${VERDE}✓${NC} Todos los módulos Python funcionan" || echo -e "    ${AMARILLO}⚠ Error en algún módulo Python${NC}"

# ----------------------
# Guardar ruta del repo
# ----------------------
CONFIG_DIR="$HOME/.config/agente-de-escalamiento"
mkdir -p "$CONFIG_DIR"
echo "$SCRIPT_DIR" > "$CONFIG_DIR/repo-path"
echo "v$VERSION" > "$CONFIG_DIR/version"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$CONFIG_DIR/last-update"
echo -e "  ${VERDE}✓${NC} Ruta guardada: ${CONFIG_DIR}/repo-path"
echo -e "  ${VERDE}✓${NC} Versión: v$VERSION"

# ----------------------
# Hacer ejecutables los scripts
# ----------------------
chmod +x "$SCRIPT_DIR/update.sh" "$SCRIPT_DIR/uninstall.sh" 2>/dev/null || true

# ----------------------
# Resumen final
# ----------------------
echo ""
echo -e "${VERDE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${VERDE}║   Instalación completada exitosamente        ║${NC}"
echo -e "${VERDE}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "  Plataformas configuradas: ${PLATAFORMAS[*]}"
echo "  Skill público instalado: escala (las capacidades internas se cargan bajo demanda)"
echo "  Paquete Python: escala-coaching v$VERSION"
echo ""
echo "  Próximo paso: Abre tu agente de IA y cuéntale a ESCALA qué te preocupa hoy."
echo "  No necesitas aprender comandos: ESCALA elegirá el siguiente paso contigo."
echo "  Si ya tienes datos previos, se conservarán (scores, foco e historial)."
echo ""
echo "  Para actualizar más tarde:"
echo "    ./update.sh            (terminal)"
echo ""
echo "  Para verificar instalación: revisa que tu agente detecte ESCALA y háblale en lenguaje natural."
echo ""
echo "  Para desinstalar:"
echo "    ./uninstall.sh       (terminal)"
echo ""
echo -e "  ${AMARILLO}Importante:${NC} Skills instalados como symlinks."
echo "  Cuando hagas git pull, los skills se actualizan automáticamente."
