"""S86.32 — Las fichas del curso de cash viajan en la copia que se instala.

Lo que se prueba:
- el README que se instala y el overview de las fichas terminan con el aviso de
  autoría, tal cual;
- la frontera pública admite nombrar la metodología sólo en esas dos rutas
  exactas; en cualquier otro archivo exportado sigue fallando, y la frase
  «derived from Scaling Up» falla en todas partes;
- la copia construida desde HEAD trae las 19 fichas y el overview, byte a byte,
  y el verificador independiente pasa.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from validators.public_boundary import (
    BoundaryFindingCode,
    load_public_boundary_policy,
    scan_public_content,
)
from validators.public_export import (
    VerificationStatus,
    load_public_export_policy,
    load_third_party_inventory,
    verify_public_export,
)

ROOT = Path(__file__).resolve().parents[1]
FICHAS = ROOT / ".escala" / "knowledge" / "cash"
BOUNDARY = ROOT / "governance" / "public-boundary.yaml"

AVISO = (
    "**Aviso.** Este agente lo creó Eduardo Luna para participantes de EO y EOA "
    "en Querétaro, con apuntes y lecciones de cursos que tomó. Lo hizo con cariño "
    "para empresarios de su zona. No es un producto oficial de Scaling Up, de "
    "Gazelles ni de EO, ni está avalado por ellos. Se prohíbe su uso comercial."
)
CON_AVISO = ("README.md", ".escala/knowledge/cash/overview.md")


def _termina_con_aviso(texto: str) -> bool:
    return texto.rstrip().endswith("---\n\n" + AVISO)


# ── El aviso de autoría ────────────────────────────────────────────────────


@pytest.mark.parametrize("ruta", CON_AVISO)
def test_el_archivo_que_se_instala_termina_con_el_aviso(ruta: str) -> None:
    assert _termina_con_aviso((ROOT / ruta).read_text(encoding="utf-8"))


def test_quitar_el_aviso_se_nota() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    sin_aviso = readme.replace(AVISO, "")
    assert not _termina_con_aviso(sin_aviso)
    cambiado = readme.replace("Se prohíbe su uso comercial.", "Úsalo como quieras.")
    assert not _termina_con_aviso(cambiado)


# ── La frontera pública: exención por ruta exacta, sólo de texto ───────────


def _reglas(ruta: str, texto: str) -> set[str]:
    politica = load_public_boundary_policy(BOUNDARY)
    return {
        violacion.rule_id
        for violacion in scan_public_content(ruta, texto.encode("utf-8"), politica)
        if violacion.code is BoundaryFindingCode.PROHIBITED_TEXT
    }


@pytest.mark.parametrize("ruta", CON_AVISO)
def test_el_aviso_pasa_la_frontera_en_su_ruta(ruta: str) -> None:
    texto = (ROOT / ruta).read_text(encoding="utf-8")
    assert _reglas(ruta, texto) == set()


@pytest.mark.parametrize(
    "ruta",
    [
        "escala_server/README.md",
        ".escala/knowledge/cash/01-ciclo-del-efectivo.md",
        "conocimiento/cash/README.md",
        "docs/README.md",
    ],
)
def test_el_aviso_en_otra_ruta_sigue_fallando(ruta: str) -> None:
    assert {"public.product_identity", "public.company_identity"} <= _reglas(
        ruta, AVISO
    )


def test_el_autor_del_libro_solo_se_admite_en_el_overview() -> None:
    texto = "Scaling Up de Verne Harnish"
    assert _reglas(".escala/knowledge/cash/overview.md", texto) == set()
    assert "public.author_identity" in _reglas("README.md", texto)


@pytest.mark.parametrize("ruta", CON_AVISO)
def test_atribuir_el_producto_a_la_metodologia_falla_en_todas_partes(
    ruta: str,
) -> None:
    assert "public.source_attribution" in _reglas(
        ruta, "ESCALA is derived from Scaling Up."
    )


def test_la_ruta_exenta_no_exime_el_nombre_de_archivo() -> None:
    politica = load_public_boundary_policy(BOUNDARY)
    violaciones = scan_public_content(
        ".escala/knowledge/cash/scaling_up.md", b"hola", politica
    )
    assert any(v.code is BoundaryFindingCode.PROHIBITED_PATH for v in violaciones)


# ── Las fichas viajan en la copia que se instala ───────────────────────────


def test_hay_diecinueve_fichas_y_un_overview() -> None:
    assert len(sorted(FICHAS.glob("[0-9][0-9]-*.md"))) == 19
    assert (FICHAS / "overview.md").is_file()


def test_la_copia_lleva_las_fichas_y_el_verificador_pasa(tmp_path: Path) -> None:
    from tests.test_public_skill_installation import _portable_artifact

    copia = _portable_artifact(tmp_path / "escala")
    for ficha in sorted(FICHAS.glob("*.md")):
        llegada = copia / ".escala" / "knowledge" / "cash" / ficha.name
        assert llegada.read_bytes() == ficha.read_bytes(), ficha.name
    assert _termina_con_aviso((copia / "README.md").read_text(encoding="utf-8"))

    resultado = verify_public_export(
        artifact=copia,
        policy=load_public_export_policy(ROOT / "governance/public-export.yaml"),
        inventory=load_third_party_inventory(ROOT / "governance/third-party.yaml"),
        boundary_policy=load_public_boundary_policy(BOUNDARY),
    )
    assert resultado.violations == []
    assert resultado.technical_artifact_status is VerificationStatus.PASS
