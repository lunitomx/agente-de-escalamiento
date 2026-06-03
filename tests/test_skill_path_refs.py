"""Smoke test: las rutas estáticas referenciadas por los SKILL.md de escala
deben existir en el repo.

pytest ejercita el engine, no la prosa de los SKILL.md. Este test cubre ese
hueco: extrae cada ruta estática (.scaleup/…, templates/…, conocimiento/… con
extensión conocida) de cada SKILL.md de `escala-skills/` y verifica que el
archivo exista. Detecta las refs rotas de los issues #2/#3 y futuras regresiones
de la migración ScaleUp→Escala.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_FILES = sorted((REPO_ROOT / "escala-skills").glob("**/SKILL.md"))

# Rutas estáticas con extensión conocida bajo dirs versionados del repo.
PATH_RE = re.compile(r'(?:\.scaleup|templates|conocimiento)/[^\s`\'")|]+\.(?:yaml|yml|md|py)')
# Placeholders / paths dinámicos (generados por el usuario en runtime).
PLACEHOLDER_RE = re.compile(r'[{}<>*]|\$\(|YYYY|\.\.\.')

# Paths de EJEMPLO (estado generado por el usuario, no assets versionados).
ALLOWLIST = {
    ".scaleup/my-company/worksheets/face.yaml",  # ejemplo de estado de worksheet
}


def _static_refs(text: str) -> set[str]:
    return {
        m for m in PATH_RE.findall(text)
        if not PLACEHOLDER_RE.search(m) and m not in ALLOWLIST
    }


@pytest.mark.skipif(not SKILL_FILES, reason="escala-skills/ no presente")
@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_static_paths_exist(skill_file):
    text = skill_file.read_text(encoding="utf-8")
    missing = [ref for ref in _static_refs(text) if not (REPO_ROOT / ref).exists()]
    assert not missing, f"{skill_file.parent.name} referencia rutas inexistentes: {missing}"
