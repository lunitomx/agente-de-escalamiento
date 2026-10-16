"""El recorrido: de los estados revisados a todos los paneles (S86.26).

Según el curso de cash que vimos, después de calcular (fase 6) ESCALA muestra
(fase 7) y luego el dueño decide (fase 8). Aquí se arman, sin escribir nada,
los paneles de las historias S86.18 a S86.25:

- Fase 7, para ver: tu contabilidad real, días y ciclo, las tres medidas.
- Fase 8, para decidir: tu perfil ideal, el simulador, precio contra volumen
  y el margen antes de impuestos.

Cada panel trae un titular corto con números que calculó Python, su página
(HTML de un archivo) y la fuente: el JSON del que sale cada número del titular.
Si un panel no sale, dice por qué; nunca pone 0.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from escala_server.cash import (
    contabilidad,
    flujo,
    panel_decision,
    panel_dias,
    panel_perfil,
    simulador,
)
from escala_server.cash.curso import (
    BaseDeDias,
    Calculado,
    EstadosRevisados,
    Indicador,
    ResultadoDelCurso,
    dias_del_dinero,
)
from escala_server.cash.perfil import (
    PerfilGuardado,
    PlaticaDelPerfil,
    atender as atender_perfil,
    leer_guardado,
    porcentajes_de_un_peso,
    valores_del_perfil,
)
from escala_server.financial.formatos import formato_monto

ClaveDePanel = Literal[
    "contabilidad", "dias", "flujo", "perfil", "simulador", "precio_volumen", "margen"
]
Estado = Literal["listo", "no sale", "falta tu respuesta"]

FASES: dict[int, str] = {
    1: "leer lo que me mandas",
    2: "decirte qué tengo y qué me falta",
    3: "preguntarte lo pendiente",
    4: "revisar que todo cuadre",
    5: "decirte qué voy a calcular",
    6: "calcular",
    7: "mostrarte tus paneles",
    8: "decidir con ellos",
}
TOTAL_DE_FASES = len(FASES)


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PanelDelRecorrido(_Modelo):
    clave: ClaveDePanel
    nombre: str
    fase: Literal[7, 8]
    estado: Estado
    titular: str
    # La página y los datos del panel: se guardan con «sí»; no van en la salida.
    pagina: str | None = Field(default=None, exclude=True)
    fuente: str = Field(default="", exclude=True)


def _monto(valor: Calculado) -> str:
    texto = formato_monto(abs(valor.valor))
    return f"−{texto}" if valor.valor < 0 else texto


def _no_sale(
    clave: ClaveDePanel, nombre: str, fase: Literal[7, 8], razon: str
) -> PanelDelRecorrido:
    return PanelDelRecorrido(
        clave=clave,
        nombre=nombre,
        fase=fase,
        estado="no sale",
        titular=f"no calculable: {razon}",
    )


# ---------------------------------------------------------------------------
# Fase 7: para ver
# ---------------------------------------------------------------------------


def _contabilidad(estados: EstadosRevisados) -> PanelDelRecorrido:
    nombre = "Tu contabilidad real"
    panel = contabilidad.panel_de(estados)
    if panel.no_calculable is not None or not panel.balances:
        return _no_sale(
            "contabilidad", nombre, 7, panel.no_calculable or "no hay balance"
        )
    if panel.preguntas:
        return PanelDelRecorrido(
            clave="contabilidad",
            nombre=nombre,
            fase=7,
            estado="falta tu respuesta",
            titular=f"Antes de pintarlo necesito que me aclares esto: {panel.preguntas[0].pregunta}",
            fuente=panel.model_dump_json(),
        )
    ordenados = sorted(panel.balances, key=lambda b: b.fecha)
    final = ordenados[-1]
    titular = final.frase
    if len(ordenados) > 1:
        titular += (
            f" Tu deuda neta pasó de {_monto(ordenados[0].deuda_neta.total)} "
            f"a {_monto(final.deuda_neta.total)}."
        )
    return PanelDelRecorrido(
        clave="contabilidad",
        nombre=nombre,
        fase=7,
        estado="listo",
        titular=titular,
        pagina=contabilidad.pagina(panel),
        fuente=panel.model_dump_json(),
    )


def _dias(estados: EstadosRevisados, base: BaseDeDias) -> PanelDelRecorrido:
    nombre = "Días y ciclo del dinero"
    dias = dias_del_dinero(estados, base)
    if dias.no_calculable is not None:
        return _no_sale("dias", nombre, 7, dias.no_calculable)
    textos = [c.texto for c in dias.cambios]
    if not textos:
        textos = [
            f"{a.ciclo.nombre} al {a.fecha.isoformat()}: {_monto(a.ciclo)} días."
            for a in dias.anios
            if isinstance(a.ciclo, Calculado)
        ]
    titular = " ".join(textos) + f" ({dias.rotulo})."
    return PanelDelRecorrido(
        clave="dias",
        nombre=nombre,
        fase=7,
        estado="listo",
        titular=titular,
        pagina=panel_dias.pagina(dias),
        fuente=dias.model_dump_json(),
    )


def _flujo(estados: EstadosRevisados) -> PanelDelRecorrido:
    nombre = "Las tres medidas del flujo"
    panel = flujo.panel_de(estados)
    if panel.no_calculable is not None:
        return _no_sale("flujo", nombre, 7, panel.no_calculable)
    if panel.preguntas:
        return PanelDelRecorrido(
            clave="flujo",
            nombre=nombre,
            fase=7,
            estado="falta tu respuesta",
            titular=f"Antes de pintarlo necesito que me aclares esto: {panel.preguntas[0].pregunta}",
            fuente=panel.model_dump_json(),
        )
    return PanelDelRecorrido(
        clave="flujo",
        nombre=nombre,
        fase=7,
        estado="listo",
        titular=panel.frase,
        pagina=flujo.pagina(panel),
        fuente=panel.model_dump_json(),
    )


# ---------------------------------------------------------------------------
# Fase 8: para decidir
# ---------------------------------------------------------------------------

SIN_LIMITES = (
    "Para pintar tu semáforo primero te pregunto tus límites: tu ideal, desde dónde "
    "es verde y desde dónde es rojo. No pinto colores con límites que no son tuyos."
)


def _perfil(
    estados: EstadosRevisados, base: BaseDeDias, empresa: str, carpeta: Path
) -> PanelDelRecorrido:
    nombre = "Tu perfil ideal"
    guardado = leer_guardado(empresa, carpeta=carpeta)
    if isinstance(guardado, str):
        return _no_sale("perfil", nombre, 8, guardado)
    if guardado is None:
        return PanelDelRecorrido(
            clave="perfil",
            nombre=nombre,
            fase=8,
            estado="falta tu respuesta",
            titular=SIN_LIMITES,
        )
    return _perfil_con_limites(estados, base, empresa, guardado)


def _perfil_con_limites(
    estados: EstadosRevisados, base: BaseDeDias, empresa: str, guardado: PerfilGuardado
) -> PanelDelRecorrido:
    nombre = "Tu perfil ideal"
    paso = atender_perfil(
        PlaticaDelPerfil(empresa=empresa),
        valores_del_perfil(estados, base),
        porcentajes_de_un_peso(estados),
        guardado=guardado,
    )
    if not paso.pintar:
        return PanelDelRecorrido(
            clave="perfil",
            nombre=nombre,
            fase=8,
            estado="falta tu respuesta",
            titular=SIN_LIMITES,
            fuente=paso.model_dump_json(),
        )
    colores = [
        f"{t.nombre}: {t.color}" if t.color is not None else f"{t.nombre}: sin color"
        for t in paso.tarjetas
    ]
    return PanelDelRecorrido(
        clave="perfil",
        nombre=nombre,
        fase=8,
        estado="listo",
        titular="Tu semáforo con tus límites guardados. " + "; ".join(colores) + ".",
        pagina=panel_perfil.pagina(paso),
        fuente=paso.model_dump_json(),
    )


def _simulador(calculo: ResultadoDelCurso) -> PanelDelRecorrido:
    nombre = "Simulador"
    sim = simulador.simulador_de(calculo)
    if sim.no_calculable is not None:
        return _no_sale("simulador", nombre, 8, sim.no_calculable)
    efectivo, utilidad = calculo.poder_del_uno_flujo, calculo.poder_del_uno_utilidad
    if isinstance(efectivo, Calculado) and isinstance(utilidad, Calculado):
        titular = (
            f"Si mejoras un punto cada palanca (precio, volumen, costo, gastos y tus días), "
            f"tu efectivo mejora {_monto(efectivo)} y tu utilidad {_monto(utilidad)} "
            f"({sim.rotulo}). En la página mueves cada palanca."
        )
    else:
        titular = f"Mueve cada palanca y ve cuánto cambia tu utilidad ({sim.rotulo})."
    fuente = sim.model_dump_json() + (efectivo.model_dump_json() if efectivo else "")
    fuente += utilidad.model_dump_json() if utilidad else ""
    return PanelDelRecorrido(
        clave="simulador",
        nombre=nombre,
        fase=8,
        estado="listo",
        titular=titular,
        pagina=simulador.pagina(sim),
        fuente=fuente,
    )


def _precio_volumen(calculo: ResultadoDelCurso) -> PanelDelRecorrido:
    nombre = "Precio contra volumen"
    pv = calculo.precio_contra_volumen
    if pv is None:
        return _no_sale("precio_volumen", nombre, 8, "la calculadora no lo trae")
    if pv.no_calculable is not None:
        return _no_sale("precio_volumen", nombre, 8, pv.no_calculable)
    return PanelDelRecorrido(
        clave="precio_volumen",
        nombre=nombre,
        fase=8,
        estado="listo",
        titular=" ".join(pv.mensajes),
        pagina=panel_decision.pagina_precio_volumen(pv),
        fuente=pv.model_dump_json(),
    )


def _porcentaje(indicador: Indicador) -> str | None:
    return f"{_monto(indicador)}%" if isinstance(indicador, Calculado) else None


def _margen(calculo: ResultadoDelCurso) -> PanelDelRecorrido:
    nombre = "Margen antes de impuestos"
    margen = calculo.margen
    if margen is None:
        return _no_sale("margen", nombre, 8, "la calculadora no lo trae")
    pretax = _porcentaje(margen.pretax)
    if pretax is None:
        razon = getattr(margen.pretax, "no_calculable", None) or getattr(
            margen.pretax, "no_aplica", "no sale"
        )
        return _no_sale("margen", nombre, 8, str(razon))
    lado = "llega a" if margen.por_encima_de_la_linea else "queda abajo de"
    partes = [
        f"Tu margen antes de impuestos es {pretax}: {lado} la línea de referencia "
        f"del {margen.linea_de_referencia}%."
    ]
    con_salario = _porcentaje(margen.pretax_con_salario)
    if con_salario is not None:
        partes.append(
            f"Con el salario de mercado que me diste, queda en {con_salario}."
        )
    devoluciones = _porcentaje(margen.devoluciones)
    if devoluciones is not None:
        partes.append(
            f"Tus devoluciones equivalen a {devoluciones} de tu utilidad antes de impuestos."
        )
    return PanelDelRecorrido(
        clave="margen",
        nombre=nombre,
        fase=8,
        estado="listo",
        titular=" ".join(partes),
        pagina=panel_decision.pagina_margen(margen),
        fuente=margen.model_dump_json(),
    )


def paneles_del_recorrido(
    estados: EstadosRevisados,
    calculo: ResultadoDelCurso,
    *,
    empresa: str,
    carpeta: Path,
) -> tuple[PanelDelRecorrido, ...]:
    """Los 7 paneles, en orden: primero los de ver (fase 7), luego los de decidir (fase 8)."""
    base = BaseDeDias.de(estados.respuestas)
    return (
        _contabilidad(estados),
        _dias(estados, base),
        _flujo(estados),
        _perfil(estados, base, empresa, carpeta),
        _simulador(calculo),
        _precio_volumen(calculo),
        _margen(calculo),
    )
