#!/usr/bin/env python3
"""Render finite compatibility wrappers from E56's internal alias map."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from escala_server.capabilities import (  # noqa: E402
    load_capability_catalog,
    load_legacy_aliases,
)

LEGACY_GLOB = "scale" + "up-*/SKILL.md"


LEGACY_ROOTS = (ROOT / ".claude" / "legacy-skills", ROOT / ".agents" / "legacy-skills")


def render(alias: str, target: str, notice: str) -> str:
    return f"""---
name: {alias}
description: Alias temporal de compatibilidad. Redirige al contrato canónico {target}.
---

# Alias legado: {alias}

Este alias no contiene lógica ni metodología propia. {notice}

1. Consulta `../../../escala-skills/catalog.yaml` y confirma que `{alias}` sigue
   autorizado durante su ventana de migración.
2. Continúa con el contrato canónico en
   `../../../escala-skills/{target}/SKILL.md`.
3. No muestres el catálogo técnico al empresario; sigue la experiencia
   conversacional definida por `escala`.
"""


def expected_files() -> dict[Path, str]:
    catalog = load_capability_catalog()
    aliases = {alias.alias: alias for alias in load_legacy_aliases(catalog)}
    expected: dict[Path, str] = {}
    for root in LEGACY_ROOTS:
        if not root.is_dir():
            continue
        for path in sorted(root.glob(LEGACY_GLOB)):
            alias = aliases.get(path.parent.name)
            if alias is None:
                raise ValueError(f"unmapped_legacy_skill:{path.parent.name}")
            expected[path] = render(alias.alias, alias.target, alias.notice)
    return expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    expected = expected_files()
    drift = [
        path
        for path, content in expected.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    if args.check:
        if drift:
            print(
                "legacy_alias_drift:"
                + ",".join(str(path.relative_to(ROOT)) for path in drift)
            )
            return 1
        print(f"legacy aliases synchronized: {len(expected)}")
        return 0
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")
    print(f"legacy aliases refreshed: {len(expected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
