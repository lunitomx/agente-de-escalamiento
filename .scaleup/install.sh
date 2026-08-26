#!/usr/bin/env bash
set -euo pipefail

# ScaleUp Cross-Platform Installer
# Installs ScaleUp skills, coaching engine, knowledge, and agent config.
#
# Usage:
#   ./install.sh                    # Install to Claude Code global
#   ./install.sh --target hermes    # Install to Hermes Agent
#   ./install.sh --target codex     # Install to Codex global
#   ./install.sh --target all       # Install to all platforms
#   ./install.sh --destination-root /tmp/scaleup-e2e
#   ./install.sh --status           # Show installation status
#   ./install.sh --uninstall        # Remove from all platforms

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/VERSION"
VERSION="0.0.0"
[[ -f "$VERSION_FILE" ]] && VERSION="$(cat "$VERSION_FILE")"

# Source directories
SKILLS_DIR="$(dirname "$SCRIPT_DIR")/.scaleup/internal/skills"
[[ -d "$SKILLS_DIR" ]] || SKILLS_DIR="$(dirname "$SCRIPT_DIR")/.claude/skills"
COACHING_DIR="$(dirname "$SCRIPT_DIR")/coaching"
KNOWLEDGE_DIR="$SCRIPT_DIR/knowledge"
AGENT_DIR="$SCRIPT_DIR/agent"
BIN_DIR="$SCRIPT_DIR/bin"
MEMORY_RUNTIME_DIR="$(dirname "$SCRIPT_DIR")/escala_server"

# Target directories (configured after parsing CLI arguments)
CLAUDE_SKILLS=""
CLAUDE_SCALEUP=""
HERMES_SKILLS=""
HERMES_SCALEUP=""
CODEX_SKILLS=""
CODEX_SCALEUP=""
MANAGED_SKILLS_FILE=".scaleup-managed-skills"

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
    CODEX_SKILLS="$destination_root/.codex/skills"
    CODEX_SCALEUP="$destination_root/.codex/scaleup"
}

adapt_skill() {
    local skill_file="$1" runtime_root="$2" escaped_root
    escaped_root="${runtime_root//\\/\\\\}"
    escaped_root="${escaped_root//&/\\&}"
    escaped_root="${escaped_root//|/\\|}"

    sed -i \
        -e "s|sys\\.path\\.insert(0, '\\.')|sys.path.insert(0, '$escaped_root')|g" \
        -e "s|sys\\.path\\.insert(0,'\\.')|sys.path.insert(0, '$escaped_root')|g" \
        -e "s|str(pathlib\\.Path('\\.scaleup/agent'))|str(pathlib.Path('$escaped_root/agent'))|g" \
        -e "s|python3 \\.scaleup/agent/validators/|python3 $escaped_root/agent/validators/|g" \
        -e "s|python3 -m coaching\\.|PYTHONPATH='$escaped_root' python3 -m coaching.|g" \
        -e "s|\.scaleup/bin/scaleup-frontdoor|$escaped_root/bin/scaleup-frontdoor|g" \
        "$skill_file"
}

is_known_scaleup_skill() {
    local name="$1"
    [[ "$name" == "scaleup" ]] || [[ -d "$SKILLS_DIR/$name" && "$name" == scaleup-* ]]
}

remove_managed_skills() {
    local skills="$1" runtime_root="$2" name known_dir
    local manifest="$runtime_root/$MANAGED_SKILLS_FILE"

    # The manifest identifies what this installer wrote. Current source skill
    # names are included for upgrades from installers predating the manifest.
    # Every candidate is still checked against the repository's known names,
    # so a third-party `scaleup-*` directory can never be removed by prefix.
    while IFS= read -r name; do
        [[ -n "$name" ]] || continue
        is_known_scaleup_skill "$name" || continue
        if [[ -d "$skills/$name" ]]; then
            rm -rf "$skills/$name"
        fi
    done < <(
        [[ -f "$manifest" ]] && cat "$manifest"
        printf '%s\n' "scaleup"
        for known_dir in "$SKILLS_DIR"/scaleup-*/; do
            [[ -d "$known_dir" ]] && basename "$known_dir"
        done
    )
}

write_managed_skills_manifest() {
    local runtime_root="$1"
    mkdir -p "$runtime_root"
    printf '%s\n' "scaleup" > "$runtime_root/$MANAGED_SKILLS_FILE"
}

copy_skills() {
    local src="$1" dst="$2" runtime_root="$3" count=0
    mkdir -p "$dst"
    remove_managed_skills "$dst" "$runtime_root"
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

copy_front_door() {
    local dst="$1" runtime_root="$2" candidate
    # The Claude copy contains executable paths which adapt_skill rewrites for
    # global installs. .agents remains the local discovery copy for Codex.
    for candidate in "$(dirname "$SCRIPT_DIR")/.claude/skills/scaleup" "$(dirname "$SCRIPT_DIR")/.agents/skills/scaleup"; do
        [[ -f "$candidate/SKILL.md" ]] || continue
        mkdir -p "$dst/scaleup"
        cp "$candidate/SKILL.md" "$dst/scaleup/SKILL.md"
        adapt_skill "$dst/scaleup/SKILL.md" "$runtime_root"
        info "Copied ScaleUp front door to $dst/scaleup"
        return
    done
}

install_public_front_door() {
    local skills="$1" runtime_root="$2"
    mkdir -p "$skills"
    # Legacy skills remain in the source repository for compatibility, but are
    # implementation details in every installed product runtime.
    remove_managed_skills "$skills" "$runtime_root"
    copy_front_door "$skills" "$runtime_root"
    [[ -f "$skills/scaleup/SKILL.md" ]] || error "Installation requires the public ScaleUp skill at .claude/skills/scaleup/SKILL.md"
    write_managed_skills_manifest "$runtime_root"
}

copy_engine() {
    local dst="$1"
    # Clean slate: remove old coaching engine to avoid orphaned files (engine.py, formatter.py, summary/)
    rm -rf "$dst/coaching"
    mkdir -p "$dst/coaching"
    # Copy Python modules
    for mod in core dashboard diagnose export level opsp progress pulse router summary welcome worksheet; do
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
    cp "$COACHING_DIR/opsp.py" "$dst/coaching/" 2>/dev/null || true
    info "Copied coaching engine to $dst/coaching/ (clean install)"
}

copy_memory_runtime() {
    local dst="$1"
    rm -rf "$dst/escala_server"
    mkdir -p "$dst/escala_server"
    for module in __init__.py schema.py project_memory.py project_memory_context.py project_memory_session_close.py project_memory_continuity.py memory_engine.py graph_engine.py; do
        cp "$MEMORY_RUNTIME_DIR/$module" "$dst/escala_server/$module"
    done
    cp -a "$MEMORY_RUNTIME_DIR/daos" "$dst/escala_server/daos"
    info "Copied local SQLite memory runtime to $dst/escala_server/"
}

copy_knowledge() {
    local dst="$1"
    rm -rf "$dst/knowledge"
    mkdir -p "$dst/knowledge"
    cp -a "$KNOWLEDGE_DIR/." "$dst/knowledge/"
    info "Copied knowledge ontology to $dst/knowledge/ (synchronized)"
}

copy_agent() {
    local dst="$1"
    rm -rf "$dst/agent"
    mkdir -p "$dst/agent"
    cp -a "$AGENT_DIR/." "$dst/agent/"
    info "Copied agent config to $dst/agent/ (synchronized)"
}
copy_bin() {
    local dst="$1"
    rm -rf "$dst/bin"
    mkdir -p "$dst/bin"
    cp "$BIN_DIR/scaleup-frontdoor" "$dst/bin/scaleup-frontdoor"
    chmod 755 "$dst/bin/scaleup-frontdoor"
    info "Copied ScaleUp commands to $dst/bin/"
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
    install_public_front_door "$CLAUDE_SKILLS" "$CLAUDE_SCALEUP"
    copy_engine "$CLAUDE_SCALEUP"
    copy_memory_runtime "$CLAUDE_SCALEUP"
    copy_knowledge "$CLAUDE_SCALEUP"
    copy_agent "$CLAUDE_SCALEUP"
    copy_bin "$CLAUDE_SCALEUP"
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
    install_public_front_door "$HERMES_SKILLS" "$HERMES_SCALEUP"
    copy_engine "$HERMES_SCALEUP"
    copy_memory_runtime "$HERMES_SCALEUP"
    copy_knowledge "$HERMES_SCALEUP"
    copy_agent "$HERMES_SCALEUP"
    copy_bin "$HERMES_SCALEUP"
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

install_codex() {
    echo ""
    echo "Installing ScaleUp to Codex ($CODEX_SCALEUP)..."
    install_public_front_door "$CODEX_SKILLS" "$CODEX_SCALEUP"
    copy_engine "$CODEX_SCALEUP"
    copy_memory_runtime "$CODEX_SCALEUP"
    copy_knowledge "$CODEX_SCALEUP"
    copy_agent "$CODEX_SCALEUP"
    copy_bin "$CODEX_SCALEUP"
    write_version "$CODEX_SCALEUP"

    local company_dir="$CODEX_SCALEUP/my-company"
    if [[ ! -d "$company_dir" ]]; then
        mkdir -p "$company_dir/worksheets"
        info "Created my-company template at $company_dir"
    else
        info "my-company directory exists — preserved user data"
    fi
    echo "  Codex installation complete."
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
    echo ""

    if [[ -f "$CODEX_SCALEUP/VERSION" ]]; then
        local xv xskill_count
        xv="$(cat "$CODEX_SCALEUP/VERSION")"
        xskill_count="$(find "$CODEX_SKILLS" -maxdepth 2 -name "SKILL.md" \( -path "*/scaleup-*" -o -path "*/scaleup/SKILL.md" \) 2>/dev/null | wc -l | tr -d ' ')"
        echo "Codex: v$xv ($xskill_count skills)"
        echo "  Skills: $CODEX_SKILLS"
        echo "  Engine: $CODEX_SCALEUP"
    else
        echo "Codex: not installed"
    fi
}

# ── Uninstall ────────────────────────────────────────────────────────────────

uninstall_runtime() {
    local label="$1" skills="$2" runtime="$3" purge="$4"
    remove_managed_skills "$skills" "$runtime"
    if [[ -d "$runtime" ]]; then
        if [[ "$purge" == "true" ]]; then
            rm -rf "$runtime"
            info "Removed $runtime including user company data"
        else
            rm -rf "$runtime/coaching" "$runtime/knowledge" "$runtime/agent" "$runtime/bin" "$runtime/escala_server" "$runtime/VERSION" "$runtime/$MANAGED_SKILLS_FILE"
            rmdir "$runtime" 2>/dev/null || true
            info "Removed managed $label files; preserved $runtime/my-company and $runtime/memory"
        fi
    fi
    info "Removed $label skills"
}

uninstall() {
    local target="$1" purge="$2"
    echo ""
    echo "Uninstalling ScaleUp..."
    case "$target" in
        claude) uninstall_runtime "Claude Code" "$CLAUDE_SKILLS" "$CLAUDE_SCALEUP" "$purge" ;;
        hermes) uninstall_runtime "Hermes" "$HERMES_SKILLS" "$HERMES_SCALEUP" "$purge" ;;
        codex) uninstall_runtime "Codex" "$CODEX_SKILLS" "$CODEX_SCALEUP" "$purge" ;;
        all)
            uninstall_runtime "Claude Code" "$CLAUDE_SKILLS" "$CLAUDE_SCALEUP" "$purge"
            uninstall_runtime "Hermes" "$HERMES_SKILLS" "$HERMES_SCALEUP" "$purge"
            uninstall_runtime "Codex" "$CODEX_SKILLS" "$CODEX_SCALEUP" "$purge"
            ;;
        *) error "Unknown target: $target (use claude, hermes, codex, or all)" ;;
    esac
    echo "  Uninstall complete."
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
    local target="claude"
    local target_provided="false"
    local destination_root="$HOME"
    local action="install"
    local purge="false"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --target)
                [[ $# -ge 2 ]] || error "--target requires a value"
                target="$2"
                target_provided="true"
                shift 2
                ;;
            --destination-root)
                [[ $# -ge 2 ]] || error "--destination-root requires a path"
                destination_root="$2"
                shift 2
                ;;
            --status) action="status"; shift ;;
            --uninstall) action="uninstall"; shift ;;
            --purge) purge="true"; shift ;;
            --help|-h)
                echo "Usage: install.sh [--target claude|hermes|codex|all] [--destination-root PATH] [--status] [--uninstall [--purge]] (uninstall defaults to all)"
                exit 0
                ;;
            *) error "Unknown option: $1" ;;
        esac
    done

    [[ -n "$destination_root" ]] || error "--destination-root cannot be empty"
    [[ "$destination_root" != "/" ]] || error "Refusing to use / as destination root"
    [[ "$destination_root" != *"'"* ]] || error "Destination root cannot contain a single quote"
    configure_targets "$destination_root"

    if [[ "$action" == "uninstall" && "$target_provided" == "false" ]]; then
        target="all"
    fi

    case "$action" in
        status) show_status; exit 0 ;;
        uninstall) uninstall "$target" "$purge"; exit 0 ;;
    esac

    echo "ScaleUp Installer v$VERSION"
    echo "=========================="

    case "$target" in
        claude) install_claude ;;
        hermes) install_hermes ;;
        codex)  install_codex ;;
        all)    install_claude; install_hermes; install_codex ;;
        *)      error "Unknown target: $target (use claude, hermes, codex, or all)" ;;
    esac

    echo ""
    echo "Done! Open Claude Code or Codex and write: ‘Quiero organizar mi empresa.’"
}

main "$@"
