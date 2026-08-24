#!/usr/bin/env bash
set -euo pipefail

# ScaleUp Cross-Platform Installer
# Installs ScaleUp skills, coaching engine, knowledge, and agent config.
#
# Usage:
#   ./install.sh                    # Install to Claude Code global
#   ./install.sh --target hermes    # Install to Hermes Agent
#   ./install.sh --target all       # Install to all platforms
#   ./install.sh --destination-root /tmp/scaleup-e2e
#   ./install.sh --status           # Show installation status
#   ./install.sh --uninstall        # Remove from all platforms

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/VERSION"
VERSION="0.0.0"
[[ -f "$VERSION_FILE" ]] && VERSION="$(cat "$VERSION_FILE")"

# Source directories
SKILLS_DIR="$(dirname "$SCRIPT_DIR")/.claude/skills"
COACHING_DIR="$(dirname "$SCRIPT_DIR")/coaching"
KNOWLEDGE_DIR="$SCRIPT_DIR/knowledge"
AGENT_DIR="$SCRIPT_DIR/agent"

# Target directories (configured after parsing CLI arguments)
CLAUDE_SKILLS=""
CLAUDE_SCALEUP=""
HERMES_SKILLS=""
HERMES_SCALEUP=""

# ── Helpers ──────────────────────────────────────────────────────────────────

info()  { echo "  [+] $*"; }
warn()  { echo "  [!] $*" >&2; }
error() { echo "  [✗] $*" >&2; exit 1; }

configure_targets() {
    local destination_root="$1"
    CLAUDE_SKILLS="$destination_root/.claude/skills"
    CLAUDE_SCALEUP="$destination_root/.claude/scaleup"
    HERMES_SKILLS="$destination_root/.hermes/skills"
    HERMES_SCALEUP="$destination_root/.hermes/scaleup"
}

adapt_skill() {
    local skill_file="$1" runtime_root="$2" escaped_root
    escaped_root="${runtime_root//\\/\\\\}"
    escaped_root="${escaped_root//&/\\&}"
    escaped_root="${escaped_root//|/\\|}"

    sed -i \
        -e "s|sys\\.path\\.insert(0, '\\.')|sys.path.insert(0, '$escaped_root')|g" \
        -e "s|str(pathlib\\.Path('\\.scaleup/agent'))|str(pathlib.Path('$escaped_root/agent'))|g" \
        -e "s|python3 \\.scaleup/agent/validators/|python3 $escaped_root/agent/validators/|g" \
        -e "s|python3 -m coaching\\.|PYTHONPATH='$escaped_root' python3 -m coaching.|g" \
        "$skill_file"
}

copy_skills() {
    local src="$1" dst="$2" runtime_root="$3" count=0
    mkdir -p "$dst"
    for skill_dir in "$src"/scaleup-*/; do
        [[ -d "$skill_dir" ]] || continue
        local name
        name="$(basename "$skill_dir")"
        mkdir -p "$dst/$name"
        cp "$skill_dir/SKILL.md" "$dst/$name/SKILL.md"
        adapt_skill "$dst/$name/SKILL.md" "$runtime_root"
        count=$((count + 1))
    done
    info "Copied $count skills to $dst"
}

copy_engine() {
    local dst="$1"
    # Clean slate: remove old coaching engine to avoid orphaned files (engine.py, formatter.py, summary/)
    rm -rf "$dst/coaching"
    mkdir -p "$dst/coaching"
    # Copy Python modules
    for mod in core dashboard diagnose export level progress pulse router welcome worksheet; do
        if [[ -d "$COACHING_DIR/$mod" ]]; then
            mkdir -p "$dst/coaching/$mod"
            cp "$COACHING_DIR/$mod/"*.py "$dst/coaching/$mod/" 2>/dev/null || true
            # Copy tests too for verification
            if [[ -d "$COACHING_DIR/$mod/tests" ]]; then
                mkdir -p "$dst/coaching/$mod/tests"
                cp "$COACHING_DIR/$mod/tests/"*.py "$dst/coaching/$mod/tests/" 2>/dev/null || true
            fi
        fi
    done
    cp "$COACHING_DIR/__init__.py" "$dst/coaching/" 2>/dev/null || true
    info "Copied coaching engine to $dst/coaching/ (clean install)"
}

copy_knowledge() {
    local dst="$1"
    mkdir -p "$dst/knowledge"
    cp -r "$KNOWLEDGE_DIR/"* "$dst/knowledge/"
    info "Copied knowledge ontology to $dst/knowledge/"
}

copy_agent() {
    local dst="$1"
    mkdir -p "$dst/agent"
    cp -r "$AGENT_DIR/"* "$dst/agent/" 2>/dev/null || true
    info "Copied agent config to $dst/agent/"
}

write_version() {
    local dst="$1"
    echo "$VERSION" > "$dst/VERSION"
    info "Version $VERSION written to $dst/VERSION"
}

# ── Install Functions ────────────────────────────────────────────────────────

install_claude() {
    echo ""
    echo "Installing ScaleUp to Claude Code ($CLAUDE_SCALEUP)..."
    copy_skills "$SKILLS_DIR" "$CLAUDE_SKILLS" "$CLAUDE_SCALEUP"
    copy_engine "$CLAUDE_SCALEUP"
    copy_knowledge "$CLAUDE_SCALEUP"
    copy_agent "$CLAUDE_SCALEUP"
    write_version "$CLAUDE_SCALEUP"

    # Create my-company template if it doesn't exist
    local company_dir="$CLAUDE_SCALEUP/my-company"
    if [[ ! -d "$company_dir" ]]; then
        mkdir -p "$company_dir/worksheets"
        info "Created my-company template at $company_dir"
    else
        info "my-company directory exists — preserved user data"
    fi

    echo "  Claude Code installation complete."
}

install_hermes() {
    echo ""
    echo "Installing ScaleUp to Hermes Agent ($HERMES_SCALEUP)..."
    copy_skills "$SKILLS_DIR" "$HERMES_SKILLS" "$HERMES_SCALEUP"
    copy_engine "$HERMES_SCALEUP"
    copy_knowledge "$HERMES_SCALEUP"
    copy_agent "$HERMES_SCALEUP"
    write_version "$HERMES_SCALEUP"

    local company_dir="$HERMES_SCALEUP/my-company"
    if [[ ! -d "$company_dir" ]]; then
        mkdir -p "$company_dir/worksheets"
        info "Created my-company template at $company_dir"
    else
        info "my-company directory exists — preserved user data"
    fi

    echo "  Hermes installation complete."
}

# ── Status ───────────────────────────────────────────────────────────────────

show_status() {
    echo ""
    echo "ScaleUp Installation Status"
    echo "==========================="
    echo ""

    # Source
    echo "Source: $SCRIPT_DIR"
    echo "Source version: $VERSION"
    echo ""

    # Claude Code
    if [[ -f "$CLAUDE_SCALEUP/VERSION" ]]; then
        local cv
        cv="$(cat "$CLAUDE_SCALEUP/VERSION")"
        local skill_count
        skill_count="$(find "$CLAUDE_SKILLS" -maxdepth 2 -name "SKILL.md" -path "*/scaleup-*" 2>/dev/null | wc -l | tr -d ' ')"
        echo "Claude Code: v$cv ($skill_count skills)"
        echo "  Skills: $CLAUDE_SKILLS"
        echo "  Engine: $CLAUDE_SCALEUP"
    else
        echo "Claude Code: not installed"
    fi
    echo ""

    # Hermes
    if [[ -f "$HERMES_SCALEUP/VERSION" ]]; then
        local hv
        hv="$(cat "$HERMES_SCALEUP/VERSION")"
        local hskill_count
        hskill_count="$(find "$HERMES_SKILLS" -maxdepth 2 -name "SKILL.md" -path "*/scaleup-*" 2>/dev/null | wc -l | tr -d ' ')"
        echo "Hermes: v$hv ($hskill_count skills)"
        echo "  Skills: $HERMES_SKILLS"
        echo "  Engine: $HERMES_SCALEUP"
    else
        echo "Hermes: not installed"
    fi
}

# ── Uninstall ────────────────────────────────────────────────────────────────

uninstall() {
    echo ""
    echo "Uninstalling ScaleUp..."

    # Claude Code
    if [[ -d "$CLAUDE_SCALEUP" ]]; then
        rm -rf "$CLAUDE_SCALEUP"
        info "Removed $CLAUDE_SCALEUP"
    fi
    for d in "$CLAUDE_SKILLS"/scaleup-*/; do
        [[ -d "$d" ]] && rm -rf "$d"
    done
    info "Removed Claude Code skills"

    # Hermes
    if [[ -d "$HERMES_SCALEUP" ]]; then
        rm -rf "$HERMES_SCALEUP"
        info "Removed $HERMES_SCALEUP"
    fi
    for d in "$HERMES_SKILLS"/scaleup-*/; do
        [[ -d "$d" ]] && rm -rf "$d"
    done
    info "Removed Hermes skills"

    echo "  Uninstall complete."
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
    local target="claude"
    local destination_root="$HOME"
    local action="install"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)
                [[ $# -ge 2 ]] || error "--target requires a value"
                target="$2"
                shift 2
                ;;
            --destination-root)
                [[ $# -ge 2 ]] || error "--destination-root requires a path"
                destination_root="$2"
                shift 2
                ;;
            --status) action="status"; shift ;;
            --uninstall) action="uninstall"; shift ;;
            --help|-h)
                echo "Usage: install.sh [--target claude|hermes|all] [--destination-root PATH] [--status] [--uninstall]"
                exit 0
                ;;
            *) error "Unknown option: $1" ;;
        esac
    done

    [[ -n "$destination_root" ]] || error "--destination-root cannot be empty"
    [[ "$destination_root" != "/" ]] || error "Refusing to use / as destination root"
    [[ "$destination_root" != *"'"* ]] || error "Destination root cannot contain a single quote"
    configure_targets "$destination_root"

    case "$action" in
        status) show_status; exit 0 ;;
        uninstall) uninstall; exit 0 ;;
    esac

    echo "ScaleUp Installer v$VERSION"
    echo "=========================="

    case "$target" in
        claude) install_claude ;;
        hermes) install_hermes ;;
        all)    install_claude; install_hermes ;;
        *)      error "Unknown target: $target (use claude, hermes, or all)" ;;
    esac

    echo ""
    echo "Done! Run '/scaleup-welcome' to get started."
}

main "$@"
