"""La nota de Cash del panel de control, desde el recorrido de cash (S86.36).

Lee lo que el dueño guardó con «sí» en ``work/cash/<empresa>/``:

- el último ``estados-revisados-<fecha>[-N].json`` (``cash.escenario.guardar``);
- ``perfil-ideal.json`` con sus límites, si lo guardó (``cash.perfil``).

Los números los vuelve a sacar la calculadora (``calcular_curso``,
``dias_del_dinero``, ``valores_del_perfil``). Aquí no se calcula ningún
indicador ni se inventa un límite.

La regla de la nota:

- Sin recorrido guardado: no hay nota. «Sin datos: corre el recorrido de cash».
- Sin perfil ideal: los valores van sin color y sin nota. «Falta tu perfil ideal».
- Con perfil: cada indicador con límite lleva el color de los límites del dueño.
  Nota = indicadores en verde ÷ indicadores pintados × 100.
  Ejemplo: 3 de 6 en verde → 50. Rojo si alguno está en rojo; verde si todos.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from escala_server.cash.archivos import CARPETA, EscrituraInsegura, sin_enlace
from escala_server.cash.curso import (
    BaseDeDias,
    Calculado,
    EstadosRevisados,
    NoCalculable,
    calcular_curso,
    dias_del_dinero,
)
from escala_server.cash.perfil import (
    Color,
    Limites,
    PerfilGuardado,
    ValorDelPerfil,
    ValorOSin,
    color,
    leer_guardado,
    valores_del_perfil,
)
from escala_server.financial.formatos import formato_monto

SIN_RECORRIDO = "Sin datos: corre el recorrido de cash (/escala-cash)"
FALTA_PERFIL = (
    "Tus números de cash, sin color: falta tu perfil ideal. "
    "Fija tus límites en el recorrido de cash (/escala-cash)."
)
_ARCHIVO = re.compile(r"^estados-revisados-(\d{4}-\d{2}-\d{2})(?:-(\d+))?\.json$")

Estado = Literal["sin_datos", "sin_perfil", "con_perfil"]
Status = Literal["good", "warning", "critical", "missing"]


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LineaDeLaNota(_Modelo):
    clave: str
    nombre: str
    valor: Decimal | None = None  # el valor que se lee (2 decimales)
    unidad: str
    texto: str
    sale_de: str
    color: Color | None = None


class NotaDeCash(_Modelo):
    estado: Estado
    texto: str
    empresa: str | None = None
    archivo: str | None = None
    nota: int | None = None
    status: Status = "missing"
    verdes: int = 0
    pintados: int = 0
    sale_de: str | None = None
    lineas: tuple[LineaDeLaNota, ...] = ()

    def para_el_panel(self) -> dict[str, object]:
        """La forma que espera ``/api/dashboard/summary``."""
        return {
            "score": self.nota,
            "status": self.status,
            "label": self.texto,
            "sale_de": self.sale_de,
            "siguiente": None if self.estado == "con_perfil" else self.texto,
            "empresa": self.empresa,
            "archivo": self.archivo,
            "lineas": [linea.model_dump(mode="json") for linea in self.lineas],
        }


def _ultimo(carpeta: Path) -> Path | None:
    """El ``estados-revisados`` más nuevo: fecha del nombre, luego versión (-2, -3…)."""
    if not carpeta.is_dir() or carpeta.is_symlink():
        return None
    candidatos: list[tuple[date, int, str, Path]] = []
    for empresa in carpeta.iterdir():
        if empresa.is_symlink() or not empresa.is_dir():
            continue
        for archivo in empresa.iterdir():
            encontrado = _ARCHIVO.match(archivo.name)
            if encontrado is None or archivo.is_symlink():
                continue
            fecha = date.fromisoformat(encontrado.group(1))
            version = int(encontrado.group(2) or 1)
            candidatos.append((fecha, version, empresa.name, archivo))
    if not candidatos:
        return None
    return max(candidatos, key=lambda c: (c[0], c[1], c[2]))[3]


def _sin_datos(texto: str = SIN_RECORRIDO) -> NotaDeCash:
    return NotaDeCash(estado="sin_datos", texto=texto)


def _linea_calculada(indicador: Calculado, unidad: str) -> LineaDeLaNota:
    numero = formato_monto(indicador.valor)
    texto = f"{numero} días" if unidad == "días" else numero
    return LineaDeLaNota(
        clave=indicador.clave,
        nombre=indicador.nombre,
        valor=indicador.valor,
        unidad=unidad,
        texto=f"{indicador.nombre}: {texto}",
        sale_de=f"sale de: {indicador.formula}; {indicador.origen}",
    )


def _linea_no_calculable(clave: str, nombre: str, razon: str) -> LineaDeLaNota:
    return LineaDeLaNota(
        clave=clave,
        nombre=nombre,
        unidad="",
        texto=f"{nombre}: no calculable",
        sale_de=f"sale de: no calculable: {razon}",
    )


def nota_de_cash(carpeta: Path = CARPETA) -> NotaDeCash:
    """La nota de Cash con lo último que el dueño guardó en ``carpeta``."""
    archivo = _ultimo(carpeta)
    if archivo is None:
        return _sin_datos()
    try:
        sin_enlace(archivo)
        estados = EstadosRevisados.model_validate_json(
            archivo.read_text(encoding="utf-8")
        )
    except (EscrituraInsegura, OSError, ValidationError):
        return _sin_datos(f"Sin datos: no pude leer {archivo.as_posix()}")
    empresa = archivo.parent.name
    calculo = calcular_curso(estados)
    final = estados.revision.balance_final
    if calculo.no_calculable is not None or final is None:
        razon = calculo.no_calculable or "falta el balance al final del periodo"
        return _sin_datos(f"Sin datos: no calculable: {razon}")

    lineas: list[LineaDeLaNota] = []
    base = BaseDeDias.de(estados.respuestas)
    dias = dias_del_dinero(estados, base)
    anio = next((a for a in dias.anios if a.fecha == final), None)
    ciclo = anio.ciclo if anio is not None else None
    if isinstance(ciclo, Calculado):
        lineas.append(_linea_calculada(ciclo, "días"))
    else:
        razon = (
            ciclo.no_calculable
            if isinstance(ciclo, NoCalculable)
            else dias.no_calculable or "sin valor"
        )
        lineas.append(_linea_no_calculable("ciclo", "Ciclo del efectivo", razon))

    valores = valores_del_perfil(estados, base)
    por_clave: dict[str, ValorOSin] = {valor.clave: valor for valor in valores}
    for clave in ("dias_clientes", "dias_inventario", "dias_proveedores"):
        lineas.append(_linea_del_perfil(por_clave[clave]))

    flujo = calculo.indicador("flujo_neto", final)
    if isinstance(flujo, Calculado):
        lineas.append(_linea_calculada(flujo, "pesos"))
    else:
        razon = (
            flujo.no_calculable if isinstance(flujo, NoCalculable) else flujo.no_aplica
        )
        lineas.append(_linea_no_calculable("flujo_neto", flujo.nombre, razon))

    for clave in ("utilidad_bruta", "gastos", "utilidad_de_operacion"):
        lineas.append(_linea_del_perfil(por_clave[clave]))

    base_nota = NotaDeCash(
        estado="sin_perfil",
        texto=FALTA_PERFIL,
        empresa=empresa,
        archivo=archivo.as_posix(),
        lineas=tuple(lineas),
    )
    perfil = leer_guardado(empresa, carpeta=carpeta)
    if perfil is None:
        return base_nota
    if isinstance(perfil, str):
        return base_nota.model_copy(update={"texto": f"{FALTA_PERFIL} ({perfil})"})
    return _con_perfil(base_nota, perfil, por_clave)


def _linea_del_perfil(valor: ValorOSin) -> LineaDeLaNota:
    if isinstance(valor, ValorDelPerfil):
        numero = formato_monto(valor.mostrado)
        texto = f"{numero}%" if valor.unidad == "%" else f"{numero} días"
        return LineaDeLaNota(
            clave=valor.clave,
            nombre=valor.nombre,
            valor=valor.mostrado,
            unidad=valor.unidad,
            texto=f"{valor.nombre}: {texto}",
            sale_de=valor.origen,
        )
    return LineaDeLaNota(
        clave=valor.clave,
        nombre=valor.nombre,
        unidad=valor.unidad,
        texto=f"{valor.nombre}: {valor.razon}",
        sale_de=f"sale de: {valor.razon}",
    )


def _con_perfil(
    nota: NotaDeCash,
    perfil: PerfilGuardado,
    por_clave: dict[str, ValorOSin],
) -> NotaDeCash:
    limites_por: dict[str, Limites] = {
        clave: lim for clave, lim in perfil.limites.items()
    }
    lineas: list[LineaDeLaNota] = []
    colores: list[Color] = []
    for linea in nota.lineas:
        valor = por_clave.get(linea.clave)
        limites = limites_por.get(linea.clave)
        if isinstance(valor, ValorDelPerfil) and limites is not None:
            pinta = color(valor.clave, valor.valor, limites)
            colores.append(pinta)
            linea = linea.model_copy(update={"color": pinta})
        lineas.append(linea)
    if not colores:
        return nota
    verdes = colores.count("verde")
    pintados = len(colores)
    calificacion = int(
        (Decimal(100 * verdes) / pintados).quantize(Decimal("1"), ROUND_HALF_UP)
    )
    status: Status = (
        "critical" if "rojo" in colores else "good" if verdes == pintados else "warning"
    )
    sale_de = (
        f"sale de: {verdes} de {pintados} indicadores en verde con tus límites "
        f"(perfil ideal guardado el {perfil.guardado.isoformat()}) × 100"
    )
    return nota.model_copy(
        update={
            "estado": "con_perfil",
            "texto": f"{verdes} de {pintados} en verde con tu perfil ideal",
            "nota": calificacion,
            "status": status,
            "verdes": verdes,
            "pintados": pintados,
            "sale_de": sale_de,
            "lineas": tuple(lineas),
        }
    )
