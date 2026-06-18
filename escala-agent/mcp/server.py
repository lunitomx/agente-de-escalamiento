# Escala MCP Server

from pathlib import Path
from typing import Any
import json
from datetime import datetime


MEMORIA_DIR = Path.home() / ".escala" / "memoria"


def ensure_dir():
    MEMORIA_DIR.mkdir(parents=True, exist_ok=True)
    for sub in [
        "dailys",
        "analisis/cash",
        "analisis/strategy",
        "analisis/people",
        "analisis/execution",
        "dashboard",
    ]:
        (MEMORIA_DIR / sub).mkdir(parents=True, exist_ok=True)


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Simple MCP-style request handler."""
    method = request.get("method", "")

    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "escala_write_memo",
                    "description": "Write a memo (.md) file to memoria/",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path under memoria/ (e.g. 'analisis/cash/power-of-one-2026-05-30.md')",
                            },
                            "content": {
                                "type": "string",
                                "description": "Markdown content with YAML frontmatter",
                            },
                        },
                        "required": ["path", "content"],
                    },
                },
                {
                    "name": "escala_read_memo",
                    "description": "Read a .md file from memoria/",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path under memoria/",
                            },
                        },
                        "required": ["path"],
                    },
                },
                {
                    "name": "escala_list_memos",
                    "description": "List .md files in a directory under memoria/",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "dir": {
                                "type": "string",
                                "description": "Subdirectory (e.g. 'analisis/cash')",
                                "default": "",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results",
                                "default": 20,
                            },
                        },
                        "required": [],
                    },
                },
                {
                    "name": "escala_search_memos",
                    "description": "Search memo content by keyword",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search keyword",
                            },
                            "dir": {
                                "type": "string",
                                "description": "Subdirectory to search in",
                                "default": "",
                            },
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "escala_generate_index",
                    "description": "Regenerate the memoria/indice.md index file",
                    "inputSchema": {"type": "object", "properties": {}},
                },
            ]
        }

    elif method == "tools/call":
        tool = request.get("params", {}).get("name", "")
        args = request.get("params", {}).get("arguments", {})
        ensure_dir()

        if tool == "escala_write_memo":
            path = args["path"]
            content = args["content"]
            full_path = MEMORIA_DIR / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            return {
                "content": [
                    {"type": "text", "text": f"Written: {path} ({len(content)} chars)"}
                ]
            }

        elif tool == "escala_read_memo":
            path = args["path"]
            full_path = MEMORIA_DIR / path
            if not full_path.exists():
                return {
                    "content": [{"type": "text", "text": f"File not found: {path}"}],
                    "isError": True,
                }
            return {"content": [{"type": "text", "text": full_path.read_text()}]}

        elif tool == "escala_list_memos":
            subdir = args.get("dir", "")
            limit = args.get("limit", 20)
            target = MEMORIA_DIR / subdir if subdir else MEMORIA_DIR
            if not target.exists():
                return {"content": [{"type": "text", "text": "[]"}]}
            files = sorted(
                target.rglob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True
            )[:limit]
            result = [
                {
                    "path": str(f.relative_to(MEMORIA_DIR)),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }
                for f in files
            ]
            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

        elif tool == "escala_search_memos":
            query = args["query"].lower()
            subdir = args.get("dir", "")
            target = MEMORIA_DIR / subdir if subdir else MEMORIA_DIR
            if not target.exists():
                return {"content": [{"type": "text", "text": "[]"}]}
            results = []
            for f in target.rglob("*.md"):
                if query in f.read_text().lower():
                    results.append(
                        {
                            "path": str(f.relative_to(MEMORIA_DIR)),
                            "modified": datetime.fromtimestamp(
                                f.stat().st_mtime
                            ).isoformat(),
                        }
                    )
            return {
                "content": [
                    {"type": "text", "text": json.dumps(results[:20], indent=2)}
                ]
            }

        elif tool == "escala_generate_index":
            index_lines = [
                "# Índice de Memoria — Escala\n",
                f"*Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n",
            ]
            for subdir in [
                "dailys",
                "analisis/cash",
                "analisis/strategy",
                "analisis/people",
                "analisis/execution",
                "dashboard",
            ]:
                target = MEMORIA_DIR / subdir
                if target.exists():
                    files = sorted(
                        target.glob("*.md"),
                        key=lambda f: f.stat().st_mtime,
                        reverse=True,
                    )
                    if files:
                        index_lines.append(f"## {subdir}\n")
                        for f in files:
                            name = f.stem
                            rel = f.relative_to(MEMORIA_DIR)
                            index_lines.append(f"- [{name}]({rel})\n")
                        index_lines.append("\n")
            content = "".join(index_lines)
            (MEMORIA_DIR / "indice.md").write_text(content)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Index regenerated: {len(index_lines)} lines",
                    }
                ]
            }

    return {
        "content": [{"type": "text", "text": f"Unknown method: {method}"}],
        "isError": True,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        # STDIO transport for MCP
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = handle_request(request)
                print(json.dumps(response), flush=True)
            except Exception as e:
                print(json.dumps({"error": str(e)}), flush=True)
    else:
        print("Escala MCP Server — run with 'stdio' argument for MCP transport")
