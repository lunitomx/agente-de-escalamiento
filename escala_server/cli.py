"""Escala Server CLI — start, stop, and status commands."""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


PID_FILE = Path.home() / ".escala" / "server.pid"
LOG_FILE = Path.home() / ".escala" / "server.log"
DEFAULT_DB_PATH = str(Path.home() / ".escala" / "escala.db")
DEFAULT_PORT = 8080
DEFAULT_HOST = "localhost"


def cmd_start(args):
    """Start the Escala server in the background."""
    pid_file = PID_FILE
    log_file = LOG_FILE

    # Check if already running
    if pid_file.exists():
        pid = int(pid_file.read_text().strip())
        if _is_pid_running(pid):
            print(
                f"Server already running (PID: {pid}) on http://localhost:{args.port}"
            )
            return

    # Ensure .escala dir exists
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    # Determine server module path — use -m for correct package resolution
    project_root = Path(__file__).resolve().parent.parent

    # Build command arguments
    cmd_args = [
        sys.executable,
        "-m",
        "escala_server",
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--static-root",
        args.static_root,
        "--db-path",
        args.db_path,
    ]

    # Start server process using -m (preserves package context)
    with open(log_file, "w") as log:
        proc = subprocess.Popen(
            cmd_args,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            cwd=str(project_root),
        )

    # Write PID file
    pid_file.write_text(str(proc.pid))

    # Wait a moment and verify
    time.sleep(0.5)
    if _is_pid_running(proc.pid):
        print(f"Server started (PID: {proc.pid}) on http://{args.host}:{args.port}")
        print(f"Database: {args.db_path}")
    else:
        print("Error: Server failed to start. Check log:", log_file)
        sys.exit(1)


def cmd_stop(args):
    """Stop the running Escala server."""
    pid_file = PID_FILE

    if not pid_file.exists():
        print("Server is not running.")
        return

    pid = int(pid_file.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        # Wait for process to terminate
        for _ in range(10):
            if not _is_pid_running(pid):
                break
            time.sleep(0.3)
        else:
            # Force kill
            os.kill(pid, signal.SIGKILL)
        pid_file.unlink(missing_ok=True)
        print("Server stopped.")
    except ProcessLookupError:
        pid_file.unlink(missing_ok=True)
        print("Server was not running (stale PID file cleaned up).")


def cmd_status(args):
    """Show server status."""
    pid_file = PID_FILE

    if not pid_file.exists():
        print("Stopped")
        return

    pid = int(pid_file.read_text().strip())
    if _is_pid_running(pid):
        print(f"Running (PID: {pid})")
        print(f"Server: http://localhost:{args.port}")
        print(f"Database: {args.db_path}" if hasattr(args, "db_path") else "")
    else:
        print(f"Stopped (stale PID: {pid})")
        pid_file.unlink(missing_ok=True)


def _is_pid_running(pid: int) -> bool:
    """Check if a process with the given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Escala Server — Local coaching dashboard server"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # start
    start_parser = subparsers.add_parser("start", help="Start the server")
    start_parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"Host (default: {DEFAULT_HOST})"
    )
    start_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})"
    )
    start_parser.add_argument(
        "--static-root",
        default="escala_server/static",
        help="Root directory for static files",
    )
    start_parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=f"SQLite database path (default: {DEFAULT_DB_PATH})",
    )

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop the server")
    stop_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Port (for display)"
    )

    # status
    status_parser = subparsers.add_parser("status", help="Show server status")
    status_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Port (for display)"
    )
    status_parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help="SQLite database path (for display)",
    )

    # migrate
    migrate_parser = subparsers.add_parser(
        "migrate", help="Import .scaleup/ data into SQLite"
    )
    migrate_parser.add_argument(
        "yaml_root",
        nargs="?",
        default=".scaleup",
        help="Path to .scaleup/ directory (default: .scaleup)",
    )
    migrate_parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=f"SQLite database path (default: {DEFAULT_DB_PATH})",
    )

    # ── inicia ──
    inicia_parser = subparsers.add_parser("inicia", help="Start a coaching session")
    inicia_parser.add_argument(
        "--db-path",
        default=str(Path.home() / ".escala" / "escala.db"),
        help="SQLite database path",
    )

    # ── cierra ──
    cierra_parser = subparsers.add_parser(
        "cierra", help="Close the current coaching session"
    )
    cierra_parser.add_argument("--session-id", help="Session ID to close")
    cierra_parser.add_argument(
        "--db-path",
        default=str(Path.home() / ".escala" / "escala.db"),
        help="SQLite database path",
    )

    # ── verne ──
    verne_parser = subparsers.add_parser("verne", help="Consultar a Verne Harnish")
    verne_sub = verne_parser.add_subparsers(dest="verne_command")
    verne_ask_parser = verne_sub.add_parser("ask", help="Preguntar a Verne")
    verne_ask_parser.add_argument("question", nargs="+", help="Pregunta para Verne")
    verne_ask_parser.add_argument(
        "--db-path",
        default=str(Path.home() / ".escala" / "escala.db"),
        help="SQLite database path",
    )

    verne_review_parser = verne_sub.add_parser(
        "review-daily", help="Revisar un daily huddle"
    )
    verne_review_parser.add_argument(
        "daily_text", nargs="+", help="Texto del daily huddle"
    )
    verne_review_parser.add_argument(
        "--db-path",
        default=str(Path.home() / ".escala" / "escala.db"),
        help="SQLite database path",
    )

    verne_debate_parser = verne_sub.add_parser(
        "debate", help="Debatir una decisión estratégica con Verne"
    )
    verne_debate_parser.add_argument(
        "decision", nargs="+", help="Decisión estratégica a debatir"
    )
    verne_debate_parser.add_argument("--context", help="Contexto de la empresa")
    verne_debate_parser.add_argument(
        "--db-path",
        default=str(Path.home() / ".escala" / "escala.db"),
        help="SQLite database path",
    )

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "migrate":
        cmd_migrate(args)
    elif args.command == "inicia":
        cmd_inicia(args)
    elif args.command == "cierra":
        cmd_cierra(args)
    elif args.command == "verne":
        cmd_verne(args)
    else:
        parser.print_help()


def cmd_migrate(args):
    """Run YAML migration into SQLite."""
    from escala_server.migrate import migrate_from_yaml

    print(f"Migrating from {args.yaml_root} → {args.db_path}")
    result = migrate_from_yaml(args.db_path, args.yaml_root)
    print(f"Migration {result['status']}: {result['counts']}")
    print(f"Log: {result['log_path']}")


def cmd_inicia(args):
    """Start a coaching session."""
    from escala_server.session.session_start import SessionStartOrchestrator

    orchestrator = SessionStartOrchestrator(args.db_path)
    orchestrator.start_session()
    print(orchestrator.get_context_prompt())


def cmd_cierra(args):
    """Close a coaching session."""
    from escala_server.session.session_close import SessionCloseOrchestrator

    orchestrator = SessionCloseOrchestrator(args.db_path)
    session_id = getattr(args, "session_id", None)
    if session_id is None:
        raise SystemExit("--session-id is required for cierra")
    result = orchestrator.close_session(session_id)
    print(f"Session {result.session_id} closed.")
    print(f"  Duration: {result.duration}")
    print(f"  Changes: {result.changes_count}")
    print(f"  New facts: {result.new_facts_count}")
    print(f"  Summary: {result.summary}")
    print()

    # Verne's perspective (S21.4)
    from escala_server.verne_handler import VerneHandler

    verne = VerneHandler(args.db_path)
    vp = verne.session_perspective(
        category=getattr(result, "category", None),
        changes_count=result.changes_count,
        company=getattr(result, "company", None),
    )
    print(vp.get("perspective", ""))


def cmd_verne(args):
    """Dispatch Verne subcommands."""
    from escala_server.verne_handler import VerneHandler

    if args.verne_command == "ask":
        question = " ".join(args.question)
        handler = VerneHandler(args.db_path)
        result = handler.ask(question)
        print()
        print(result.get("answer", ""))
        print()
        if result.get("entity_count", 0) > 0:
            print(f"📚 Basado en {result['entity_count']} entidad(es) del grafo:")
            for name in result.get("entities_used", []):
                print(f"   • {name}")
        if result.get("principles_applied"):
            print(f"⚖️  Principios: {', '.join(result['principles_applied'])}")
        print(f"🏷️  Categoría: {result.get('category', 'general')}".capitalize())
    elif args.verne_command == "review-daily":
        daily_text = " ".join(args.daily_text)
        handler = VerneHandler(args.db_path)
        result = handler.review_daily(daily_text)
        print()
        print(result.get("observations", ""))
        print()
    elif args.verne_command == "debate":
        decision = " ".join(args.decision)
        context = getattr(args, "context", None)
        handler = VerneHandler(args.db_path)
        result = handler.board_debate(decision=decision, context=context)
        print()
        print(result.get("response", ""))
        print()
        if result.get("next_questions"):
            print("Próximas preguntas para reflexionar:")
            for i, q in enumerate(result["next_questions"], 1):
                print(f"  {i}. {q}")
        print()
    else:
        print("Comandos de Verne: ask, review-daily, debate")
        print()
        print('  escala verne ask "tu pregunta"')
        print("    → Verne responde desde su framework de 4 Decisiones")
        print('    Ej: escala verne ask "cómo mejoro mi flujo de efectivo"')
        print()
        print('  escala verne review-daily "logros de ayer, planes de hoy, obstáculos"')
        print("    → Verne califica tu daily (0-12) contra Rockefeller Habits")
        print(
            '    Ej: escala verne review-daily "ayer vendí 5, hoy voy a cobrar, no tengo maíz"'
        )
        print()
        print('  escala verne debate "decisión estratégica"')
        print("    → Verne analiza tu decisión con las 4 Decisiones")
        print('    Ej: escala verne debate "deberíamos abrir un nuevo local"')
        print()
        print("  También puedes preguntarle 'quién eres' para conocerlo.")


if __name__ == "__main__":
    main()
