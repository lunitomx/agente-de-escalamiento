---
nombre: escala-cash
descripcion: "Cash — remite al procedimiento de ESCALA. Los números los saca la calculadora de ESCALA."
licencia: MIT
creditos:
  metodologia: Alan Miltz (Scaling Up / Gazelles)
  adaptacion: Kokoro (Eduardo Muñoz Luna)
compatible_con: [Claude Code, Codex CLI, Hermes, OpenClaude, Cursor]
---

# ESCALA — Cash

<!-- Generado por scripts/refresh_agent_cash_pointer.py. No lo edites a mano. -->

Este skill no tiene procedimiento ni fórmulas propias. Sigue el procedimiento
de ESCALA y deja que la calculadora haga las cuentas:

1. En la copia de ESCALA (la carpeta donde se clonó), sigue
   `escala-skills/escala-cash/SKILL.md`. Desde este archivo dentro del repo:
   `../../../escala-skills/escala-cash/SKILL.md`.
2. En un paquete, sigue `references/procedures/escala-cash.md`, junto a la
   puerta de ESCALA.
3. Los números los saca `escala_server/cash/calcular.py` (en un paquete:
   `references/calculadora/escala_server/cash/calcular.py`). Cada número trae
   su fórmula y su origen.

Si no encuentras el procedimiento o la calculadora, di exactamente:

> "No encontré la calculadora de ESCALA. No voy a hacer las cuentas de memoria."

y no des ningún número.
