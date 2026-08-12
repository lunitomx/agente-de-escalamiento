#!/usr/bin/env bash
# =============================================================
# Desinstalador del Agente de Escalamiento
# =============================================================
set -euo pipefail

CONFIG_DIR="$HOME/.config/agente-de-escalamiento"
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
CYAN='\033[0;36m'
ROJO='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║   Agente de Escalamiento — Desinstalador    ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# --- Resumen de lo que se va a borrar ---
echo ""
echo "  Se eliminará:"

PLATFORMAS=()
if [ -d "$HOME/.claude/skills" ]; then
    COUNT=$(ls -d "$HOME/.claude/skills"/escala-* 2>/dev/null | wc -l | tr -d ' ')
    [ "$COUNT" -gt 0 ] && PLATFORMAS+=("Claude Code: $COUNT skills en ~/.claude/skills/")
fi
if [ -d "$HOME/.hermes/skills" ]; then
    COUNT=$(ls -d "$HOME/.hermes/skills"/escala-* 2>/dev/null | wc -l | tr -d ' ')
    [ "$COUNT" -gt 0 ] && PLATFORMAS+=("Hermes Agent: $COUNT skills en ~/.hermes/skills/")
fi
if [ -d "$HOME/.codex/skills" ]; then
    COUNT=$(ls -d "$HOME/.codex/skills"/escala-* 2>/dev/null | wc -l | tr -d ' ')
    [ "$COUNT" -gt 0 ] && PLATFORMAS+=("Codex CLI: $COUNT skills en ~/.codex/skills/")
fi

if [ ${#PLATFORMAS[@]} -eq 0 ]; then
    echo "    (no se encontraron skills instalados)"
else
    for p in "${PLATFORMAS[@]}"; do
        echo "    - $p"
    done
fi

# Paquete Python
if pip show escala-coaching &>/dev/null; then
    echo "    - Paquete Python: escala-coaching"
fi

# Config
if [ -d "$CONFIG_DIR" ]; then
    echo "    - Configuración: $CONFIG_DIR"
fi

echo ""
echo -e "${AMARILLO}¿Estás seguro de eliminar todo? (s/N)${NC}"
read -r CONFIRMACION
if [ "$CONFIRMACION" != "s" ] && [ "$CONFIRMACION" != "S" ]; then
    echo "  Desinstalación cancelada."
    exit 0
fi

# --- Eliminar skills ---
echo ""
echo -e "  ${CYAN}Eliminando skills...${NC}"
for dir in "$HOME/.claude/skills" "$HOME/.hermes/skills" "$HOME/.codex/skills"; do
    if [ -d "$dir" ]; then
        COUNT=0
        for skill in "$dir"/escala-*; do
            if [ -e "$skill" ]; then
                rm -rf "$skill"
                COUNT=$((COUNT + 1))
            fi
        done
        [ "$COUNT" -gt 0 ] && echo -e "    ${VERDE}✓${NC} $COUNT skills eliminados de $dir"
    fi
done

# --- Desinstalar paquete Python ---
echo ""
echo -e "  ${CYAN}Desinstalando paquete Python...${NC}"
if pip show escala-coaching &>/dev/null; then
    pip uninstall escala-coaching -y 2>&1 | tail -1
    echo -e "    ${VERDE}✓${NC} Paquete escala-coaching desinstalado"
else
    echo "    (no instalado)"
fi

# --- Eliminar config ---
echo ""
echo -e "  ${CYAN}Eliminando configuración...${NC}"
if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    echo -e "    ${VERDE}✓${NC} Configuración eliminada"
fi

echo ""
echo -e "${VERDE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${VERDE}║   Desinstalación completada                  ║${NC}"
echo -e "${VERDE}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "  Si quieres volver a instalar en el futuro:"
echo "    git clone https://github.com/lunitomx/agente-de-escalamiento.git"
echo "    cd agente-de-escalamiento && ./install.sh"
