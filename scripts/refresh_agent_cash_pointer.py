#!/usr/bin/env python3
"""Genera el remitente de cash del agente viejo (``escala-agent/``).

El procedimiento de cash vive en ``escala-skills/escala-cash*`` y las fórmulas
en la calculadora (``escala_server/cash/``). El agente viejo sólo remite ahí:
este script escribe ese remitente y, con ``--check``, falla si alguien lo
cambió a mano.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_SKILLS = ROOT / "escala-agent" / "skills"

# skill del agente viejo -> procedimiento canónico en escala-skills/
REMITENTES = {"escala-cash": "escala-cash"}


def render(nombre: str, destino: str) -> str:
    return f"""---
nombre: {nombre}
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
   `escala-skills/{destino}/SKILL.md`. Desde este archivo dentro del repo:
   `../../../escala-skills/{destino}/SKILL.md`.
2. En un paquete, sigue `references/procedures/{destino}.md`, junto a la
   puerta de ESCALA.
3. Los números los saca `escala_server/cash/calcular.py` (en un paquete:
   `references/calculadora/escala_server/cash/calcular.py`). Cada número trae
   su fórmula y su origen.

Si no encuentras el procedimiento o la calculadora, di exactamente:

> "No encontré la calculadora de ESCALA. No voy a hacer las cuentas de memoria."

y no des ningún número.
"""


def expected_files(root: Path = AGENT_SKILLS) -> dict[Path, str]:
    return {
        root / nombre / "SKILL.md": render(nombre, destino)
        for nombre, destino in REMITENTES.items()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=AGENT_SKILLS)
    args = parser.parse_args(argv)
    expected = expected_files(args.root)
    drift = [
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    if args.check:
        if drift:
            print("agent_cash_pointer_drift:" + ",".join(str(path) for path in drift))
            return 1
        print(f"agent cash pointers synchronized: {len(expected)}")
        return 0
    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"agent cash pointers refreshed: {len(expected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
