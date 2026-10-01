#!/bin/sh
# =============================================================
# ESCALA — instalación de un paso para Claude Code.
#
#   curl -fsSL https://raw.githubusercontent.com/lunitomx/agente-de-escalamiento/main/instalar.sh | sh
#
# Sin banderas ni preguntas. Volver a correrlo actualiza.
# Prepara lo que falte (uv y su Python, Claude Code), deja la copia de ESCALA
# en ~/ESCALA (o usa la copia desde la que corre este archivo) y la conecta con
# Claude junto con sus especialistas internos.
# Nunca borra archivos ni descarta cambios: sólo clona o hace pull --ff-only.
# =============================================================
set -u

REPO_URL="${ESCALA_REPO_URL:-https://github.com/lunitomx/agente-de-escalamiento.git}"
REPO_NAME="agente-de-escalamiento"
UV_INSTALLER_URL="https://astral.sh/uv/install.sh"
CLAUDE_INSTALLER_URL="https://claude.ai/install.sh"
PYTHON_VERSION="3.12"
CONFIG_DIR="$HOME/.config/agente-de-escalamiento"
LOG="$CONFIG_DIR/instalacion.log"

# Los instaladores oficiales de uv y de Claude Code dejan su programa aquí.
PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PATH

say() {
    printf '%s\n' "$@"
}

# Cada argumento es una línea: qué pasó y qué hacer. Nunca una traza.
fail() {
    printf '\n' >&2
    printf '%s\n' "$@" >&2
    printf '%s\n' "Si vuelve a pasar, manda una foto de esta ventana a quien te invitó a ESCALA." >&2
    if [ -f "$LOG" ]; then
        printf '%s\n' "Detalles para el equipo: $LOG" >&2
    fi
    exit 1
}

# Lo técnico va al registro; en pantalla sólo español llano.
quiet() {
    "$@" >>"$LOG" 2>&1
}

has() {
    command -v "$1" >/dev/null 2>&1
}

# ---------------------------------------------------------------- sistema
OS_NAME="$(uname -s 2>/dev/null || echo desconocido)"
case "$OS_NAME" in
    Darwin|Linux) ;;
    MINGW*|MSYS*|CYGWIN*|Windows*)
        printf '%s\n' \
            "ESCALA todavía no se instala directo en Windows." \
            "Instala WSL2 (el Linux de Windows), ábrelo y pega ahí el mismo comando." >&2
        exit 1
        ;;
    *)
        printf '%s\n' "ESCALA sólo se instala en Mac o Linux por ahora." >&2
        exit 1
        ;;
esac

mkdir -p "$CONFIG_DIR" || fail "No pude preparar la carpeta de ESCALA en tu usuario." \
    "Revisa que tu disco tenga espacio y vuelve a pegar el mismo comando."
printf '\n=== %s ===\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$LOG"

say "Instalando ESCALA. Tarda unos minutos; no cierres esta ventana."

# ---------------------------------------------------------------- git
# En una Mac nueva, /usr/bin/git sólo abre la ventana de Apple: no sirve
# hasta que se instalan sus herramientas básicas.
if [ "$OS_NAME" = Darwin ] && ! xcode-select -p >/dev/null 2>&1; then
    case "$(command -v git 2>/dev/null)" in
        ""|/usr/bin/git)
            xcode-select --install >/dev/null 2>&1
            fail "Tu Mac necesita sus herramientas básicas antes de instalar ESCALA." \
                "Se abrió una ventana de Apple: elige «Instalar», espera a que termine y vuelve a pegar el mismo comando."
            ;;
    esac
fi
if ! has git; then
    fail "Falta Git en esta computadora." \
        "Pide a quien te ayuda con tu computadora que lo instale (en Ubuntu: sudo apt install git) y vuelve a pegar el mismo comando."
fi

# ---------------------------------------------------------------- uv y Python
download_and_run() {
    # $1 = dirección del instalador oficial, $2 = intérprete (sh o bash)
    if ! has curl; then
        fail "Falta curl, el programa que descarga los instaladores." \
            "Pide a quien te ayuda con tu computadora que lo instale y vuelve a pegar el mismo comando."
    fi
    curl -fsSL "$1" 2>>"$LOG" | "$2" >>"$LOG" 2>&1
}

if ! has uv; then
    say "→ Preparando Python para ESCALA…"
    download_and_run "$UV_INSTALLER_URL" sh
    has uv || fail "No pude preparar Python para ESCALA." \
        "Revisa tu internet y vuelve a pegar el mismo comando."
fi
quiet uv python install "$PYTHON_VERSION" || fail "No pude preparar Python para ESCALA." \
    "Revisa tu internet y vuelve a pegar el mismo comando."
UV_PYTHON="$PYTHON_VERSION"
export UV_PYTHON

# ---------------------------------------------------------------- Claude Code
if ! has claude; then
    say "→ Instalando Claude Code…"
    download_and_run "$CLAUDE_INSTALLER_URL" bash
    has claude || fail "No pude instalar Claude Code." \
        "Revisa tu internet y vuelve a pegar el mismo comando."
fi

# ---------------------------------------------------------------- copia de ESCALA
is_escala_copy() {
    [ -f "$1/install.sh" ] && [ -d "$1/escala-skills" ] && [ -e "$1/.git" ]
}

update_copy() {
    say "→ Buscando la versión más nueva de ESCALA…"
    if ! quiet git -C "$1" pull --ff-only --quiet; then
        say "  No pude traer la versión más nueva. Sigo con la que ya tienes; tu información no se tocó."
    fi
}

ESCALA_DIR=""
case "$0" in
    */instalar.sh|instalar.sh)
        here="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
        if [ -n "$here" ] && is_escala_copy "$here"; then
            ESCALA_DIR="$here"
        fi
        ;;
esac

if [ -n "$ESCALA_DIR" ]; then
    update_copy "$ESCALA_DIR"
else
    ESCALA_DIR="$HOME/ESCALA"
    if [ -e "$ESCALA_DIR" ]; then
        origin="$(git -C "$ESCALA_DIR" remote get-url origin 2>/dev/null || true)"
        case "$origin" in
            *"$REPO_NAME"*) update_copy "$ESCALA_DIR" ;;
            *)
                fail "Ya hay una carpeta ESCALA en tu computadora que no es de este instalador: $ESCALA_DIR. No la toqué." \
                    "Cámbiale el nombre (por ejemplo, ESCALA-anterior) y vuelve a pegar el mismo comando."
                ;;
        esac
    else
        say "→ Descargando ESCALA…"
        quiet git clone --quiet "$REPO_URL" "$ESCALA_DIR" || fail "No pude descargar ESCALA." \
            "Revisa tu internet y vuelve a pegar el mismo comando."
    fi
fi

# ---------------------------------------------------------------- conectar con Claude
say "→ Conectando ESCALA con Claude…"
if ! (cd "$ESCALA_DIR" && bash ./install.sh --platform claude --with-specialists) >>"$LOG" 2>&1; then
    fail "No pude terminar de conectar ESCALA con Claude. No se borró nada." \
        "Intenta otra vez: vuelve a pegar el mismo comando."
fi

# Texto para pegar, no una ruta que se expanda aquí.
# shellcheck disable=SC2088
case "$ESCALA_DIR" in
    "$HOME/ESCALA") shown="~/ESCALA" ;;
    *) shown="\"$ESCALA_DIR\"" ;;
esac
say "" "Listo. Pega esta línea, presiona Enter y cuéntale a ESCALA lo que más te preocupa de tu negocio:  cd $shown && claude"
