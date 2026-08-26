"""Canonical boundary for values that may enter ScaleUp's public dialogue."""

from __future__ import annotations

import re
import unicodedata

_FORBIDDEN_TOKENS = frozenset(
    {
        "api",
        "apikey",
        "clave",
        "comando",
        "command",
        "contrasena",
        "credential",
        "credentials",
        "database",
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
_FORBIDDEN_TOKEN_PHRASES = frozenset(
    {
        ("base", "de", "datos"),
        ("clave", "de", "acceso"),
        ("access", "key"),
    }
)
_LEGITIMATE_BUSINESS_TOKEN_PHRASES = frozenset(
    {
        ("indicador", "clave", "de", "ventas"),
    }
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
    token_sequence = tuple(
        token for token in re.split(r"[^a-z0-9]+", normalized) if token
    )
    tokens = set(token_sequence)
    compact = re.sub(r"[^a-z0-9]+", "", normalized)
    has_legitimate_business_phrase = any(
        token_sequence[index : index + len(phrase)] == phrase
        for phrase in _LEGITIMATE_BUSINESS_TOKEN_PHRASES
        for index in range(len(token_sequence) - len(phrase) + 1)
    )
    forbidden_tokens = tokens & _FORBIDDEN_TOKENS
    if has_legitimate_business_phrase:
        forbidden_tokens.discard("clave")
    has_forbidden_phrase = any(
        token_sequence[index : index + len(phrase)] == phrase
        for phrase in _FORBIDDEN_TOKEN_PHRASES
        for index in range(len(token_sequence) - len(phrase) + 1)
    )
    if (
        not text
        or len(text) > 240
        or forbidden_tokens
        or any(form in compact for form in _FORBIDDEN_COMPACTS)
        or has_forbidden_phrase
        or _PATH.search(text)
    ):
        return None
    return text
