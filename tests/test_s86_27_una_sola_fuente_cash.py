"""S86.27 — Una sola fuente por fórmula y por procedimiento de cash.

Las fórmulas de cash viven en la calculadora (``escala_server/cash/curso.py``).
Los procedimientos de cash viven en ``escala-skills/escala-cash*``. Todo lo
demás remite ahí. Esta prueba falla si:

- un texto de cash (procedimiento, puerta, skill del agente viejo, ficha,
  subagente) escribe una fórmula en vez de remitir a la calculadora;
- un procedimiento de cash existe en dos lugares con contenido distinto;
- la copia portable no lleva lo que la calculadora y la puerta necesitan.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from escala_server.cash import curso
from tests.test_s86_16_calculadora_en_paquete import _estados, _indicador
from tests.test_s86_16_procedimientos_sin_modelo import problemas

ROOT = Path(__file__).resolve().parents[1]
AGENTE_SKILLS = ROOT / "escala-agent" / "skills"
CANONICOS = ROOT / "escala-skills"

# Todo texto que habla de cash y que el modelo puede leer.
TEXTOS_DE_CASH: list[Path] = sorted(
    [
        CANONICOS / "escala" / "SKILL.md",
        *CANONICOS.glob("escala-cash*/SKILL.md"),
        *AGENTE_SKILLS.glob("*/SKILL.md"),
        *(ROOT / "escala-agent").glob("*.md"),
        *(ROOT / ".escala" / "knowledge" / "cash").glob("*.md"),
        ROOT / ".escala" / "agent" / "sub-agents" / "cash.md",
        ROOT / ".scaleup" / "agent" / "sub-agents" / "cash.md",
        *(ROOT / ".scaleup" / "knowledge" / "cash").rglob("*.md"),
        ROOT / "adapters" / "claude" / "agents" / "escala-cash.md",
        ROOT / "adapters" / "codex" / "agents" / "escala-cash.toml",
        *(ROOT / ".claude" / "legacy-skills").glob("scaleup-cash*/SKILL.md"),
        ROOT / "templates" / "cash-conversion-cycle.md",
    ]
)

# Procedimientos de otras áreas que el agente viejo también duplica. No son de
# cash: quedan anotados para su propia historia. La lista sólo puede encoger.
DUPLICADOS_FUERA_DE_CASH = frozenset(
    {"escala-bugreport", "escala-execution", "escala-people", "escala-strategy"}
)

# ── El revisor de fórmulas ─────────────────────────────────────────────────

_CUENTA = (
    r"(?:(?:cambio en )?(?:ventas|clientes|inventarios?|proveedores|costo(?: de ventas)?|"
    r"utilidad(?: bruta| de operaci[oó]n| antes de impuestos)?|"
    r"gastos(?: de operaci[oó]n)?|capital de trabajo|deuda neta|capital|bancos|"
    r"pr[eé]stamos(?: que pagan inter[eé]s)?|devoluciones(?:, rebajas y bonificaciones)?|"
    r"salario de mercado|sueldo(?: actual del due[nñ]o)?|"
    r"d[ií]as(?: del periodo| de clientes| de inventario| de proveedores)|"
    r"ccc|dso|dio|dpo|cogs|opex|ar|ap)(?: al (?:final|inicio))?)"
)
_OPERADOR = r"(?:÷|×|\+|−|\s-\s|\s/\s|\s\*\s)"
_PORCENTAJE = r"\d+(?:[.,]\d+)?\s*%"

FORMULA = re.compile(
    # dos cuentas unidas por una operación: «clientes ÷ (ventas ÷ días del periodo)»
    rf"\b{_CUENTA}\b\s*{_OPERADOR}\s*\(?\s*\b{_CUENTA}\b"
    # una cuenta por un porcentaje: «Ventas × 1%», «1% × utilidad bruta»
    rf"|\b{_CUENTA}\b\s*×\s*{_PORCENTAJE}"
    rf"|(?:{_PORCENTAJE}|\b100)\s*×\s*\(?\s*\b{_CUENTA}\b"
    # una cuenta igual a una expresión con otra cuenta: «Ciclo = DSO + …»
    rf"|\b(?:ciclo|{_CUENTA})\b\s*=\s*\(?\s*\b{_CUENTA}\b",
    flags=re.IGNORECASE,
)


def formulas_escritas(texto: str) -> list[str]:
    """Cada fórmula escrita con palabras; un ejemplo con cifras no cuenta."""
    return [coincidencia.group(0) for coincidencia in FORMULA.finditer(texto)]


def formulas_de_la_calculadora() -> list[str]:
    """Las fórmulas que la calculadora le da al dueño: la única fuente."""
    encontradas: set[str] = set()
    for valor in vars(curso).values():
        formula = getattr(valor, "formula", None)
        if isinstance(formula, str) and isinstance(getattr(valor, "clave", None), str):
            encontradas.add(formula)
    for _, _, flujo, utilidad in curso.PALANCAS.values():
        encontradas.update((flujo, utilidad))
    for _, _, por_periodo, una_vez in curso.PARTES.values():
        encontradas.update((por_periodo, una_vez))
    return sorted(encontradas)


def _con_operacion(formula: str) -> bool:
    return bool(re.search(r"[÷×+−]", formula))


def test_la_calculadora_tiene_las_formulas() -> None:
    formulas = formulas_de_la_calculadora()
    assert len(formulas) >= 25
    assert "clientes ÷ (ventas ÷ días del periodo)" in formulas
    assert "1% × ventas − 1% × clientes" in formulas


@pytest.mark.parametrize(
    "formula", [f for f in formulas_de_la_calculadora() if _con_operacion(f)]
)
def test_el_revisor_atrapa_cada_formula_de_la_calculadora(formula: str) -> None:
    """Si alguien copia una fórmula de la calculadora a un texto, se ve."""
    assert formulas_escritas(formula), formula
    assert formulas_escritas(f"- `dias`: {formula.capitalize()}."), formula


@pytest.mark.parametrize(
    "ejemplo",
    [
        "Días de clientes    = Clientes ÷ (Ventas ÷ días del periodo)",
        "Ciclo = DSO + DIO − DPO",
        "| Precio | Subir precio 1% | Ventas × 1% | Ventas × 1% − Clientes × 1% |",
        "Capital de trabajo = clientes + inventario − proveedores = 6,178,173.85",
        "Utilidad bruta = Ventas − Costo de ventas.",
        "CCC = DSO + DIO - DPO",
    ],
)
def test_el_revisor_atrapa_formulas_reescritas(ejemplo: str) -> None:
    assert formulas_escritas(ejemplo)


@pytest.mark.parametrize(
    "ejemplo",
    [
        "Capital de trabajo: clientes 5,639,601.55 + inventario 1,771,040.54 − "
        "proveedores 1,232,468.24 = 6,178,173.85.",
        "La fórmula viene en el campo `formula` del JSON de la calculadora.",
        "Pagaba al proveedor el día 14 y el cliente tardaba 39 días más en pagar.",
        "Cobrar 1 día antes",
    ],
)
def test_un_ejemplo_con_cifras_no_es_una_formula(ejemplo: str) -> None:
    assert formulas_escritas(ejemplo) == []


def test_hay_textos_de_cash_que_revisar() -> None:
    assert len(TEXTOS_DE_CASH) >= 30
    assert all(ruta.is_file() for ruta in TEXTOS_DE_CASH)


@pytest.mark.parametrize(
    "ruta", TEXTOS_DE_CASH, ids=lambda ruta: str(ruta.relative_to(ROOT))
)
def test_ninguna_formula_de_cash_se_escribe_fuera_de_la_calculadora(ruta: Path) -> None:
    assert formulas_escritas(ruta.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "ruta", TEXTOS_DE_CASH, ids=lambda ruta: str(ruta.relative_to(ROOT))
)
def test_ningun_texto_de_cash_trae_limites_inventados(ruta: Path) -> None:
    """Incluye el skill de dashboards del agente viejo («CCC > 60»)."""
    assert problemas(ruta.read_text(encoding="utf-8")) == []


# ── Procedimientos duplicados ──────────────────────────────────────────────


def test_el_agente_viejo_remite_al_procedimiento_de_cash() -> None:
    from scripts.refresh_agent_cash_pointer import expected_files

    esperados = expected_files()
    assert set(esperados) == {AGENTE_SKILLS / "escala-cash" / "SKILL.md"}
    for ruta, contenido in esperados.items():
        assert ruta.read_text(encoding="utf-8") == contenido
        assert "escala-skills/escala-cash/SKILL.md" in contenido
        assert (CANONICOS / "escala-cash" / "SKILL.md").is_file()


def test_el_remitente_detecta_un_cambio_a_mano(tmp_path: Path) -> None:
    from scripts.refresh_agent_cash_pointer import main

    assert main(["--check"]) == 0
    copia = tmp_path / "SKILL.md"
    copia.write_text("Días de clientes = clientes ÷ ventas\n", encoding="utf-8")
    assert main(["--check", "--root", str(tmp_path)]) == 1


def test_ningun_procedimiento_de_cash_esta_duplicado_con_otro_contenido() -> None:
    from scripts.refresh_agent_cash_pointer import expected_files

    remitentes = expected_files()
    distintos: list[str] = []
    for viejo in sorted(AGENTE_SKILLS.glob("*/SKILL.md")):
        nombre = viejo.parent.name
        canonico = CANONICOS / nombre / "SKILL.md"
        if not canonico.is_file() or nombre in DUPLICADOS_FUERA_DE_CASH:
            continue
        if (
            viejo in remitentes
            and viejo.read_text(encoding="utf-8") == remitentes[viejo]
        ):
            continue
        if viejo.read_bytes() != canonico.read_bytes():
            distintos.append(nombre)
    assert distintos == []


def test_la_lista_de_pendientes_no_tiene_cash_y_solo_encoge() -> None:
    assert not any(
        nombre.startswith("escala-cash") for nombre in DUPLICADOS_FUERA_DE_CASH
    )
    for nombre in DUPLICADOS_FUERA_DE_CASH:
        assert (AGENTE_SKILLS / nombre / "SKILL.md").is_file(), (
            f"ya no está duplicado: quita {nombre}"
        )
        assert (CANONICOS / nombre / "SKILL.md").is_file(), (
            f"ya no está duplicado: quita {nombre}"
        )


def test_el_conocimiento_viejo_de_cash_remite_y_no_es_otra_copia() -> None:
    viejo = ROOT / ".scaleup" / "knowledge" / "cash"
    assert sorted(
        p.relative_to(viejo).as_posix() for p in viejo.rglob("*") if p.is_file()
    ) == ["README.md"]
    remite = (viejo / "README.md").read_text(encoding="utf-8")
    assert "conocimiento/cash/" in remite
    assert ".escala/knowledge/cash/" in remite
    subagente = (ROOT / ".scaleup" / "agent" / "sub-agents" / "cash.md").read_text(
        encoding="utf-8"
    )
    assert ".escala/agent/sub-agents/cash.md" in subagente
    assert ".scaleup/knowledge/cash/`" not in subagente


# ── Las fichas ─────────────────────────────────────────────────────────────


def test_el_overview_manda_las_cuentas_a_la_calculadora() -> None:
    overview = (ROOT / ".escala" / "knowledge" / "cash" / "overview.md").read_text(
        encoding="utf-8"
    )
    assert "haz la cuenta" not in overview
    assert "escala_server/cash/calcular.py" in overview
    assert "No voy a hacer las cuentas de memoria." in overview
    for ficha in sorted(
        (ROOT / ".escala" / "knowledge" / "cash").glob("[0-9][0-9]-*.md")
    ):
        assert f"`{ficha.name}`" in overview, ficha.name


# ── La copia portable lleva lo que la calculadora necesita ─────────────────


def test_la_exportacion_lleva_las_fichas_y_el_lector() -> None:
    import yaml

    politica: Any = yaml.safe_load(
        (ROOT / "governance" / "public-export.yaml").read_text(encoding="utf-8")
    )
    rutas = {seleccion["path"] for seleccion in politica["selections"]}
    assert {".escala/knowledge/cash", "escala_server/financial"} <= rutas


def test_la_copia_portable_calcula_mi_empresa(tmp_path: Path) -> None:
    from tests.test_public_skill_installation import _portable_artifact

    copia = _portable_artifact(tmp_path / "escala")
    assert (copia / ".escala" / "knowledge" / "cash" / "overview.md").is_file()
    afuera = tmp_path / "carpeta-del-negocio"
    afuera.mkdir()
    salida = subprocess.run(
        [
            sys.executable,
            "-I",
            str(copia / "escala_server" / "cash" / "calcular.py"),
            str(_estados(tmp_path)),
        ],
        capture_output=True,
        text=True,
        cwd=afuera,
        check=False,
    )
    assert salida.returncode == 0, salida.stdout + salida.stderr
    datos = json.loads(salida.stdout)
    assert Decimal(_indicador(datos, "dias_clientes")["valor"]) == Decimal("46.97")
    assert Decimal(_indicador(datos, "ciclo")["valor"]) == Decimal("55.53")
