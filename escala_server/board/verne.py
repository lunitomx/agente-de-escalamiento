"""Deterministic synthetic advisor grounded in an EvidencePacket."""

from __future__ import annotations

from .contracts import SCHEMA_VERSION, AdviceItem, BoardResponse, EvidencePacket

DISCLOSURE = (
    "Esta es una lente sintética basada en Scaling Up; no es Verne Harnish, "
    "no habla en su nombre ni implica su participación o respaldo."
)


def validate_profile(path: str) -> list[str]:
    """Validate the versioned, non-impersonating board profile."""
    try:
        with open(path, encoding="utf-8") as handle:
            value = handle.read()
    except OSError as error:
        return [f"profile unreadable: {error}"]
    required = (
        "lente sintética",
        "No es Verne Harnish",
        "no implica su participación",
        "People",
        "Strategy",
        "Execution",
        "Cash",
        "Línea fuente",
    )
    return [
        f"missing profile requirement: {item}"
        for item in required
        if item.casefold() not in value.casefold()
    ]


class VerneLensAdvisor:
    """Produce a bounded, traceable board response without a remote model."""

    def daily_review(self, packet: EvidencePacket) -> BoardResponse:
        return self._respond("daily_review", packet)

    def decision_consult(self, packet: EvidencePacket) -> BoardResponse:
        return self._respond("decision_consult", packet)

    def _respond(self, mode: str, packet: EvidencePacket) -> BoardResponse:
        limitations = list(packet.gaps) + list(packet.warnings)
        evidence_ids = tuple(item.id for item in packet.source_evidence[:1])
        fact_ids = tuple(item.id for item in packet.company_facts[:1])
        if not packet.company_facts:
            limitations.append("No se recibió contexto empresarial.")
        if not evidence_ids:
            return BoardResponse(
                schema_version=SCHEMA_VERSION,
                mode=mode,
                disclosure=DISCLOSURE,
                summary="No hay evidencia local suficiente para una recomendación fundamentada.",
                questions=(f"¿Qué dato de {packet.category} quieres aclarar primero?",),
                limitations=tuple(dict.fromkeys(limitations)),
                evidence=packet.source_evidence,
            )
        observation = AdviceItem(
            text=packet.company_facts[0].text[:360],
            kind="company_observation",
            company_fact_ids=fact_ids,
            confidence="low",
        )
        action = AdviceItem(
            text=f"Contrasta ese tema en la próxima revisión de {packet.category} con la evidencia local indicada.",
            kind="inference",
            company_fact_ids=fact_ids,
            evidence_ids=evidence_ids,
            confidence="medium",
        )
        question = (
            f"¿Qué resultado observable confirmará el avance en {packet.category}?"
        )
        summary = "Revisión breve con evidencia local y una inferencia marcada para decisión humana."
        if mode == "decision_consult":
            summary = "Consulta estructurada: la decisión sigue siendo humana y se muestra la evidencia disponible."
        return BoardResponse(
            schema_version=SCHEMA_VERSION,
            mode=mode,
            disclosure=DISCLOSURE,
            summary=summary,
            observations=(observation,),
            questions=(question,),
            recommended_actions=(action,),
            limitations=tuple(dict.fromkeys(limitations)),
            evidence=packet.source_evidence,
        )

    @staticmethod
    def render_markdown(response: BoardResponse) -> str:
        lines = [
            "## Lente de Board de ScaleUp",
            "",
            response.disclosure,
            "",
            f"**Resumen:** {response.summary}",
        ]
        if response.observations:
            lines += ["", "### Observación"] + [
                f"- {item.text} *(inferencia/dato de empresa)*"
                for item in response.observations
            ]
        if response.questions:
            lines += ["", "### Pregunta"] + [f"- {item}" for item in response.questions]
        if response.recommended_actions:
            lines += ["", "### Siguiente paso propuesto"] + [
                f"- {item.text}" for item in response.recommended_actions
            ]
        if response.evidence:
            lines += ["", "### Evidencia local"] + [
                f"- {item.entity_name} (líneas {', '.join(map(str, item.line_refs))})"
                for item in response.evidence
            ]
        if response.limitations:
            lines += ["", "### Límites"] + [
                f"- {item}" for item in response.limitations
            ]
        return "\n".join(lines)
