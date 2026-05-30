#!/bin/bash
# ESCALA — Agente de Escalamiento
# Instalación: curl -s https://escala.sh | bash
# Créditos: Eduardo Muñoz Luna · Verne Harnish · Humberto Martínez Barón

set -e

KOKORO_DIR="$HOME/.kokoro"
ESCALA_SRC="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Instalando ESCALA — Agente de Escalamiento"
echo ""

# 1. Crear ~/.kokoro/
mkdir -p "$KOKORO_DIR"/memoria/{dailys,analisis,dashboard}
mkdir -p "$KOKORO_DIR"/mcp
echo "  ✅ ~/.kokoro/ creado"

# 2. Copiar AGENTS.md
cp "$ESCALA_SRC/AGENTS.md" "$KOKORO_DIR/AGENTS.md"
echo "  ✅ Identidad instalada"

# 3. Copiar skills
if [ -d "$ESCALA_SRC/skills" ]; then
  mkdir -p "$KOKORO_DIR/skills"
  cp -r "$ESCALA_SRC/skills/"* "$KOKORO_DIR/skills/" 2>/dev/null || true
  echo "  ✅ Skills copiadas a ~/.kokoro/skills/"
fi

# 4. Instalar en Claude Code
CLAUDE_SKILLS="$HOME/.claude/skills"
if [ -d "$CLAUDE_SKILLS" ]; then
  for skill in "$KOKORO_DIR/skills/"*/; do
    name=$(basename "$skill")
    ln -sf "$skill" "$CLAUDE_SKILLS/$name" 2>/dev/null || cp -r "$skill" "$CLAUDE_SKILLS/$name"
  done
  echo "  ✅ Skills vinculadas en ~/.claude/skills/"
fi

# 5. Instalar en Hermes
HERMES_SKILLS="$HOME/.hermes/skills"
if [ -d "$HERMES_SKILLS" ]; then
  for skill in "$KOKORO_DIR/skills/"*/; do
    name=$(basename "$skill")
    ln -sf "$skill" "$HERMES_SKILLS/$name" 2>/dev/null || cp -r "$skill" "$HERMES_SKILLS/$name"
  done
  echo "  ✅ Skills vinculadas en ~/.hermes/skills/"
fi

# 6. Crear índice de memoria inicial
if [ ! -f "$KOKORO_DIR/memoria/indice.md" ]; then
  cat > "$KOKORO_DIR/memoria/indice.md" << 'EOF'
# Índice de Memoria — ESCALA

_Actualizado automáticamente. Cada nuevo análisis se registra aquí._

## Dailys
| Fecha | Empresa | Score | Archivo |
|-------|---------|:-----:|---------|

## Análisis
| Fecha | Tipo | Empresa | Archivo |
|-------|------|---------|---------|

## Dashboards Generados
| Fecha | Título | Archivo |
|-------|--------|---------|
EOF
  echo "  ✅ Índice de memoria creado"
fi

# 7. MCP server
if [ -f "$ESCALA_SRC/mcp/server.py" ]; then
  cp "$ESCALA_SRC/mcp/server.py" "$KOKORO_DIR/mcp/server.py"
  echo "  ✅ MCP server copiado"
fi

echo ""
echo "🎯 ESCALA instalado correctamente."
echo "   Ya puedes hablar con cualquier LLM sobre escalar tu negocio."
echo "   Los skills están disponibles en ~/.kokoro/skills/"
echo ""
echo "📖 Próximo paso: abre Claude/Codex/Hermes y dile:"
echo "   'Quiero escalar mi negocio'"
