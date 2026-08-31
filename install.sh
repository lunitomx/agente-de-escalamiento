#!/usr/bin/env bash
# =============================================================
# Instalador del Agente de Escalamiento
# Instala sólo las plataformas elegidas explícitamente.
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_NAME="agente-de-escalamiento"
VERSION="1.1.0"

SKILLS_ONLY=false
ALL_PLATFORMS=false
WITH_RAISE_MCP=false
REQUESTED_PLATFORMS=()

usage() {
    cat >&2 <<'USAGE'
Uso: ./install.sh (--platform claude|codex|hermes [--platform ...] | --all-platforms) [--skills-only] [--with-rai-mcp]

Opciones:
  --platform NOMBRE  Instala sólo en Claude Code, Codex CLI o Hermes Agent.
                      Se puede repetir para elegir varias plataformas.
  --all-platforms    Instala en todas las plataformas detectadas.
  --skills-only      Instala únicamente la puerta conversacional ESCALA.
  --with-rai-mcp     Configura el MCP local de RaiSE para Codex (requiere
                      --platform codex o --all-platforms; nunca es implícito).
  --help             Muestra esta ayuda.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --platform)
            if [[ $# -lt 2 ]]; then
                echo "Falta el nombre después de --platform." >&2
                usage
                exit 2
            fi
            case "$2" in
                claude|codex|hermes) REQUESTED_PLATFORMS+=("$2") ;;
                *)
                    echo "Plataforma no válida: $2" >&2
                    usage
                    exit 2
                    ;;
            esac
            shift 2
            ;;
        --all-platforms)
            ALL_PLATFORMS=true
            shift
            ;;
        --skills-only)
            SKILLS_ONLY=true
            shift
            ;;
        --with-rai-mcp)
            WITH_RAISE_MCP=true
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Argumento desconocido: $1" >&2
            usage
            exit 2
            ;;
    esac
done

if [[ "$ALL_PLATFORMS" == true && ${#REQUESTED_PLATFORMS[@]} -gt 0 ]]; then
    echo "Usa --all-platforms o --platform, no ambos." >&2
    usage
    exit 2
fi

if [[ "$ALL_PLATFORMS" == false && ${#REQUESTED_PLATFORMS[@]} -eq 0 ]]; then
    echo "Elige una plataforma con --platform o usa --all-platforms." >&2
    usage
    exit 2
fi

if [[ "$SKILLS_ONLY" == true && "$WITH_RAISE_MCP" == true ]]; then
    echo "--with-rai-mcp requiere una instalación completa; quita --skills-only." >&2
    exit 2
fi

echo -e '\033[0;36m'
echo '╔══════════════════════════════════════════════╗'
echo "║   Agente de Escalamiento — Instalador v${VERSION}  ║"
echo '╚══════════════════════════════════════════════╝'
echo -e '\033[0m'

VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ----------------------
# Verifica artefacto portable antes de activar enlaces
# ----------------------
PORTABLE_BUNDLE=false
if [[ -f "$SCRIPT_DIR/ESCALA-MANIFEST.json" ]]; then
    PORTABLE_BUNDLE=true
    if ! python3 "$SCRIPT_DIR/scripts/verify_portable_bundle.py"; then
        echo -e "${AMARILLO}⚠ El paquete portable no pasó su verificación y no se instaló.${NC}" >&2
        exit 1
    fi
elif [[ ! -e "$SCRIPT_DIR/.git" ]]; then
    echo -e "${AMARILLO}⚠ Falta el manifiesto del paquete portable; no se instalarán skills.${NC}" >&2
    exit 1
fi

# ----------------------
# Detecta y valida destinos solicitados
# ----------------------
AVAILABLE_PLATFORMS=()
if command -v claude &>/dev/null; then
    AVAILABLE_PLATFORMS+=("claude")
    echo -e "  ${VERDE}✓${NC} Claude Code detectado"
fi
if command -v hermes &>/dev/null; then
    AVAILABLE_PLATFORMS+=("hermes")
    echo -e "  ${VERDE}✓${NC} Hermes Agent detectado"
fi
if command -v codex &>/dev/null; then
    AVAILABLE_PLATFORMS+=("codex")
    echo -e "  ${VERDE}✓${NC} Codex CLI detectado"
fi

if [[ ${#AVAILABLE_PLATFORMS[@]} -eq 0 ]]; then
    echo -e "${AMARILLO}⚠ No se detectó ninguna plataforma compatible.${NC}" >&2
    echo "  Instala Claude Code, Hermes Agent o Codex CLI primero." >&2
    exit 1
fi

contains_platform() {
    local needle="$1"
    local item
    for item in "${AVAILABLE_PLATFORMS[@]}"; do
        [[ "$item" == "$needle" ]] && return 0
    done
    return 1
}

append_target_once() {
    local candidate="$1"
    local item
    for item in "${TARGET_PLATFORMS[@]:-}"; do
        [[ "$item" == "$candidate" ]] && return 0
    done
    TARGET_PLATFORMS+=("$candidate")
}

TARGET_PLATFORMS=()
if [[ "$ALL_PLATFORMS" == true ]]; then
    TARGET_PLATFORMS=("${AVAILABLE_PLATFORMS[@]}")
else
    for platform in "${REQUESTED_PLATFORMS[@]}"; do
        if ! contains_platform "$platform"; then
            echo "La plataforma solicitada no está instalada: $platform" >&2
            exit 1
        fi
        append_target_once "$platform"
    done
fi

if [[ "$WITH_RAISE_MCP" == true ]]; then
    codex_selected=false
    for platform in "${TARGET_PLATFORMS[@]}"; do
        [[ "$platform" == "codex" ]] && codex_selected=true
    done
    if [[ "$codex_selected" == false ]]; then
        echo "--with-rai-mcp requiere seleccionar Codex con --platform codex o --all-platforms." >&2
        exit 2
    fi
fi

# ----------------------
# Runtime Python local (nunca pip global)
# ----------------------
PYTHON_RUNTIME=""
install_python_runtime() {
    local venv_python="$SCRIPT_DIR/.venv/bin/python"

    if ! command -v uv &>/dev/null; then
        echo -e "${AMARILLO}⚠ No se encontró uv; no se instaló el runtime Python.${NC}" >&2
        echo "  Instala uv o ejecuta ./install.sh --platform <plataforma> --skills-only." >&2
        return 1
    fi

    if [[ ! -x "$venv_python" ]]; then
        echo -e "  ${CYAN}Creando entorno Python local...${NC}"
        if ! uv venv "$SCRIPT_DIR/.venv"; then
            echo -e "${AMARILLO}⚠ No se pudo crear el entorno local .venv.${NC}" >&2
            return 1
        fi
    fi

    echo -e "  ${CYAN}Instalando paquete Python en .venv...${NC}"
    if ! uv pip install --python "$venv_python" -e "$SCRIPT_DIR" --quiet; then
        echo -e "${AMARILLO}⚠ No se pudo instalar escala-coaching en .venv.${NC}" >&2
        return 1
    fi

    if ! "$venv_python" -c '
from coaching.diagnose import run as d
from coaching.level import run as l
from coaching.progress import run as p
from coaching.welcome import run as w
from coaching.worksheet import run as ws
from validators.tasks import find_overdue
from validators.session import validate_session_log
'; then
        echo -e "${AMARILLO}⚠ El runtime Python instalado no pudo importar todos los módulos.${NC}" >&2
        return 1
    fi

    PYTHON_RUNTIME="$venv_python"
    echo -e "    ${VERDE}✓${NC} Paquete Python instalado: escala-coaching ($PYTHON_RUNTIME)"
}

# Instalar el runtime antes de tocar los destinos del usuario: un fallo no deja
# enlaces nuevos ni configura MCPs de forma parcial.
if [[ "$SKILLS_ONLY" == false ]]; then
    if ! install_python_runtime; then
        echo -e "${AMARILLO}Instalación incompleta: no se modificaron las plataformas seleccionadas.${NC}" >&2
        exit 1
    fi
fi

# ----------------------
# Instalación de la puerta pública (symlinks)
# ----------------------
install_on() {
    local platform="$1"
    local destination="$2"
    local skill_dir="$SCRIPT_DIR/escala-skills/escala"

    echo ""
    echo -e "  → Instalando en ${CYAN}${platform}${NC}..."
    if [[ ! -f "$skill_dir/SKILL.md" ]]; then
        echo "Skill público ESCALA no encontrado: $skill_dir" >&2
        return 1
    fi

    mkdir -p "$destination"
    local link
    for link in "$destination"/escala-*; do
        if [[ -L "$link" ]]; then
            rm "$link"
        fi
    done

    ln -sfn "$skill_dir" "$destination/escala"
    echo -e "    ${VERDE}✓${NC} 1 skill instalado (symlink) en ${destination}"
}

marker_count() {
    local file="$1"
    local marker="$2"
    if [[ ! -f "$file" ]]; then
        printf "0\n"
        return 0
    fi
    grep -Fxc -- "$marker" "$file" || true
}

validate_claude_block() {
    local file="$1"
    local begin="$2"
    local end="$3"
    local line
    local state="outside"
    local begin_count=0

    [[ ! -f "$file" ]] && return 0
    while IFS= read -r line || [[ -n "$line" ]]; do
        case "$line" in
            "$begin")
                if [[ "$state" != "outside" || "$begin_count" != "0" ]]; then
                    return 1
                fi
                state="inside"
                begin_count=1
                ;;
            "$end")
                if [[ "$state" != "inside" ]]; then
                    return 1
                fi
                state="outside"
                ;;
            *"ESCALA:BEGIN"*|*"ESCALA:END"*)
                return 1
                ;;
        esac
    done < "$file"
    [[ "$state" == "outside" ]]
}
render_claude_block() {
    local skill_dir="$1"
    local catalog_path="$2"
    local template="$SCRIPT_DIR/adapters/claude/CLAUDE.template.md"
    local line
    if [[ ! -f "$template" ]]; then
        echo "No está disponible el contrato Claude de ESCALA." >&2
        return 1
    fi
    while IFS= read -r line || [[ -n "$line" ]]; do
        case "$line" in
            *"{{ESCALA_SKILL_PATH}}"*)
                printf "El skill público de ESCALA está en %s/SKILL.md.\n" "$skill_dir"
                ;;
            *"{{ESCALA_CAPABILITY_CATALOG}}"*)
                printf "El contrato portable de capacidades está en %s.\n" "$catalog_path"
                ;;
            *) printf "%s\n" "$line" ;;
        esac
    done < "$template"
}

prepare_claude_instructions() {
    local claude_root="$1"
    local target="$claude_root/CLAUDE.md"
    local skill_dir="$SCRIPT_DIR/escala-skills/escala"
    local catalog_path="$SCRIPT_DIR/capabilities/mvp/catalog.json"
    local begin="<!-- ESCALA:BEGIN -->"
    local end="<!-- ESCALA:END -->"
    local begin_count
    local prepared
    local line
    local replacing=false

    if [[ ! -f "$skill_dir/SKILL.md" || ! -f "$catalog_path" ]]; then
        echo "Faltan los artefactos portables de ESCALA para Claude." >&2
        return 1
    fi
    mkdir -p "$claude_root"
    if ! validate_claude_block "$target" "$begin" "$end"; then
        echo "El bloque ESCALA existente en CLAUDE.md está incompleto o malformado; no se modificó." >&2
        return 1
    fi
    begin_count="$(marker_count "$target" "$begin")"
    prepared="$(mktemp "$claude_root/.escala-claude.XXXXXX")" || {
        echo "No se pudo preparar el contrato Claude de ESCALA." >&2
        return 1
    }
    if [[ "$begin_count" == "0" ]]; then
        {
            if [[ -f "$target" && -s "$target" ]]; then
                cat "$target"
                printf "\n\n"
            fi
            render_claude_block "$skill_dir" "$catalog_path"
        } > "$prepared" || {
            rm -f "$prepared"
            return 1
        }
    else
        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ "$line" == "$begin" ]]; then
                render_claude_block "$skill_dir" "$catalog_path"
                replacing=true
                continue
            fi
            if [[ "$line" == "$end" && "$replacing" == true ]]; then
                replacing=false
                continue
            fi
            if [[ "$replacing" == false ]]; then
                printf "%s\n" "$line"
            fi
        done < "$target" > "$prepared" || {
            rm -f "$prepared"
            return 1
        }
    fi
    printf "%s\n" "$prepared"
}

install_claude() {
    local claude_root="$HOME/.claude"
    local prepared
    if ! prepared="$(prepare_claude_instructions "$claude_root")"; then
        return 1
    fi
    if ! install_on "Claude Code" "$claude_root/skills"; then
        rm -f "$prepared"
        return 1
    fi
    if ! mv -f -- "$prepared" "$claude_root/CLAUDE.md"; then
        rm -f "$prepared"
        echo "No se pudo activar el contrato Claude de ESCALA." >&2
        return 1
    fi
    echo -e "    ${VERDE}✓${NC} Contrato ESCALA actualizado en ${claude_root}/CLAUDE.md"
}
for platform in "${TARGET_PLATFORMS[@]}"; do
    case "$platform" in
        claude) install_claude ;;
        hermes) install_on "Hermes Agent" "$HOME/.hermes/skills" ;;
        codex) install_on "Codex CLI" "$HOME/.codex/skills" ;;
    esac
done

if [[ "$SKILLS_ONLY" == true ]]; then
    echo "  Instalación de skill completada: habla con ESCALA en lenguaje natural."
    exit 0
fi

# RaiSE MCP is an explicit Codex opt-in. It is not part of the public skill
# package and never runs merely because Codex happens to be installed.
if [[ "$WITH_RAISE_MCP" == true ]]; then
    configurator="$SCRIPT_DIR/scripts/configure_codex_mcp.sh"
    if [[ ! -x "$configurator" ]]; then
        echo "No está disponible el configurador MCP de RaiSE en este paquete." >&2
        exit 1
    fi
    echo ""
    echo -e "  ${CYAN}Configurando RaiSE MCP para Codex...${NC}"
    if ! "$configurator" "$SCRIPT_DIR"; then
        echo -e "${AMARILLO}⚠ No se pudo configurar RaiSE MCP automáticamente.${NC}" >&2
        exit 1
    fi
fi

# ----------------------
# Guardar instalación completa y resumen
# ----------------------
CONFIG_DIR="$HOME/.config/agente-de-escalamiento"
mkdir -p "$CONFIG_DIR"
printf '%s\n' "$SCRIPT_DIR" > "$CONFIG_DIR/repo-path"
printf 'v%s\n' "$VERSION" > "$CONFIG_DIR/version"
date -u +%Y-%m-%dT%H:%M:%SZ > "$CONFIG_DIR/last-update"
echo -e "  ${VERDE}✓${NC} Ruta guardada: ${CONFIG_DIR}/repo-path"
echo -e "  ${VERDE}✓${NC} Versión: v$VERSION"

chmod +x "$SCRIPT_DIR/update.sh" "$SCRIPT_DIR/uninstall.sh" 2>/dev/null || true

echo ""
echo -e "${VERDE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${VERDE}║   Instalación completada exitosamente        ║${NC}"
echo -e "${VERDE}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "  Plataformas configuradas: ${TARGET_PLATFORMS[*]}"
echo "  Skill público instalado: escala (las capacidades internas se cargan bajo demanda)"
echo "  Runtime Python local: $PYTHON_RUNTIME"
echo ""
echo "  Próximo paso: abre tu agente de IA y cuéntale a ESCALA qué te preocupa hoy."
echo "  No necesitas aprender comandos: ESCALA elegirá el siguiente paso contigo."
echo ""
echo "  Para actualizar más tarde:"
echo "    ./update.sh            (terminal)"
echo ""
echo "  Para desinstalar:"
echo "    ./uninstall.sh       (terminal)"
echo ""
echo -e "  ${AMARILLO}Importante:${NC} Skills instalados como symlinks locales."
if [[ "$PORTABLE_BUNDLE" == true ]]; then
    echo "  Para actualizar, instala un nuevo paquete portable que pase su verificación."
else
    echo "  En modo desarrollo, git pull actualiza la copia local de los skills."
fi
