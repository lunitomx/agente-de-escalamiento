#!/usr/bin/env bash
# =============================================================
# Actualizador del Agente de Escalamiento
# Lee la ruta guardada por install.sh, hace git pull y reinstala
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/agente-de-escalamiento"
REPO_PATH_FILE="$CONFIG_DIR/repo-path"

# Colores
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
CYAN='\033[0;36m'
ROJO='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║   Agente de Escalamiento — Actualizador     ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# --- Determinar ruta del repo ---
if [ -f "$REPO_PATH_FILE" ]; then
    REPO_PATH=$(cat "$REPO_PATH_FILE")
elif [ -d "$SCRIPT_DIR/.git" ]; then
    # Fallback: estamos parados en el repo
    REPO_PATH="$SCRIPT_DIR"
else
    echo -e "${ROJO}✗ No se encontró la ruta del repositorio.${NC}"
    echo ""
    echo "  Esto puede pasar si:"
    echo "    1. Nunca ejecutaste install.sh"
    echo "    2. Borraste la carpeta del repo"
    echo ""
    echo "  Solución:"
    echo "    git clone https://github.com/lunitomx/agente-de-escalamiento.git"
    echo "    cd agente-de-escalamiento && ./install.sh"
    echo ""
    echo "  Luego vuelve a ejecutar ./update.sh"
    exit 1
fi

echo -e "  ${CYAN}Repositorio:${NC} $REPO_PATH"

# --- Verificar que es un git repo ---
if [ ! -d "$REPO_PATH/.git" ]; then
    echo -e "${ROJO}✗ La ruta guardada no es un repositorio git.${NC}"
    echo "  Elimina $REPO_PATH_FILE y ejecuta install.sh de nuevo."
    exit 1
fi

cd "$REPO_PATH"

# --- Guardar hash actual ---
BEFORE=$(git rev-parse HEAD)

echo ""
echo -e "  ${CYAN}Buscando actualizaciones...${NC}"

# --- Git pull (intenta main, luego master) ---
if PULL_OUTPUT=$(git pull origin main 2>&1); then
    : # OK
elif PULL_OUTPUT=$(git pull origin master 2>&1); then
    : # OK
else
    echo -e "${ROJO}✗ Error al actualizar:${NC}"
    echo "  $PULL_OUTPUT"
    echo ""
    echo "  Posibles causas:"
    echo "    - Sin conexión a internet"
    echo "    - El repo fue movido o borrado en GitHub"
    echo "    - Permisos insuficientes"
    echo ""
    echo "  Solución: clona de nuevo y ejecuta install.sh"
    exit 1
fi

AFTER=$(git rev-parse HEAD)

echo ""

# --- Mostrar cambios ---
if [ "$BEFORE" = "$AFTER" ]; then
    echo -e "${VERDE}✓${NC} Ya tienes la versión más reciente."
else
    echo -e "${VERDE}✓${NC} Actualización recibida:"
    echo ""
    git log --oneline "$BEFORE..$AFTER" 2>/dev/null | while IFS= read -r line; do
        echo "    $line"
    done
    echo ""
fi

# --- Reinstalar skills ---
echo -e "  ${CYAN}Reinstalando skills...${NC}"
bash install.sh

# --- Guardar timestamp ---
mkdir -p "$CONFIG_DIR"
date -u +%Y-%m-%dT%H:%M:%SZ > "$CONFIG_DIR/last-update"

echo ""
echo -e "${VERDE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${VERDE}║   Actualización completada exitosamente     ║${NC}"
echo -e "${VERDE}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "  Última actualización: $(cat $CONFIG_DIR/last-update)"
echo ""
echo -e "  ${AMARILLO}Nota:${NC} Desde tu terminal de IA también puedes usar:"
echo "    /escala-update"
