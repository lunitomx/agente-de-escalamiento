---
story_id: s23.11
title: "MCP Server opcional — Memoria compartida entre LLMs"
epic: e23
type: code
status: started
created: 2026-05-30
---

## Acceptance Criteria

- [ ] `escala-agent/mcp/server.py` exists and functions as MCP server
- [ ] Tools: write_memo, read_memo, list_memos, search_memos, generate_index
- [ ] Reads/writes files in `~/.escala/memoria/`
- [ ] STDIO transport compatible with MCP spec
- [ ] Documented in AGENTS.md as optional
