#!/usr/bin/env bash
# =============================================================
# Instalador del Agente de Escalamiento
# Detecta plataforma(s) disponible(s) y configura los skills
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_NAME="agente-de-escalamiento"
VERSION="1.0.0"

# Colores
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# Codex CLI puede estar como 'codex' o como parte del PATH
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
# Función de instalación
# ----------------------
instalar_en() {
    local plataforma="$1"
    local destino="$2"

    echo ""
    echo -e "  → Instalando en ${CYAN}${plataforma}${NC}..."

    mkdir -p "$destino"

    # Copiar skills
    local count=0
    for skill_dir in "$SCRIPT_DIR/escala-skills"/escala-*/; do
        local skill_name
        skill_name=$(basename "$skill_dir")
        cp -r "$skill_dir" "$destino/$skill_name"
        count=$((count + 1))
    done

    echo -e "    ${VERDE}✓${NC} $count skills instalados en ${destino}"
}

# ----------------------
# Ejecutar instalación
# ----------------------
for p in "${PLATAFORMAS[@]}"; do
    case "$p" in
        claude)
            instalar_en "Claude Code" "$HOME/.claude/skills"
            ;;
        hermes)
            instalar_en "Hermes Agent" "$HOME/.hermes/skills"
            ;;
        codex)
            instalar_en "Codex CLI" "$HOME/.codex/skills"
            ;;
    esac
done

# ----------------------
# Guardar ruta del repo
# ----------------------
CONFIG_DIR="$HOME/.config/agente-de-escalamiento"
mkdir -p "$CONFIG_DIR"
echo "$SCRIPT_DIR" > "$CONFIG_DIR/repo-path"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$CONFIG_DIR/last-update"
echo -e "  ${VERDE}✓${NC} Ruta guardada: ${CONFIG_DIR}/repo-path"

echo ""
echo -e "${VERDE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${VERDE}║   Instalación completada exitosamente        ║${NC}"
echo -e "${VERDE}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "  Plataformas configuradas: ${PLATAFORMAS[*]}"
echo "  Skills instalados: $(ls -d "$SCRIPT_DIR/escala-skills"/escala-* 2>/dev/null | wc -l)"
echo ""
echo "  Próximo paso: Abre tu terminal de IA y ejecuta /escala-welcome"
echo "  para crear tu perfil de empresa."
echo ""
echo "  Para ver todos los comandos disponibles, consulta el README."
echo ""
echo -e "  ${AMARILLO}Nota:${NC} Para actualizar más tarde, ejecuta:"
echo "    ./update.sh          (si tienes el repo)"
echo "    /escala-update       (desde tu terminal de IA)"
