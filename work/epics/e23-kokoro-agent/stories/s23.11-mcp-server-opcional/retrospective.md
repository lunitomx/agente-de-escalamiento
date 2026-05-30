---
story_id: s23.11
title: "MCP Server opcional — Memoria compartida entre LLMs"
status: complete
merged_at: 2026-05-30
---

Servidor MCP mínimo para compartir `~/.escala/memoria/` entre sesiones y LLMs.
Proporciona 5 herramientas: write_memo, read_memo, list_memos, search_memos, generate_index.
Usa STDIO transport. Opcional — el agente funciona sin él.
