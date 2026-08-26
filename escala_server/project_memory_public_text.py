"""Canonical boundary for values that may enter ScaleUp's public dialogue."""

from __future__ import annotations

import re
import unicodedata

_FORBIDDEN_TOKENS = frozenset(
    {
        "api",
        "apikey",
        "base",
        "clave",
        "comando",
        "command",
        "contrasena",
        "credential",
        "credentials",
        "database",
        "datos",
        "db",
        "habilidad",
        "id",
        "identificador",
        "log",
        "password",
        "path",
        "ruta",
        "secret",
        "secreto",
        "session",
        "sesion",
        "skill",
        "sqlite",
        "token",
    }
)
_FORBIDDEN_COMPACTS = frozenset(
    {"apikey", "apisecret", "dbpassword", "databasepassword", "secretkey", "sessionid"}
)
_PATH = re.compile(r"(?:^|[\s\"'`=:(\[])(?:/|\\|[A-Za-z]:[\\/])")


def public_text(value: object) -> str | None:
    """Return a bounded, human-safe value or nothing.

    This is deliberately conservative: it is used before proposal creation,
    context projection, and rendering, so an unsafe legacy value cannot leak
    through a later adapter.
    """
    if not isinstance(value, str):
        return None
    text = " ".join(value.strip().split())
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    normalized = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", normalized)
    normalized = "".join(
        char
        for char in unicodedata.normalize("NFKD", normalized).casefold()
        if unicodedata.category(char) != "Mn"
    )
    tokens = set(re.split(r"[^a-z0-9]+", normalized))
    compact = re.sub(r"[^a-z0-9]+", "", normalized)
    if (
        not text
        or len(text) > 240
        or tokens & _FORBIDDEN_TOKENS
        or any(form in compact for form in _FORBIDDEN_COMPACTS)
        or _PATH.search(text)
    ):
        return None
    return text
