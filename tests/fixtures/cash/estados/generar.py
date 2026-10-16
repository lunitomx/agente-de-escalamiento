"""Genera los estados sintéticos de «Mi Empresa, S.A. de C.V.» (S86.14).

Cifras: diccionarios A (2024) y B (2025) del curso de cash. La forma imita
exportaciones de CONTPAQi (activo y pasivo lado a lado; «Acumulado | %») y de
Aspel COI (código de cuenta, comparativo Dic-2025 / Dic-2024). Son datos
sintéticos: ninguna empresa real.

Cada reporte sale en tres formatos con las mismas celdas:
- ``.xlsx`` (montos numéricos; el negativo va con signo, como lo guarda Excel),
- ``.csv`` (montos como texto, el negativo entre paréntesis),
- ``.txt`` (lo que transcribiría el agente de un PDF o una foto: celdas con «|»).

Uso: ``python generar.py <carpeta destino>`` (sin dependencias externas).
"""

from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

Fila = list[str]

TITULO = "Mi Empresa, S.A. de C.V."

CONTPAQI_BALANCE: list[Fila] = [
    [TITULO],
    ["Estado de Posición Financiera al 31/Dic/2025"],
    [],
    ["ACTIVO", "", "PASIVO", ""],
    ["ACTIVO CIRCULANTE", "", "PASIVO A CORTO PLAZO", ""],
    ["Bancos", "210,291.16", "Proveedores", "1,232,468.24"],
    ["Clientes", "5,639,601.55", "Acreedores diversos", "11,846,834.45"],
    ["Inventarios", "1,771,040.54", "Préstamos bancarios a corto plazo", "148,811.41"],
    ["Otros activos circulantes", "2,527,257.34", "Total PASIVO A CORTO PLAZO", "13,228,114.10"],
    ["Total ACTIVO CIRCULANTE", "10,148,190.59", "PASIVO A LARGO PLAZO", ""],
    ["ACTIVO FIJO", "", "Documentos por pagar a largo plazo", "9,119,791.67"],
    ["Activo fijo neto", "25,318,585.22", "Préstamos bancarios a largo plazo", "5,818,564.98"],
    ["Total ACTIVO FIJO", "25,318,585.22", "Total PASIVO A LARGO PLAZO", "14,938,356.65"],
    ["ACTIVO DIFERIDO", "", "Total PASIVO", "28,166,470.75"],
    ["Activo diferido", "1,956,618.46", "CAPITAL CONTABLE", ""],
    ["Total ACTIVO DIFERIDO", "1,956,618.46", "Capital social", "2,000,000.00"],
    ["", "", "Reserva legal", "400,000.00"],
    ["", "", "Resultados de ejercicios anteriores", "1,838,827.60"],
    ["", "", "Utilidad del ejercicio", "5,018,095.92"],
    ["", "", "Total CAPITAL CONTABLE", "9,256,923.52"],
    ["Total ACTIVO", "37,423,394.27", "Total PASIVO Y CAPITAL", "37,423,394.27"],
]

CONTPAQI_RESULTADOS: list[Fila] = [
    [TITULO],
    ["Estado de Resultados del 1/Ene/2025 al 31/Dic/2025"],
    ["Concepto", "Acumulado", "%"],
    ["Ventas netas", "43,826,513.09", "100.00"],
    ["Costo de ventas", "22,966,464.00", "52.40"],
    ["Utilidad bruta", "20,860,049.09", "47.60"],
    ["Gastos de operación", "13,421,039.80", "30.62"],
    ["Utilidad de operación", "7,439,009.29", "16.97"],
    ["Gastos financieros", "1,339,211.23", "3.06"],
    ["Otros ingresos", "681,412.54", "1.55"],
    ["Utilidad antes de impuestos", "6,781,210.60", "15.47"],
    ["ISR", "1,763,114.68", "4.02"],
    ["Utilidad neta", "5,018,095.92", "11.45"],
]

ASPEL_BALANCE: list[Fila] = [
    [TITULO],
    ["Balance General comparativo"],
    ["(Cifras en pesos)"],
    ["Cuenta", "Nombre", "Dic-2025", "Dic-2024"],
    ["1000-000-000", "ACTIVO", "", ""],
    ["1100-000-000", "ACTIVO CIRCULANTE", "", ""],
    ["1101-000-000", "Caja y bancos", "210291.16", "120537.91"],
    ["1102-000-000", "Clientes", "5639601.55", "3526879.97"],
    ["1103-000-000", "Inventarios", "1771040.54", "1214882.30"],
    ["1104-000-000", "Otros activos circulantes", "2527257.34", "2398742.29"],
    ["", "Total ACTIVO CIRCULANTE", "10148190.59", "7261042.47"],
    ["1200-000-000", "Activo fijo neto", "25318585.22", "24997852.36"],
    ["1300-000-000", "Activo diferido", "1956618.46", "1753951.70"],
    ["", "Total ACTIVO", "37423394.27", "34012846.53"],
    ["2000-000-000", "PASIVO", "", ""],
    ["2100-000-000", "Proveedores", "1232468.24", "1167391.55"],
    ["2101-000-000", "Acreedores diversos", "11846834.45", "13885547.68"],
    ["2102-000-000", "Préstamos bancarios a corto plazo", "148811.41", "98756.25"],
    ["2200-000-000", "Documentos por pagar a largo plazo", "9119791.67", "9582174.13"],
    ["2201-000-000", "Préstamos bancarios a largo plazo", "5818564.98", "2073621.05"],
    ["", "Total PASIVO", "28166470.75", "26807490.66"],
    ["3000-000-000", "CAPITAL CONTABLE", "", ""],
    ["3100-000-000", "Capital contable", "9256923.52", "7205355.87"],
    ["", "Total PASIVO Y CAPITAL", "37423394.27", "34012846.53"],
]

ASPEL_RESULTADOS: list[Fila] = [
    [TITULO],
    ["Estado de Resultados comparativo"],
    ["(Cifras en pesos)"],
    ["Cuenta", "Nombre", "Dic-2025", "Dic-2024"],
    ["4100-000-000", "Ventas netas", "43826513.09", "35681743.00"],
    ["5100-000-000", "Costo de ventas", "22966464.00", "17524848.56"],
    ["6100-000-000", "Gastos de venta", "5368415.92", "4716402.95"],
    ["6200-000-000", "Gastos de administración", "8052623.88", "7074604.42"],
    ["", "Total gastos de operación", "13421039.80", "11791007.37"],
    ["", "Utilidad de operación", "7439009.29", "6365887.07"],
    ["7100-000-000", "Gastos financieros", "1339211.23", "875951.27"],
    ["7200-000-000", "Otros ingresos (venta de activos)", "681412.54", "(797135.85)"],
    ["", "Utilidad antes de impuestos", "6781210.60", "4692799.95"],
    ["7300-000-000", "ISR", "1763114.68", "1126271.99"],
    ["", "Utilidad neta", "5018095.92", "3566527.96"],
]

REPORTES: dict[str, tuple[str, list[Fila]]] = {
    "contpaqi_balance": ("Balance", CONTPAQI_BALANCE),
    "contpaqi_resultados": ("Resultados", CONTPAQI_RESULTADOS),
    "aspel_balance": ("Balance", ASPEL_BALANCE),
    "aspel_resultados": ("Resultados", ASPEL_RESULTADOS),
}

_MONTO = re.compile(r"\(?\$?\d[\d,]*(?:\.\d+)?\)?")


def _numero(celda: str) -> str | None:
    if not _MONTO.fullmatch(celda):
        return None
    limpio = celda.replace(",", "").replace("$", "")
    if limpio.startswith("(") and limpio.endswith(")"):
        return "-" + limpio[1:-1]
    return limpio


def _columna(indice: int) -> str:
    return chr(ord("A") + indice)


def _hoja_xml(filas: list[Fila]) -> str:
    renglones: list[str] = []
    for numero, fila in enumerate(filas, start=1):
        celdas: list[str] = []
        for indice, celda in enumerate(fila):
            if not celda:
                continue
            ref = f"{_columna(indice)}{numero}"
            valor = _numero(celda)
            if valor is not None:
                celdas.append(f'<c r="{ref}"><v>{valor}</v></c>')
            else:
                celdas.append(
                    f'<c r="{ref}" t="inlineStr"><is><t>{escape(celda)}</t></is></c>'
                )
        if celdas:  # Excel no guarda filas vacías: el número de renglón sí cuenta
            renglones.append(f'<row r="{numero}">{"".join(celdas)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(renglones)}</sheetData></worksheet>"
    )


def _xlsx(hoja: str, filas: list[Fila]) -> bytes:
    partes = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets><sheet name="{escape(hoja)}" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>"
        ),
        "xl/worksheets/sheet1.xml": _hoja_xml(filas),
    }
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archivo:
        for nombre, contenido in partes.items():
            info = ZipInfo(nombre, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archivo.writestr(info, contenido.encode("utf-8"))
    return buffer.getvalue()


def _csv(filas: list[Fila]) -> str:
    salida = io.StringIO()
    escritor = csv.writer(salida, lineterminator="\n")
    for fila in filas:
        escritor.writerow(fila)
    return salida.getvalue()


def _texto(filas: list[Fila]) -> str:
    lineas: list[str] = []
    for fila in filas:
        celdas = list(fila)
        while celdas and not celdas[-1]:
            celdas.pop()
        lineas.append(" | ".join(celdas))
    return "\n".join(lineas) + "\n"


def escribir(destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, (hoja, filas) in REPORTES.items():
        (destino / f"{nombre}.xlsx").write_bytes(_xlsx(hoja, filas))
        (destino / f"{nombre}.csv").write_text(_csv(filas), encoding="utf-8")
        (destino / f"{nombre}.txt").write_text(_texto(filas), encoding="utf-8")


if __name__ == "__main__":
    escribir(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
