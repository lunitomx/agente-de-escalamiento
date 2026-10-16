"""ESCALA lee los estados como vienen (S86.14).

El dueño manda el archivo que le dio su contador, sin arreglarlo: Excel, CSV o
el texto que el agente transcribe de un PDF o una foto. El lector devuelve
«Así leí tus cuentas»: nombre original, monto, fecha y renglón.

El lector no calcula indicadores. Sólo lee, avisa y pregunta:

- varias cuentas del mismo concepto → propone la suma y la marca
  «pide confirmación»;
- sin unidad → pregunta «¿pesos o miles de pesos?»;
- más de 90 días → avisa con la fecha (no bloquea);
- un total que difiere de su sección por dígitos invertidos → avisa.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .formatos import (
    NOMBRE_DE_CONCEPTO,
    buscar_fechas,
    concepto_de,
    contiene_frase,
    es_total,
    fecha_corta,
    fecha_larga,
    fecha_pura,
    formato_monto,
    leer_monto,
    normalizar,
    posible_digito_invertido,
)
from .profiling import read_raw_sheets

Unidad = Literal["pesos", "miles de pesos", "millones de pesos"]
DIAS_PARA_AVISAR = 90
# La utilidad ya es un resultado: dos renglones de utilidad no se suman.
_SIN_SUMA = {"utilidad_neta"}


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CuentaLeida(_Modelo):
    nombre: str
    monto: Decimal
    fecha: date | None
    renglon: int
    hoja: str
    concepto: str | None
    es_total: bool


class Aviso(_Modelo):
    codigo: Literal["estado_viejo", "posible_digito_invertido"]
    mensaje: str


class SumaPorConfirmar(_Modelo):
    concepto: str
    fecha: date | None
    nombres: tuple[str, ...]
    renglones: tuple[int, ...]
    suma: Decimal
    estado: Literal["pide confirmación"] = "pide confirmación"
    pregunta: str


class LecturaEstados(_Modelo):
    archivo: str | None = None
    cuentas: tuple[CuentaLeida, ...] = ()
    unidad: Unidad | None = None
    fecha: date | None = None
    avisos: tuple[Aviso, ...] = ()
    preguntas: tuple[str, ...] = ()
    sumas_por_confirmar: tuple[SumaPorConfirmar, ...] = ()


# ---------------------------------------------------------------------------
# Entradas
# ---------------------------------------------------------------------------


def leer_estados(ruta: Path, *, hoy: date | None = None) -> LecturaEstados:
    """Lee un archivo ``.xlsx``, ``.csv``, ``.tsv`` o ``.txt`` tal como viene."""

    if ruta.suffix.lower() in {".txt", ".md"}:
        return leer_texto(
            ruta.read_text(encoding="utf-8-sig"), hoy=hoy, hoja=ruta.stem, archivo=ruta.name
        )
    hojas = [
        _Hoja(hoja.name, [[celda.value.strip() for celda in fila] for fila in hoja.rows])
        for hoja in read_raw_sheets(ruta)
    ]
    return _leer(hojas, hoy=hoy, archivo=ruta.name)


def leer_texto(
    texto: str,
    *,
    hoy: date | None = None,
    hoja: str = "texto",
    archivo: str | None = None,
) -> LecturaEstados:
    """Lee lo que el agente transcribió de un PDF o una foto.

    Cada línea es un renglón. Las celdas van separadas por «|»; si no hay «|»,
    por un tabulador o por dos espacios o más.
    """

    filas: list[list[str]] = []
    for linea in texto.splitlines():
        if not linea.strip():
            filas.append([])
        elif "|" in linea:
            filas.append([celda.strip() for celda in linea.split("|")])
        else:
            filas.append([celda.strip() for celda in re.split(r"\t|\s{2,}", linea.strip())])
    return _leer([_Hoja(hoja, filas)], hoy=hoy, archivo=archivo)


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------


@dataclass
class _Hoja:
    nombre: str
    filas: list[list[str]]


@dataclass
class _Seccion:
    """Cuentas desde el último título o total, para revisar el siguiente total."""

    montos: list[Decimal] = field(default_factory=lambda: [])


def _tiene_letras(celda: str) -> bool:
    return re.search(r"[^\W\d_]", celda) is not None


def _es_etiqueta(celda: str) -> bool:
    return _tiene_letras(celda) and leer_monto(celda) is None and fecha_pura(celda) is None


def _encabezado_de_periodos(filas: list[list[str]]) -> tuple[int, dict[int, date]] | None:
    for indice, fila in enumerate(filas):
        columnas = {
            columna: fecha
            for columna, celda in enumerate(fila)
            if (fecha := fecha_pura(celda)) is not None
        }
        if columnas:
            return indice, columnas
    return None


def _leer(hojas: list[_Hoja], *, hoy: date | None, archivo: str | None) -> LecturaEstados:
    hoy = hoy or date.today()
    cuentas: list[CuentaLeida] = []
    avisos: list[Aviso] = []
    textos: list[str] = []
    for hoja in hojas:
        leidas, avisos_hoja, textos_hoja = _leer_hoja(hoja)
        cuentas.extend(leidas)
        avisos.extend(avisos_hoja)
        textos.extend(textos_hoja)

    unidad = _unidad(textos)
    fechas = [cuenta.fecha for cuenta in cuentas if cuenta.fecha is not None]
    fecha = max(fechas) if fechas else None
    preguntas: list[str] = []
    if unidad is None:
        preguntas.append(
            "El archivo no dice en qué vienen las cifras: ¿pesos o miles de pesos?"
        )
    if fecha is None:
        preguntas.append("¿De qué fecha son estas cifras? El archivo no la dice.")
    elif (hoy - fecha).days > DIAS_PARA_AVISAR:
        avisos.insert(
            0,
            Aviso(
                codigo="estado_viejo",
                mensaje=(
                    f"Tus cifras son al {fecha_larga(fecha)}: tienen "
                    f"{(hoy - fecha).days} días. ¿Tienes un estado más reciente? "
                    "Si no, sigo con éste."
                ),
            ),
        )
    sumas = _sumas_por_confirmar(cuentas)
    preguntas.extend(suma.pregunta for suma in sumas)
    return LecturaEstados(
        archivo=archivo,
        cuentas=tuple(cuentas),
        unidad=unidad,
        fecha=fecha,
        avisos=tuple(avisos),
        preguntas=tuple(preguntas),
        sumas_por_confirmar=sumas,
    )


def _leer_hoja(hoja: _Hoja) -> tuple[list[CuentaLeida], list[Aviso], list[str]]:
    filas = hoja.filas
    textos = [celda for fila in filas for celda in fila if _es_etiqueta(celda)]
    encabezado = _encabezado_de_periodos(filas)
    if encabezado is not None:
        lecturas = _por_periodos(filas, *encabezado)
    else:
        fechas = [f for texto in textos for f in buscar_fechas(texto)]
        lecturas = _por_pares(filas, max(fechas) if fechas else None)

    cuentas: list[CuentaLeida] = []
    avisos: list[Aviso] = []
    secciones: dict[tuple[int, date | None], _Seccion] = {}
    for renglon, columna, nombre, monto, fecha in lecturas:
        llave = (columna, fecha)
        seccion = secciones.setdefault(llave, _Seccion())
        if nombre is None or monto is None:  # título de sección: empieza otra
            secciones[llave] = _Seccion()
            continue
        total = es_total(nombre)
        cuentas.append(
            CuentaLeida(
                nombre=nombre,
                monto=monto,
                fecha=fecha,
                renglon=renglon,
                hoja=hoja.nombre,
                concepto=concepto_de(nombre),
                es_total=total,
            )
        )
        if not total:
            seccion.montos.append(monto)
            continue
        if seccion.montos:
            suma = sum(seccion.montos, Decimal("0"))
            if posible_digito_invertido(monto, suma):
                avisos.append(
                    Aviso(
                        codigo="posible_digito_invertido",
                        mensaje=(
                            f"«{nombre}» (renglón {renglon}) dice {formato_monto(monto)}, "
                            f"pero sus cuentas suman {formato_monto(suma)}. La diferencia "
                            f"({formato_monto(abs(monto - suma))}) es múltiplo de 9: puede "
                            "ser un dígito invertido. ¿Cuál es la cifra buena?"
                        ),
                    )
                )
        secciones[llave] = _Seccion()
    return cuentas, avisos, textos


# Cada lectura: (renglón, columna de la etiqueta o del periodo, nombre, monto, fecha).
# Nombre o monto en ``None`` marca un título que separa secciones.
_Lectura = tuple[int, int, str | None, Decimal | None, date | None]


def _por_periodos(
    filas: list[list[str]], encabezado: int, periodos: dict[int, date]
) -> list[_Lectura]:
    """Una columna por fecha (Aspel: «Dic-2025 | Dic-2024»)."""

    lecturas: list[_Lectura] = []
    for indice in range(encabezado + 1, len(filas)):
        fila = filas[indice]
        nombre = next((celda for celda in fila if _es_etiqueta(celda)), None)
        if nombre is None:
            continue
        for columna, fecha in periodos.items():
            celda = fila[columna] if columna < len(fila) else ""
            monto = leer_monto(celda)
            lecturas.append((indice + 1, columna, nombre, monto, fecha))
    return lecturas


def _por_pares(filas: list[list[str]], fecha: date | None) -> list[_Lectura]:
    """Cada etiqueta toma el primer monto a su derecha (CONTPAQi, lado a lado)."""

    lecturas: list[_Lectura] = []
    for indice, fila in enumerate(filas):
        pendiente: tuple[int, str] | None = None
        for columna, celda in enumerate(fila):
            if _es_etiqueta(celda):
                if pendiente is not None:
                    lecturas.append((indice + 1, pendiente[0], pendiente[1], None, fecha))
                pendiente = (columna, celda)
                continue
            monto = leer_monto(celda)
            if monto is not None and pendiente is not None:
                lecturas.append((indice + 1, pendiente[0], pendiente[1], monto, fecha))
                pendiente = None
        if pendiente is not None:
            lecturas.append((indice + 1, pendiente[0], pendiente[1], None, fecha))
    return lecturas


def _unidad(textos: list[str]) -> Unidad | None:
    for texto in textos:
        if contiene_frase(texto, "millones de pesos") or normalizar(texto) == "millones":
            return "millones de pesos"
        if contiene_frase(texto, "miles de pesos") or normalizar(texto) == "miles":
            return "miles de pesos"
    for texto in textos:
        if contiene_frase(texto, "pesos") or contiene_frase(texto, "mxn"):
            return "pesos"
    return None


def _sumas_por_confirmar(cuentas: list[CuentaLeida]) -> tuple[SumaPorConfirmar, ...]:
    grupos: dict[tuple[str, date | None], list[CuentaLeida]] = {}
    for cuenta in cuentas:
        if cuenta.es_total or cuenta.concepto is None or cuenta.concepto in _SIN_SUMA:
            continue
        grupos.setdefault((cuenta.concepto, cuenta.fecha), []).append(cuenta)
    sumas: list[SumaPorConfirmar] = []
    for (concepto, fecha), grupo in grupos.items():
        if len(grupo) < 2:
            continue
        suma = sum((cuenta.monto for cuenta in grupo), Decimal("0"))
        detalle = " + ".join(
            f"«{cuenta.nombre}» {formato_monto(cuenta.monto)}" for cuenta in grupo
        )
        cuando = f" al {fecha_corta(fecha)}" if fecha else ""
        sumas.append(
            SumaPorConfirmar(
                concepto=concepto,
                fecha=fecha,
                nombres=tuple(cuenta.nombre for cuenta in grupo),
                renglones=tuple(cuenta.renglon for cuenta in grupo),
                suma=suma,
                pregunta=(
                    f"Encontré {len(grupo)} cuentas de "
                    f"{NOMBRE_DE_CONCEPTO.get(concepto, concepto)}{cuando}: {detalle}. "
                    f"¿Las sumo como {NOMBRE_DE_CONCEPTO.get(concepto, concepto)}: "
                    f"{formato_monto(suma)}?"
                ),
            )
        )
    return tuple(sumas)


# ---------------------------------------------------------------------------
# Salida para el dueño
# ---------------------------------------------------------------------------


def render_asi_lei(lectura: LecturaEstados) -> str:
    """«Así leí tus cuentas»: nombre original, monto, fecha y renglón. Sin cálculos."""

    origen = f" de {lectura.archivo}" if lectura.archivo else ""
    unidad = lectura.unidad or "sin unidad (te pregunto abajo)"
    lineas = [
        f"Así leí tus cuentas{origen}",
        "",
        f"Unidad: {unidad}.",
        "",
        "| Cuenta | Monto | Fecha | Renglón |",
        "|---|---:|---|---:|",
    ]
    for cuenta in lectura.cuentas:
        fecha = fecha_corta(cuenta.fecha) if cuenta.fecha else "sin fecha"
        lineas.append(
            f"| {cuenta.nombre} | {formato_monto(cuenta.monto)} | {fecha} | {cuenta.renglon} |"
        )
    if lectura.sumas_por_confirmar:
        lineas.extend(["", "Sumas que propongo (pide confirmación):"])
        for suma in lectura.sumas_por_confirmar:
            cuando = f" al {fecha_corta(suma.fecha)}" if suma.fecha else ""
            lineas.append(
                f"- {NOMBRE_DE_CONCEPTO.get(suma.concepto, suma.concepto)}{cuando}: "
                f"{' + '.join(suma.nombres)} = {formato_monto(suma.suma)} — {suma.estado}"
            )
    if lectura.avisos:
        lineas.extend(["", "Avisos:"])
        lineas.extend(f"- {aviso.mensaje}" for aviso in lectura.avisos)
    preguntas = [
        pregunta
        for pregunta in lectura.preguntas
        if pregunta not in {suma.pregunta for suma in lectura.sumas_por_confirmar}
    ]
    if preguntas:
        lineas.extend(["", "Preguntas:"])
        lineas.extend(f"- {pregunta}" for pregunta in preguntas)
    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    """``python -m escala_server.financial.lector <archivo>``: imprime la lectura."""

    argumentos = sys.argv[1:] if argv is None else argv
    if len(argumentos) != 1:
        print("Uso: python -m escala_server.financial.lector <archivo>", file=sys.stderr)
        return 2
    print(render_asi_lei(leer_estados(Path(argumentos[0]))), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
