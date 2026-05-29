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
            print(f"Server already running (PID: {pid}) on http://localhost:{args.port}")
            return

    # Ensure .escala dir exists
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    # Determine server module path — use -m for correct package resolution
    project_root = Path(__file__).resolve().parent.parent

    # Start server process using -m (preserves package context)
    with open(log_file, "w") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "escala_server",
             "--host", args.host,
             "--port", str(args.port),
             "--static-root", args.static_root],
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
    parser = argparse.ArgumentParser(description="Escala Server — Local coaching dashboard server")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # start
    start_parser = subparsers.add_parser("start", help="Start the server")
    start_parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host (default: {DEFAULT_HOST})")
    start_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    start_parser.add_argument("--static-root", default=".", help="Root directory for static files")

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop the server")
    stop_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port (for display)")

    # status
    status_parser = subparsers.add_parser("status", help="Show server status")
    status_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port (for display)")

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
