"""CORS del servidor local de ESCALA (S86.36, Seguridad).

El panel devuelve los números reales del dueño. Sólo el propio servidor local
recibe permiso de CORS: ``http://localhost:<puerto>`` y
``http://127.0.0.1:<puerto>``. Una página ajena, por ejemplo
``https://ejemplo-malo.com``, no recibe ``Access-Control-Allow-Origin`` y su
navegador no le deja leer la respuesta. Nunca se usa el comodín ``*``.
Las páginas de ``static/`` son del mismo origen: no necesitan CORS.
"""

ANFITRIONES_LOCALES = ("localhost", "127.0.0.1")


def origen_permitido(origen: str | None, puerto: int) -> bool:
    """``True`` sólo para el origen exacto del propio servidor local."""
    if not origen:
        return False
    return origen in {
        f"http://{anfitrion}:{puerto}" for anfitrion in ANFITRIONES_LOCALES
    }


class CORSHandler:
    """Cabeceras de CORS para una respuesta, según el ``Origin`` que llegó."""

    @staticmethod
    def get_headers(origen: str | None, puerto: int) -> dict[str, str]:
        cabeceras = {"Vary": "Origin"}
        if origen is None or not origen_permitido(origen, puerto):
            return cabeceras
        cabeceras.update(
            {
                "Access-Control-Allow-Origin": origen,
                "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "86400",
            }
        )
        return cabeceras
