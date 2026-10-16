"""Cómo vienen los estados financieros en México: nombres, montos y fechas (S86.14).

Reglas compartidas por el lector nuevo (``lector.py``) y el de E38
(``profiling.py``, ``statements.py``):

- un nombre coincide con un concepto sólo por palabra completa y con lista de
  exclusiones («Costo de ventas» no es «ventas»);
- un monto puede venir con ``$``, comas o entre paréntesis («(797,135.85)» es
  negativo);
- una fecha puede venir como «2025-12», «Dic-2025», «31/12/2025»,
  «31/Dic/2025» o «al 31 de diciembre de 2025».

Aquí no se calcula ningún indicador.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

# ---------------------------------------------------------------------------
# Nombres
# ---------------------------------------------------------------------------


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y con un solo espacio entre palabras."""

    descompuesto = unicodedata.normalize("NFKD", texto.casefold())
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_acentos.split())


def palabras(texto: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", normalizar(texto)))


def contiene_frase(texto: str, frase: str) -> bool:
    """¿``texto`` contiene ``frase`` como palabras completas y seguidas?"""

    tokens = palabras(texto)
    buscadas = palabras(frase)
    if not buscadas:
        return False
    largo = len(buscadas)
    return any(
        tokens[inicio : inicio + largo] == buscadas
        for inicio in range(len(tokens) - largo + 1)
    )


@dataclass(frozen=True)
class _Concepto:
    nombres: tuple[str, ...]
    exclusiones: tuple[str, ...] = ()


# Conceptos que el flujo de efectivo necesita (S86.15/S86.16 los acomodan).
CONCEPTOS: dict[str, _Concepto] = {
    "ventas": _Concepto(
        ("ventas netas", "ventas", "ingresos por ventas", "ventas totales"),
        (
            "costo",
            "devoluciones",
            "descuentos",
            "rebajas",
            "gastos de venta",
            "gastos de ventas",
            "venta de activos",
        ),
    ),
    "costo_ventas": _Concepto(("costo de ventas", "costo de venta", "costo de lo vendido")),
    "gastos_operacion": _Concepto(
        (
            "gastos de operacion",
            "gastos operativos",
            "gastos de venta",
            "gastos de ventas",
            "gastos de administracion",
            "gastos generales",
        )
    ),
    "intereses": _Concepto(
        ("gastos financieros", "intereses", "costo financiero"),
        ("a favor", "productos financieros", "ganados"),
    ),
    "isr": _Concepto(("isr", "impuesto sobre la renta", "impuestos a la utilidad")),
    "utilidad_neta": _Concepto(
        ("utilidad neta", "utilidad del ejercicio", "resultado del ejercicio"),
        ("anteriores",),
    ),
    "bancos": _Concepto(("caja y bancos", "bancos", "caja", "efectivo")),
    "clientes": _Concepto(
        ("clientes", "cuentas por cobrar"), ("anticipo", "anticipos")
    ),
    "inventario": _Concepto(("inventarios", "inventario", "almacen")),
    "proveedores": _Concepto(
        ("proveedores", "cuentas por pagar"), ("anticipo", "anticipos")
    ),
    "acreedores": _Concepto(("acreedores diversos", "acreedores")),
    "prestamos_cp": _Concepto(
        (
            "prestamos bancarios a corto plazo",
            "prestamos a corto plazo",
            "creditos bancarios a corto plazo",
        )
    ),
    "documentos_lp": _Concepto(("documentos por pagar a largo plazo",)),
    "prestamos_lp": _Concepto(
        (
            "prestamos bancarios a largo plazo",
            "prestamos a largo plazo",
            "creditos bancarios a largo plazo",
        )
    ),
}

NOMBRE_DE_CONCEPTO: dict[str, str] = {
    "ventas": "ventas",
    "costo_ventas": "costo de ventas",
    "gastos_operacion": "gastos de operación",
    "intereses": "gastos financieros",
    "isr": "ISR",
    "utilidad_neta": "utilidad neta",
    "bancos": "bancos",
    "clientes": "clientes",
    "inventario": "inventario",
    "proveedores": "proveedores",
    "acreedores": "acreedores",
    "prestamos_cp": "préstamos a corto plazo",
    "documentos_lp": "documentos por pagar a largo plazo",
    "prestamos_lp": "préstamos a largo plazo",
}


def coincide(nombre: str, frases: tuple[str, ...], exclusiones: tuple[str, ...] = ()) -> int:
    """Largo (en palabras) de la frase más larga que coincide; 0 si ninguna.

    Si el nombre trae una exclusión, no coincide aunque traiga la frase.
    """

    if any(contiene_frase(nombre, excluida) for excluida in exclusiones):
        return 0
    return max(
        (len(palabras(frase)) for frase in frases if contiene_frase(nombre, frase)),
        default=0,
    )


def concepto_de(nombre: str) -> str | None:
    """Concepto de una cuenta por palabra completa; ``None`` si no hay o si se excluye."""

    mejor: tuple[int, str] | None = None
    for concepto, regla in CONCEPTOS.items():
        largo = coincide(nombre, regla.nombres, regla.exclusiones)
        if largo and (mejor is None or largo > mejor[0]):
            mejor = (largo, concepto)
    return mejor[1] if mejor else None


def es_total(nombre: str) -> bool:
    tokens = palabras(nombre)
    return bool(tokens) and tokens[0] in {"total", "totales", "suma"}


# ---------------------------------------------------------------------------
# Montos
# ---------------------------------------------------------------------------

_MONTO = re.compile(
    r"^(?P<menos>-)?\s*\$?\s*(?P<abre>\()?\s*\$?\s*(?P<menos2>-)?\s*"
    r"(?P<entero>\d{1,3}(?:,\d{3})+|\d+)(?P<decimales>\.\d+)?\s*(?P<cierra>\))?$"
)


def leer_monto(texto: str) -> Decimal | None:
    """Monto de una celda: ``$``, comas y paréntesis (negativo). ``None`` si no es monto."""

    coincidencia = _MONTO.match(texto.strip())
    if coincidencia is None:
        return None
    if bool(coincidencia["abre"]) != bool(coincidencia["cierra"]):
        return None
    decimales = coincidencia["decimales"] or ""
    cifra = coincidencia["entero"].replace(",", "") + decimales
    try:
        valor = Decimal(cifra)
        if len(decimales) > 7:  # «13421039.800000001»: así guarda Excel un flotante
            valor = Decimal(repr(float(cifra)))
    except (InvalidOperation, ValueError):
        return None
    negativo = bool(coincidencia["abre"]) or bool(coincidencia["menos"]) or bool(
        coincidencia["menos2"]
    )
    return -valor if negativo else valor


def formato_monto(valor: Decimal) -> str:
    return f"{valor:,.2f}"


# ---------------------------------------------------------------------------
# Fechas
# ---------------------------------------------------------------------------

MESES: dict[str, int] = {
    "ene": 1, "enero": 1, "jan": 1, "january": 1,
    "feb": 2, "febrero": 2, "february": 2,
    "mar": 3, "marzo": 3, "march": 3,
    "abr": 4, "abril": 4, "apr": 4, "april": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "junio": 6, "june": 6,
    "jul": 7, "julio": 7, "july": 7,
    "ago": 8, "agosto": 8, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "septiembre": 9, "setiembre": 9, "september": 9,
    "oct": 10, "octubre": 10, "october": 10,
    "nov": 11, "noviembre": 11, "november": 11,
    "dic": 12, "diciembre": 12, "dec": 12, "december": 12,
}  # fmt: skip
_ABREVIADO = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
_COMPLETO = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)  # fmt: skip

_MES = "|".join(sorted(MESES, key=len, reverse=True))
_ANIO = r"(?:19|20)\d{2}"
# Orden: primero las formas con día, luego mes y año; cada hallazgo se borra.
_PATRONES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("dma", re.compile(rf"(?<!\d)(\d{{1,2}})\s*[/.-]\s*(\d{{1,2}}|{_MES})\s*[/.-]\s*({_ANIO})(?!\d)")),
    ("dma", re.compile(rf"(?<!\d)(\d{{1,2}})\s+de\s+({_MES})\s+(?:de|del)\s+({_ANIO})(?!\d)")),
    ("amd", re.compile(rf"(?<!\d)({_ANIO})[/-](\d{{1,2}})(?:[/-](\d{{1,2}}))?(?![\d/-])")),
    ("ma", re.compile(rf"(?<![a-z])({_MES})\s*[/.-]?\s*(?:de\s+|del\s+)?({_ANIO})(?!\d)")),
)
_RELLENO = {"al", "a", "de", "del", "saldo", "saldos", "periodo", "ejercicio", "cierre", "y"}


@dataclass(frozen=True)
class _Fecha:
    fecha: date
    con_dia: bool


def _mes(texto: str) -> int | None:
    if texto.isdigit():
        mes = int(texto)
        return mes if 1 <= mes <= 12 else None
    return MESES.get(texto)


def _armar(anio: int, mes: int | None, dia: int | None) -> _Fecha | None:
    if mes is None:
        return None
    ultimo = calendar.monthrange(anio, mes)[1]
    if dia is None:
        return _Fecha(date(anio, mes, ultimo), con_dia=False)
    if not 1 <= dia <= ultimo:
        return None
    return _Fecha(date(anio, mes, dia), con_dia=True)


def _fechas_y_resto(texto: str) -> tuple[list[_Fecha], str]:
    resto = normalizar(texto)
    halladas: list[_Fecha] = []
    for forma, patron in _PATRONES:
        while (encontrada := patron.search(resto)) is not None:
            grupos = encontrada.groups()
            if forma == "dma":
                fecha = _armar(int(grupos[2]), _mes(grupos[1]), int(grupos[0]))
            elif forma == "amd":
                dia = int(grupos[2]) if grupos[2] else None
                fecha = _armar(int(grupos[0]), _mes(grupos[1]), dia)
            else:
                fecha = _armar(int(grupos[1]), _mes(grupos[0]), None)
            if fecha is not None:
                halladas.append(fecha)
            inicio, fin = encontrada.span()
            # Se borra aunque no sea fecha válida, para no volver a encontrarla.
            resto = resto[:inicio] + " \x00 " * (fecha is None) + " " + resto[fin:]
    return halladas, resto


def buscar_fechas(texto: str) -> list[date]:
    """Todas las fechas del texto. Un mes sin día cuenta como su último día."""

    return [hallada.fecha for hallada in _fechas_y_resto(texto)[0]]


def _fecha_pura(texto: str) -> _Fecha | None:
    halladas, resto = _fechas_y_resto(texto)
    if len(halladas) != 1:
        return None
    sobrante = [p for p in re.findall(r"[a-z0-9\x00]+", resto) if p not in _RELLENO]
    return halladas[0] if not sobrante else None


def fecha_pura(texto: str) -> date | None:
    """Fecha de una celda que sólo es fecha («Dic-2025», «Saldo al 31/12/2025»)."""

    hallada = _fecha_pura(texto)
    return hallada.fecha if hallada else None


def periodo_iso(texto: str) -> str | None:
    """«Dic-2025» → «2025-12»; «31/12/2025» → «2025-12-31». ``None`` si no es fecha."""

    hallada = _fecha_pura(texto)
    if hallada is None:
        return None
    if hallada.con_dia:
        return hallada.fecha.isoformat()
    return f"{hallada.fecha.year:04d}-{hallada.fecha.month:02d}"


def fecha_corta(fecha: date) -> str:
    return f"{fecha.day:02d}-{_ABREVIADO[fecha.month - 1]}-{fecha.year}"


def fecha_larga(fecha: date) -> str:
    return f"{fecha.day} de {_COMPLETO[fecha.month - 1]} de {fecha.year}"


# ---------------------------------------------------------------------------
# Dígito invertido
# ---------------------------------------------------------------------------


def posible_digito_invertido(total: Decimal, suma: Decimal) -> bool:
    """¿El total y la suma difieren como cuando se invierten dos dígitos?

    Dos dígitos invertidos dejan una diferencia múltiplo de 9 y los mismos
    dígitos: 97,942 contra 97,492 (diferencia 450 = 9 × 50).
    """

    if total == suma:
        return False
    centavos_total = (abs(total) * 100).to_integral_value()
    centavos_suma = (abs(suma) * 100).to_integral_value()
    if (centavos_total - centavos_suma) % 9 != 0:
        return False
    return sorted(str(int(centavos_total))) == sorted(str(int(centavos_suma)))
