"""Dónde y cómo escribe ESCALA lo que el dueño guarda con «sí» (S86.17, S86.26).

Vive aparte del escenario para que el escenario, el perfil y los paneles lo usen
sin importarse entre sí.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

from escala_server.financial.formatos import normalizar

CARPETA = Path("work/cash")


def carpeta_de(empresa: str) -> str:
    """«Mi Empresa, S.A. de C.V.» → «mi-empresa-s-a-de-c-v»."""

    return re.sub(r"[^a-z0-9]+", "-", normalizar(empresa)).strip("-") or "empresa"


class EscrituraInsegura(Exception):
    """La ruta es un enlace simbólico: no se escribe ni se lee a través de él."""


def sin_enlace(ruta: Path) -> None:
    if ruta.is_symlink() or ruta.parent.is_symlink():
        raise EscrituraInsegura(
            f"{ruta} es un enlace simbólico; no escribo ni leo a través de un enlace"
        )


def escribir_privado(ruta: Path, texto: str, *, carpeta_privada: bool = False) -> None:
    """Escribe de forma atómica (temporal en la misma carpeta + ``os.replace``).

    El archivo queda 0o600. Con ``carpeta_privada`` la carpeta queda 0o700.
    Nunca sigue un enlace simbólico: si ``ruta`` lo es, no escribe.
    """

    ruta.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    sin_enlace(ruta)
    if carpeta_privada:
        os.chmod(ruta.parent, 0o700)
    descriptor, temporal = tempfile.mkstemp(dir=ruta.parent, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
            archivo.write(texto)
        os.chmod(temporal, 0o600)
        os.replace(temporal, ruta)  # reemplaza la entrada; no sigue enlaces
    except BaseException:
        Path(temporal).unlink(missing_ok=True)
        raise


def libre(carpeta: Path, nombre: str, extension: str = ".json") -> Path:
    """Nunca sobrescribe: la segunda versión del día es ``-2``, luego ``-3``…"""

    ruta = carpeta / f"{nombre}{extension}"
    version = 2
    while ruta.exists() or ruta.is_symlink():
        ruta = carpeta / f"{nombre}-{version}{extension}"
        version += 1
    return ruta
