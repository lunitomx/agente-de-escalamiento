"""Lanzador de la calculadora del curso de cash (S86.16).

Uso, en la copia de ESCALA o dentro de un paquete:

    python3 <ruta>/escala_server/cash/calcular.py <estados-revisados.json>
    python3 <ruta>/escala_server/cash/calcular.py --verifica

Sólo usa la biblioteca estándar hasta revisar que hay con qué calcular:
Python 3.10 o más nuevo y la biblioteca pydantic. Si falta algo, imprime
``{"no_calculable": "…"}`` y termina con error. ESCALA nunca hace las cuentas
de memoria.

Pone la carpeta que contiene ``escala_server`` al frente de ``sys.path``: en un
paquete, el código que corre es el que viaja en el paquete.
"""

import json
from pathlib import Path
import platform
import sys
from typing import Dict, List, Optional, Sequence, Tuple

MINIMO = (3, 10)
SIN_CON_QUE_CALCULAR = (
    "Para calcular necesito Python 3.10 o más nuevo con la biblioteca pydantic, "
    "y en esta computadora no lo encontré. No voy a hacer las cuentas de memoria."
)
RAIZ = Path(__file__).resolve().parents[2]


def revisar_python(version: Tuple[int, ...]) -> Optional[str]:
    """La razón para no calcular con esta versión de Python, o None si sirve."""

    if tuple(version[:2]) < MINIMO:
        return f"{SIN_CON_QUE_CALCULAR} (encontré Python {version[0]}.{version[1]})"
    return None


def _no(razon: str) -> int:
    print(json.dumps({"no_calculable": razon}, ensure_ascii=False))
    return 3


def _modulos_de_escala() -> Dict[str, str]:
    archivos: Dict[str, str] = {}
    for nombre, modulo in sorted(sys.modules.items()):
        if nombre == "escala_server" or nombre.startswith("escala_server."):
            archivos[nombre] = str(getattr(modulo, "__file__", "") or "")
    return archivos


def main(argv: Optional[Sequence[str]] = None) -> int:
    argumentos: List[str] = list(sys.argv[1:] if argv is None else argv)
    falta = revisar_python((sys.version_info.major, sys.version_info.minor))
    if falta is not None:
        return _no(falta)
    if str(RAIZ) not in sys.path[:1]:
        sys.path.insert(0, str(RAIZ))
    try:
        import pydantic
    except ImportError:
        return _no(f"{SIN_CON_QUE_CALCULAR} (falta pydantic)")

    from escala_server.cash import curso

    if argumentos == ["--verifica"]:
        print(
            json.dumps(
                {
                    "python": platform.python_version(),
                    "pydantic": pydantic.VERSION,
                    "calculadora": curso.__file__,
                    "modulos": _modulos_de_escala(),
                },
                ensure_ascii=False,
            )
        )
        return 0
    return curso.main(argumentos)


if __name__ == "__main__":
    raise SystemExit(main())
