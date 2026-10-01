#!/bin/bash
# ESCALA — Agente de Escalamiento
# Instalación: curl -s https://escala.sh | bash
# Repo: github.com/lunitomx/agente-de-escalamiento
# Créditos: Eduardo Muñoz Luna · Verne Harnish

set -e

# ── Colors ──────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BOLD}${BLUE}  ███████  ██████   █████  ██      █████      ███████ ████████ ██  ██████  ███    ██${NC}"
echo -e "${BOLD}${BLUE}  ██      ██      ██   ██ ██      ██   ██     ██         ██    ██ ██       ████   ██${NC}"
echo -e "${BOLD}${BLUE}  █████   ██      ███████ ██      ███████     █████      ██    ██ ██   ███ ██ ██  ██${NC}"
echo -e "${BOLD}${BLUE}  ██      ██      ██   ██ ██      ██   ██     ██         ██    ██ ██    ██ ██  ██ ██${NC}"
echo -e "${BOLD}${BLUE}  ███████  ██████ ██   ██ ███████ ██   ██     ███████    ██    ██  ██████  ██   ████${NC}"
echo ""
echo -e "${BOLD}Agente de Escalamiento — Metodología Scaling Up${NC}"
echo -e "${YELLOW}Verne Harnish · Alan Miltz${NC}"
echo ""

# ── Config ──────────────────────────────────────────────────────────
ESCALA_DIR="$HOME/.escala"

# ── Detect source ──────────────────────────────────────────────────
SCRIPT_SRC="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
if [ ! -f "$SCRIPT_SRC/AGENTS.md" ]; then
  echo -e "  ${YELLOW}⚠️${NC} No se encuentra AGENTS.md en este directorio."
  echo -e "  Asegúrate de estar en el repositorio clonado:"
  echo -e "  git clone https://github.com/lunitomx/agente-de-escalamiento.git"
  exit 1
fi
SRC="$SCRIPT_SRC"
echo -e "  ${GREEN}📦${NC} Instalando desde repositorio local"

# ── Install ──────────────────────────────────────────────────────────

# 1. Create ~/.escala/
mkdir -p "$ESCALA_DIR"/memoria/{dailys,analisis,dashboard,evolucion,evolucion/backups}
mkdir -p "$ESCALA_DIR"/mcp
echo -e "  ${GREEN}✅${NC} ~/.escala/ creado"

# 2. Copy AGENTS.md
cp "$SRC/AGENTS.md" "$ESCALA_DIR/AGENTS.md"
echo -e "  ${GREEN}✅${NC} Identidad instalada"

# 3. Copy skills
if [ -d "$SRC/skills" ] && [ "$(ls -A "$SRC/skills" 2>/dev/null)" ]; then
  mkdir -p "$ESCALA_DIR/skills"
  cp -r "$SRC/skills/"* "$ESCALA_DIR/skills/" 2>/dev/null || true
  echo -e "  ${GREEN}✅${NC} Skills copiadas a ~/.escala/skills/"
fi

# 4. Copy MCP server
if [ -f "$SRC/mcp/server.py" ]; then
  cp "$SRC/mcp/server.py" "$ESCALA_DIR/mcp/server.py"
  echo -e "  ${GREEN}✅${NC} MCP server copiado"
fi

# 5. Link to Claude Code
CLAUDE_DIR="$HOME/.claude/skills"
if [ -d "$CLAUDE_DIR" ] && [ -d "$ESCALA_DIR/skills" ]; then
  for skill in "$ESCALA_DIR/skills/"*/; do
    [ -d "$skill" ] || continue
    name=$(basename "$skill")
    ln -sf "$skill" "$CLAUDE_DIR/$name" 2>/dev/null || cp -r "$skill" "$CLAUDE_DIR/$name"
  done
  echo -e "  ${GREEN}✅${NC} Skills vinculadas en ~/.claude/skills/"
fi

# 6. Link to Hermes
HERMES_DIR="$HOME/.hermes/skills"
if [ -d "$HERMES_DIR" ] && [ -d "$ESCALA_DIR/skills" ]; then
  for skill in "$ESCALA_DIR/skills/"*/; do
    [ -d "$skill" ] || continue
    name=$(basename "$skill")
    ln -sf "$skill" "$HERMES_DIR/$name" 2>/dev/null || cp -r "$skill" "$HERMES_DIR/$name"
  done
  echo -e "  ${GREEN}✅${NC} Skills vinculadas en ~/.hermes/skills/"
fi

# 7. Create memory index
if [ ! -f "$ESCALA_DIR/memoria/indice.md" ]; then
  cat > "$ESCALA_DIR/memoria/indice.md" << 'EOF'
# Índice de Memoria — ESCALA

_Actualizado automáticamente._

## Dailys
| Fecha | Empresa | Score | Archivo |
|-------|---------|:-----:|---------|

## Análisis
| Fecha | Tipo | Empresa | Archivo |
|-------|------|---------|---------|

## Dashboards
| Fecha | Título | Archivo |
|-------|--------|---------|
EOF
  echo -e "  ${GREEN}✅${NC} Índice de memoria creado"
fi


# ── Done ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}🎯 ESCALA instalado correctamente.${NC}"
echo ""
echo -e "  ${BOLD}📂${NC} Instalado en:  ${BLUE}~/.escala/${NC}"
echo -e "  ${BOLD}📝${NC} Identidad:     ${BLUE}~/.escala/AGENTS.md${NC}"
echo -e "  ${BOLD}🧠${NC} Memoria:       ${BLUE}~/.escala/memoria/${NC}"
echo -e "  ${BOLD}🔧${NC} Skills:        ${BLUE}~/.escala/skills/${NC}"
echo ""
echo -e "${BOLD}${YELLOW}📖 Próximo paso:${NC}"
echo -e "  Abre Claude/Codex/Hermes y dile:"
echo -e "  ${BLUE}\"Quiero escalar mi negocio\"${NC}"
echo ""
echo -e "${BOLD}${YELLOW}📖 O prueba los skills directamente:${NC}"
echo -e "  ${BLUE}\"Analiza mi daily huddle\"${NC}"
echo -e "  ${BLUE}\"Hagamos el Power of One\"${NC}"
echo -e "  ${BLUE}\"Revisemos mi FACe\"${NC}"
echo ""
