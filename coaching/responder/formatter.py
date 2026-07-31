"""coaching.responder.formatter — markdown renderer for executive responses.

No I/O. Renders the five-block executive response as user-facing markdown.
"""

from __future__ import annotations

from .models import ExecutiveResponse


def format_response(response: ExecutiveResponse) -> str:
    """Render an ExecutiveResponse as the five-block markdown output."""
    lines = [
        "## Respuesta ejecutiva",
        "",
        "### 1. Qué veo",
        response.what_i_see,
        "",
        "### 2. Por qué importa",
        response.why_it_matters,
        "",
        "### 3. Evidencia relevante",
    ]

    if response.evidence:
        for item in response.evidence:
            lines.append(f"- {item}")
    else:
        lines.append("- No hay evidencia relevante disponible.")

    lines.extend(
        [
            "",
            "### 4. Qué no sé todavía",
            response.what_i_dont_know,
            "",
            "### 5. Acción recomendada",
            response.next_step,
            "",
        ]
    )

    return "\n".join(lines)
