"""Escala Server entry point for `python -m escala_server`."""

import argparse
import sys
from pathlib import Path


def main():
    # Ensure project root is on path (supports both `-m` and direct script execution)
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from escala_server.server import make_server

    parser = argparse.ArgumentParser(description="Escala Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--static-root", default=".", help="Static files root directory")
    args = parser.parse_args()

    server = make_server(
        host=args.host,
        port=args.port,
        static_root=args.static_root,
    )

    print(f"Escala Server running on http://{args.host}:{args.port}")
    print(f"Static root: {args.static_root}")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
