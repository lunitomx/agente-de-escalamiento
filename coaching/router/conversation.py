"""A small, deterministic conversation layer for the public ScaleUp door.

The language model only passes the latest user sentence to this module.  The
state machine owns field names, persistence and the next question, so a
beginner never has to construct a tool payload.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from escala_server.accountability import AccountabilityStore
from escala_server.board import (
    BoardContextBuilder,
    PortableKnowledgeHandler,
    VerneLensAdvisor,
)
from escala_server.connected_guidance import (
    anonymize_preview,
    capabilities,
    recommend,
    record_decision,
    swt_recipe,
)
from escala_server.evidence import EvidenceStore, field_specs, sensitivity_of
from escala_server.human_context import HumanContextStore
from escala_server.project_memory import ProjectMemoryRuntime
from escala_server.project_memory_continuity import ProjectMemoryContinuity
from escala_server.weekly_cadence import WeeklyCadenceStore
from escala_server.workspace import WorkspaceIndexer, create_workspace, load_workspace

from ..core import read_yaml, write_yaml
from ..diagnose import DIAGNOSE_QUESTIONS
from ..diagnose import run as run_diagnose
from ..opsp import update_opsp
from ..progress import run as run_progress
from ..welcome import run as run_welcome

STATE_PATH = Path(".scaleup/agent/memory/conversation.yaml")
DECISIONS = ("people", "strategy", "execution", "cash")
PLAN_STEPS = (
    (
        "core_values",
        "¿Cuáles son tres valores que guían las decisiones de tu empresa? Escríbelos separados por comas.",
    ),
    ("purpose", "¿Cuál es el propósito de tu empresa más allá de hacer dinero?"),
    ("bhag", "¿Qué meta ambiciosa quieren alcanzar en 10 a 25 años?"),
    ("bhag_date", "¿Para qué fecha quieren alcanzar esa meta?"),
    ("market", "¿En qué mercado o geografía competirán?"),
    (
        "brand_promise",
        "¿Qué promesa concreta hacen a sus clientes y cómo la medirán? Escribe promesa; indicador.",
    ),
    ("quarter", "¿Qué trimestre estás planificando?"),
    ("critical_number", "¿Cuál es el número crítico que enfocará este trimestre?"),
    ("year", "¿Qué año cubrirán estas metas?"),
    ("annual_revenue", "¿Cuál es su meta anual de ingresos?"),
    ("annual_profit", "¿Cuál es su meta anual de utilidad?"),
    (
        "annual_priority",
        "Dime una prioridad anual con responsable e indicador: prioridad; responsable; indicador.",
    ),
    (
        "quarterly_priority",
        "Dime una prioridad de este trimestre con responsable e indicador: prioridad; responsable; indicador.",
    ),
)


def _state_path(base: Path) -> Path:
    # A shared E26 folder must never store a leader's personal answers.
    runtime = ProjectMemoryRuntime(base)
    if runtime.shared_workspace:
        return runtime.memory_root / "conversation.yaml"
    return base / STATE_PATH


def _load(base: Path) -> dict[str, Any]:
    state = read_yaml(_state_path(base))
    return state if isinstance(state, dict) else {}


def _save(base: Path, state: dict[str, Any]) -> None:
    write_yaml(_state_path(base), state)


def _profile(base: Path) -> dict[str, Any]:
    value = read_yaml(base / ".scaleup/agent/memory/company-profile.yaml")
    return value if isinstance(value, dict) else {}


def _normalise(text: str) -> str:
    import unicodedata

    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


def _wants_plan(text: str) -> bool:
    return bool(
        re.search(
            r"\b(opsp|one[ -]?page|una pagina|plan en una hoja|plan.*hoja|plan estrategico)\b",
            _normalise(text),
        )
    )


def _wants_progress(text: str) -> bool:
    return bool(
        re.search(
            r"\b(progreso|avance|tareas|pendiente|continuar|retomar|como vamos|que sigue)\b",
            _normalise(text),
        )
    )



def _wants_workspace(text: str) -> bool:
    normal = _normalise(text)
    return bool(
        re.search(
            r"\b(compartir|compartida|colaborador(?:es)?|workspace|drive desktop|"
            r"carpeta.*(?:equipo|drive|compart)|equipo.*(?:carpeta|trabaj))\b",
            normal,
        )
    )


def _wants_workspace_status(text: str) -> bool:
    normal = _normalise(text)
    return bool(
        re.search(
            r"\b(?:revisa|revisar|estado|salud|diagnostico|reconstruye|reconstruir)\b.*"
            r"\b(?:carpeta|workspace|compartid)\b",
            normal,
        )
    )


def _wants_workspace_rebuild(text: str) -> bool:
    normal = _normalise(text)
    return bool(
        re.search(r"\b(?:reconstruye|reconstruir|actualiza|actualizar)\b", normal)
        and re.search(r"\b(?:carpeta|workspace|compartid)\b", normal)
    )


def _answers_yes(text: str) -> bool:
    return _normalise(text).strip(" .!¡?¿") in {
        "si",
        "si quiero",
        "sí",
        "sí quiero",
        "confirmo",
        "adelante",
        "preparala",
        "preparala por favor",
    }


def _answers_no(text: str) -> bool:
    return _normalise(text).strip(" .!¡?¿") in {"no", "ahora no", "cancelar"}


def _workspace_turn(base: Path, state: dict[str, Any], text: str) -> str | None:
    """Keep workspace setup in the same public, one-question conversation."""
    pending = state.get("workspace_stage")
    if pending == "confirm-current-folder":
        if _answers_no(text):
            state.pop("workspace_stage", None)
            _save(base, state)
            return "De acuerdo. Seguiremos trabajando localmente y podrás compartir una carpeta cuando quieras."
        if not _answers_yes(text):
            return "Para preparar esta carpeta para tu equipo necesito una confirmación clara: ¿quieres que la deje lista para compartir?"
        profile = _profile(base)
        name = profile.get("company", {}).get("name") or "Mi empresa"
        created = create_workspace(base, str(name))
        state.pop("workspace_stage", None)
        _save(base, state)
        if not created.ready:
            return "No pude preparar la carpeta compartida: " + (created.reason or "inténtalo de nuevo")
        return (
            "Listo. Esta carpeta ya tiene una estructura empresarial que puedes sincronizar con Drive Desktop, Dropbox u OneDrive. "
            "La base local de este equipo queda fuera de la carpeta compartida. "
            "Cuando otro colaborador abra la misma carpeta, podrá reconstruir su propia memoria local."
        )

    workspace = load_workspace(base)
    if workspace.ready:
        if _wants_workspace_rebuild(text):
            rebuilt = WorkspaceIndexer(base).rebuild()
            if not rebuilt.ready:
                return "No pude reconstruir la memoria local: " + (rebuilt.reason or "inténtalo de nuevo")
            if rebuilt.conflicts:
                return "Reconstruí la memoria local y conservé cambios que necesitan conciliación. Di “revisa la carpeta compartida” para ver el siguiente paso."
            return "Listo: reconstruí la memoria local de este equipo desde la carpeta compartida."
        if _wants_workspace_status(text):
            doctor = WorkspaceIndexer(base).doctor()
            return doctor.message
        if _wants_workspace(text):
            return (
                "Esta carpeta ya está preparada para colaborar. Compártela con el proveedor de archivos que uses; "
                "ScaleUp no pide credenciales ni comparte bases SQLite. Puedes decir “revisa la carpeta compartida” cuando quieras comprobarla."
            )
        return None
    if _wants_workspace(text):
        state["workspace_stage"] = "confirm-current-folder"
        _save(base, state)
        return (
            "Puedo preparar esta carpeta para que la compartas con tu equipo usando el proveedor que prefieras. "
            "Sólo se compartirán documentos empresariales legibles; la memoria SQLite de cada equipo será local. "
            "¿Quieres preparar esta carpeta ahora?"
        )
    return None

_HUMAN_CONTEXT_STEPS = ("role", "communication_style", "detail_level", "availability")
_HUMAN_FIELD_ALIASES = {
    "rol": "role", "responsabilidad": "responsibilities",
    "estilo": "communication_style", "idioma": "language",
    "detalle": "detail_level", "ritmo": "pace", "disponibilidad": "availability",
    "horario": "availability", "horizonte": "horizon", "capacidad": "capacity",
    "objetivo profesional": "professional_goal",
}


def _human_context_question(field: str) -> str:
    label, purpose = HumanContextStore.describe(field)
    return f"Opcional: ¿qué te gustaría que supiera sobre tu {label}? Me serviría para {purpose}. Puedes decir “saltar”."


def _offer_human_context(base: Path, state: dict[str, Any]) -> str:
    state["stage"] = "human_context_offer"
    _save(base, state)
    return "Antes de seguir, si quieres puedo adaptar la ayuda a cómo trabajas. Sólo guardaría preferencias que confirmes, en la memoria local de este equipo. ¿Quieres personalizarlo ahora?"


def _advance_human_context(base: Path, state: dict[str, Any]) -> str:
    step = int(state.get("human_context_step", 0)) + 1
    if step >= len(_HUMAN_CONTEXT_STEPS):
        state.pop("human_context_step", None)
        state.pop("human_context_pending", None)
        return _begin_diagnosis(base, state)
    state.update({"stage": "human_context_capture", "human_context_step": step})
    _save(base, state)
    return _human_context_question(_HUMAN_CONTEXT_STEPS[step])


def _human_context_turn(base: Path, state: dict[str, Any], text: str) -> str | None:
    stage = state.get("stage")
    normal = _normalise(text).strip(" .!¡?¿")
    store = HumanContextStore(base)
    if stage == "human_context_offer":
        if _answers_no(text) or normal in {"saltar", "omitir"}:
            return _begin_diagnosis(base, state)
        if not _answers_yes(text):
            return "Es opcional. ¿Quieres personalizar cómo te acompaño ahora? Puedes responder “sí” o “ahora no”."
        state.update({"stage": "human_context_capture", "human_context_step": 0})
        _save(base, state)
        return _human_context_question("role")
    if stage == "human_context_capture":
        if _answers_no(text) or normal in {"saltar", "omitir"}:
            return _advance_human_context(base, state)
        field = _HUMAN_CONTEXT_STEPS[int(state.get("human_context_step", 0))]
        valid = store.validate(field, text)
        if not valid.ready:
            return "Eso parece un dato delicado, así que no lo guardaré. " + (valid.suggested_generalization or _human_context_question(field))
        label, purpose = HumanContextStore.describe(field)
        state.update({"stage": "human_context_confirm", "human_context_pending": {"field": field, "value": text.strip()}})
        _save(base, state)
        return f"Entendí tu {label}: “{text.strip()}”. Esto sirve para {purpose}. ¿Quieres guardarlo sólo en la memoria local de este equipo?"
    if stage == "human_context_confirm":
        pending = state.get("human_context_pending")
        if not isinstance(pending, dict) or not isinstance(pending.get("field"), str) or not isinstance(pending.get("value"), str):
            state.pop("human_context_pending", None)
            return _advance_human_context(base, state)
        if _answers_yes(text):
            result = store.confirm(pending["field"], pending["value"], explicit_confirmation=True)
            state.pop("human_context_pending", None)
            if not result.ready:
                state["stage"] = "human_context_capture"
                _save(base, state)
                return "No pude guardar esa preferencia. " + _human_context_question(pending["field"])
            return _advance_human_context(base, state)
        if _answers_no(text) or normal in {"saltar", "omitir"}:
            state.pop("human_context_pending", None)
            return _advance_human_context(base, state)
        return "No lo guardaré sin tu confirmación. ¿Quieres guardarlo sólo en este equipo? Responde “sí” o “no”."
    if stage == "human_context_change":
        field = state.get("human_context_field")
        if not isinstance(field, str):
            state.pop("stage", None)
            _save(base, state)
            return None
        valid = store.validate(field, text)
        if not valid.ready:
            return "Eso parece delicado y no lo guardaré. " + (valid.suggested_generalization or _human_context_question(field))
        state.update({"stage": "human_context_confirm_change", "human_context_pending": {"field": field, "value": text.strip()}})
        _save(base, state)
        return "¿Quieres guardar este cambio sólo en la memoria local de este equipo?"
    if stage == "human_context_confirm_change":
        pending = state.get("human_context_pending")
        if isinstance(pending, dict) and _answers_yes(text):
            result = store.confirm(str(pending.get("field")), pending.get("value"), explicit_confirmation=True)
            state.pop("human_context_pending", None)
            state.pop("human_context_field", None)
            state.pop("stage", None)
            _save(base, state)
            return "Listo, actualicé esa preferencia local." if result.ready else "No pude actualizar esa preferencia."
        if _answers_no(text):
            state.pop("human_context_pending", None)
            state.pop("human_context_field", None)
            state.pop("stage", None)
            _save(base, state)
            return "De acuerdo, no cambié nada."
        return "No lo guardaré sin confirmación. ¿Quieres guardar el cambio sólo en este equipo?"
    if re.search(r"\b(?:ver|mostrar|que recuerdas|que sabes)\b.*\b(?:perfil|contexto|preferenc|como trabajo)\b", normal):
        result = store.list()
        if not result.ready:
            return "No pude abrir tu contexto personal local."
        if not result.entries:
            return "No tengo preferencias personales guardadas."
        lines = ["Esto es lo que guardaste para adaptar la ayuda:"]
        for entry in result.entries:
            label, _ = HumanContextStore.describe(entry.field)
            lines.append(f"- {label.capitalize()}: {entry.value}")
        return "\n".join(lines)
    if re.search(r"\b(?:borra|elimina|olvida)\b.*\b(?:perfil|contexto|preferenc|como trabajo)\b", normal):
        return "Listo, borré tu contexto personal local." if store.delete().ready else "No pude borrar ese contexto."
    if re.search(r"\b(?:cambia|modifica|actualiza)\b", normal):
        field = next((value for phrase, value in _HUMAN_FIELD_ALIASES.items() if phrase in normal), None)
        if field:
            state.update({"stage": "human_context_change", "human_context_field": field})
            _save(base, state)
            return _human_context_question(field)
    if re.search(r"\b(?:personaliza(?:r)?|perfil personal|mi perfil|como trabajo|preferencias|conocerme)\b", normal):
        state.update({"stage": "human_context_capture", "human_context_step": 0})
        _save(base, state)
        return _human_context_question("role")
    return None

_CADENCE_STEPS = ("weekday", "timezone", "duration", "owner", "priority", "project", "desired_outcome", "next_action")
_WEEKDAYS = {
    "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2, "jueves": 3,
    "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6,
}


def _wants_cadence(text: str) -> bool:
    return bool(re.search(r"\b(?:revision semanal|revisión semanal|cadencia semanal|activar.*semanal|check.?in semanal)\b", _normalise(text)))


_ACCOUNTABILITY_STEPS = (
    ("held_on", "¿De qué fecha es esta sesión de Accountability? Puedes decir “hoy”.", False),
    ("personal_update", "¿Qué pasó en lo personal desde la sesión anterior? Puedes decir “saltar”; no usaré esto para inferencias psicológicas.", True),
    ("business_update", "¿Qué cambió en el negocio desde la sesión anterior? Cuéntame hechos y resultados.", False),
    ("issue_statement", "¿Qué situación concreta quieres llevar al grupo?", False),
    ("pillar_and_tool", "¿Se relaciona principalmente con People, Strategy, Execution o Cash? ¿Qué herramienta has intentado usar?", False),
    ("background", "¿Qué contexto necesita el grupo para entender la situación?", False),
    ("current_situation", "¿Cuál es la situación actual, sin interpretar ni resolverla todavía?", False),
    ("future_options", "¿Qué opciones reales estás considerando?", False),
    ("uncertainty", "¿Dónde te sientes más incierto, confundido o preocupado?", False),
    ("own_contribution", "¿Cómo podrían tus propias acciones estar contribuyendo a esta situación?", False),
    ("failure_impact", "¿Qué significaría no resolverla para ti, el equipo o la empresa?", False),
    ("personal_challenge", "¿Cuál es tu reto personal al enfrentarla?", False),
    ("desired_outcome", "¿Qué resultado esperas obtener de esta sesión?", False),
    ("confidence", "¿Qué nivel de confianza tienes hoy, de 0 a 100, para lograr ese resultado?", False),
    ("notes", "¿Hay alguna nota u opción que quieras llevar preparada? Puedes decir “saltar”.", True),
    ("tags", "¿Qué temas quieres usar para encontrar patrones después? Escríbelos separados por comas; deben ser temas que tú confirmas.", False),
)
_ACCOUNTABILITY_COMMITMENT_STEPS = (
    ("statement", "¿Qué acción o resultado te comprometes a completar antes de la siguiente sesión?"),
    ("owner", "¿Quién es la única persona dueña de este compromiso?"),
    ("due_on", "¿Para qué fecha debe estar listo?"),
    ("success_measure", "¿Qué evidencia concreta demostrará que se cumplió?"),
)


def _accountability_date(text: str) -> str | None:
    from datetime import date, datetime

    normal = _normalise(text).strip(" .!¡?¿")
    if normal == "hoy":
        return date.today().isoformat()
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if match:
        try:
            return date.fromisoformat(match.group(1)).isoformat()
        except ValueError:
            return None
    match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
    if match:
        try:
            return datetime.strptime(match.group(0), "%d/%m/%Y").date().isoformat()
        except ValueError:
            return None
    return None


def _clear_accountability_state(state: dict[str, Any]) -> None:
    for key in tuple(state):
        if key.startswith("accountability_"):
            state.pop(key, None)
    state.pop("stage", None)


def _accountability_pattern_reply(store: AccountabilityStore) -> str:
    result = store.patterns()
    if not result.ready or not result.data:
        return "No pude analizar tus sesiones de Accountability."
    data = result.data
    if not data["session_count"]:
        return "Todavía no hay sesiones de Accountability guardadas. Puedo ayudarte a preparar la primera."
    sessions_result = store.list_sessions()
    sessions = sessions_result.data["sessions"] if sessions_result.ready and sessions_result.data else []
    dates = {item["id"]: item["held_on"] for item in sessions}
    lines = [f"Analicé {data['session_count']} sesiones incluidas con una regla clara: algo sólo es patrón si aparece en dos o más sesiones."]
    if data["average_follow_through_percent"] is not None:
        lines.append(f"Seguimiento promedio de compromisos revisados: {data['average_follow_through_percent']}% según resultado, evidencia, plazo y aprendizaje.")
    labels = {
        "decision_frequency": "Área recurrente",
        "confirmed_theme": "Tema confirmado recurrente",
        "repeated_blocker": "Bloqueo repetido",
        "confidence_gap": "Brecha entre confianza y resultado",
    }
    for item in data["patterns"][:5]:
        support = ", ".join(dates.get(value, value) for value in item["session_ids"])
        lines.append(f"- {labels.get(item['kind'], 'Patrón')}: {item['label']} ({support}).")
    if not data["patterns"]:
        lines.append("Aún no hay patrones con dos sesiones de evidencia.")
    if data["observations"]:
        lines.append("Hay observaciones únicas que todavía no llamaré patrones.")
    return "\n".join(lines)


def _accountability_turn(base: Path, state: dict[str, Any], text: str) -> str | None:
    stage = state.get("stage")
    normal = _normalise(text).strip(" .!¡?¿")
    store = AccountabilityStore(base)

    if "accountability group sharing worksheet" in normal:
        confirmed = normal.startswith("confirmo guardar")
        document = re.sub(r"^\s*confirmo guardar\s*:\s*", "", text, flags=re.I)
        preview = store.preview_import(
            document,
            title="Documento de Accountability pegado por la persona",
            held_on=str(__import__("datetime").date.today()),
            source_type="imported_document",
        )
        if not confirmed:
            warning = ", ".join(preview.warnings) if preview.warnings else "sin marcadores delicados detectados"
            return (
                f"Reconocí {len(preview.recognized_fields)} secciones y detecté: {warning}. "
                "No guardé ni indexé el texto. Si quieres conservarlo, vuelve a pegarlo empezando con “Confirmo guardar:”."
            )
        saved = store.confirm_import(preview, explicit_confirmation=True)
        return "Guardé localmente esa sesión con su fuente y consentimiento." if saved.ready else "No pude guardar esa sesión: " + (saved.reason or "revisa el documento")

    if stage == "accountability_prepare_offer":
        if _answers_no(text):
            _clear_accountability_state(state)
            _save(base, state)
            return "De acuerdo. No guardé un borrador. Puedes retomarlo cuando quieras."
        if not _answers_yes(text):
            return "No conservaré respuestas sin tu permiso. ¿Quieres iniciar y guardar el borrador sólo en la memoria local de este equipo?"
        state.update({"stage": "accountability_prepare", "accountability_step": 0, "accountability_data": {}})
        _save(base, state)
        return _ACCOUNTABILITY_STEPS[0][1]

    if stage == "accountability_prepare":
        step = int(state.get("accountability_step", 0))
        key, question, optional = _ACCOUNTABILITY_STEPS[step]
        data = dict(state.get("accountability_data", {}))
        if optional and normal in {"saltar", "omitir", "ninguna", "ninguno"}:
            value: Any = None
        elif key == "held_on":
            value = _accountability_date(text)
            if value is None:
                return "No pude reconocer la fecha. Puedes decir “hoy”, “26/08/2026” o “2026-08-26”."
        elif key == "confidence":
            match = re.search(r"(?<!\d)(100|[1-9]?\d)(?!\d)", text)
            value = int(match.group(1)) if match else None
            if value is None:
                return "Necesito un número de 0 a 100 y después te pediré la evidencia detrás de los resultados."
        elif key == "tags":
            value = [part.strip() for part in re.split(r"[,;]", text) if part.strip()]
            if not value:
                return question
        else:
            value = text.strip()
            if not value:
                return question
        if value is not None:
            data[key] = value
        step += 1
        if step < len(_ACCOUNTABILITY_STEPS):
            state.update({"accountability_step": step, "accountability_data": data})
            _save(base, state)
            return _ACCOUNTABILITY_STEPS[step][1]
        state.update({"stage": "accountability_prepare_confirm", "accountability_data": data})
        _save(base, state)
        return (
            f"Preparé la sesión del {data['held_on']}. Asunto: “{data['issue_statement']}”. "
            f"Resultado buscado: “{data['desired_outcome']}”. Confianza declarada: {data['confidence']}/100. "
            "¿Confirmas guardarla localmente como tu worksheet de Accountability?"
        )

    if stage == "accountability_prepare_confirm":
        if _answers_no(text):
            _clear_accountability_state(state)
            _save(base, state)
            return "De acuerdo. Borré el borrador y no creé la sesión."
        if not _answers_yes(text):
            return "No crearé la sesión sin una confirmación clara. ¿La guardo localmente?"
        data = dict(state.get("accountability_data", {}))
        held_on = data.pop("held_on", None)
        tags = data.pop("tags", [])
        result = store.create_session(data, held_on=str(held_on), tags=tags, explicit_confirmation=True)
        if not result.ready or not result.data:
            return "No pude guardar la sesión: " + (result.reason or "revisa las respuestas")
        state.update({"stage": "accountability_commitment_offer", "accountability_session_id": result.data["id"]})
        state.pop("accountability_data", None)
        state.pop("accountability_step", None)
        _save(base, state)
        return "La sesión quedó guardada con fuente y fecha. ¿Quieres convertirla ahora en un compromiso verificable?"

    if stage == "accountability_commitment_offer":
        if _answers_no(text):
            _clear_accountability_state(state)
            _save(base, state)
            return "Listo. Conservé la sesión sin inventar un compromiso."
        if not _answers_yes(text):
            return "¿Quieres definir ahora quién hará qué, para cuándo y cómo sabremos que se cumplió?"
        state.update({"stage": "accountability_commitment", "accountability_commitment_step": 0, "accountability_commitment": {}})
        _save(base, state)
        return _ACCOUNTABILITY_COMMITMENT_STEPS[0][1]

    if stage == "accountability_commitment":
        step = int(state.get("accountability_commitment_step", 0))
        key, question = _ACCOUNTABILITY_COMMITMENT_STEPS[step]
        data = dict(state.get("accountability_commitment", {}))
        if key == "due_on":
            value = _accountability_date(text)
            if value is None:
                return "No pude reconocer la fecha. Puedes decir “15/09/2026” o “2026-09-15”."
        else:
            value = text.strip()
            if not value:
                return question
        data[key] = value
        step += 1
        if step < len(_ACCOUNTABILITY_COMMITMENT_STEPS):
            state.update({"accountability_commitment_step": step, "accountability_commitment": data})
            _save(base, state)
            return _ACCOUNTABILITY_COMMITMENT_STEPS[step][1]
        state.update({"stage": "accountability_commitment_confirm", "accountability_commitment": data})
        _save(base, state)
        return f"Compromiso: “{data['statement']}”; responsable: {data['owner']}; fecha: {data['due_on']}; evidencia: {data['success_measure']}. ¿Lo confirmas?"

    if stage == "accountability_commitment_confirm":
        if _answers_no(text):
            _clear_accountability_state(state)
            _save(base, state)
            return "De acuerdo. Conservé la sesión pero no guardé el compromiso."
        if not _answers_yes(text):
            return "No guardaré el compromiso sin tu confirmación. ¿Lo confirmas?"
        data = state.get("accountability_commitment", {})
        result = store.add_commitment(str(state.get("accountability_session_id")), **data, explicit_confirmation=True) if isinstance(data, dict) else None
        _clear_accountability_state(state)
        _save(base, state)
        return "Guardé el compromiso. En la siguiente sesión podrás revisar resultado, evidencia, plazo y aprendizaje." if result and result.ready else "No pude guardar el compromiso."

    if stage == "accountability_review_status":
        status = {"hecho": "done", "cumplido": "done", "parcial": "partial", "no hecho": "not_done", "incumplido": "not_done", "renegociado": "renegotiated"}.get(normal)
        if status is None:
            return "¿El compromiso quedó hecho, parcial, no hecho o renegociado?"
        review = dict(state.get("accountability_review", {})); review["status"] = status
        state.update({"stage": "accountability_review_result", "accountability_review": review}); _save(base, state)
        return "¿Qué resultado observable obtuviste?"
    if stage == "accountability_review_result":
        review = dict(state.get("accountability_review", {})); review["result"] = text.strip()
        state.update({"stage": "accountability_review_evidence", "accountability_review": review}); _save(base, state)
        return "¿Qué evidencia tienes? Si no existe, di “sin evidencia”."
    if stage == "accountability_review_evidence":
        review = dict(state.get("accountability_review", {}))
        evidence = None if normal in {"sin evidencia", "ninguna", "ninguno"} else text.strip()
        if review.get("status") in {"done", "partial"} and not evidence:
            return "Para marcarlo hecho o parcial necesito una evidencia concreta, no una impresión. ¿Cuál es?"
        review["evidence"] = evidence
        state.update({"stage": "accountability_review_blocker", "accountability_review": review}); _save(base, state)
        return "¿Qué bloqueo apareció? Puedes decir “ninguno”."
    if stage == "accountability_review_blocker":
        review = dict(state.get("accountability_review", {})); review["blocker"] = None if normal in {"ninguno", "ninguna", "no hubo"} else text.strip()
        state.update({"stage": "accountability_review_learning", "accountability_review": review}); _save(base, state)
        return "¿Qué aprendizaje quieres conservar para el siguiente ciclo? Puedes decir “ninguno”."
    if stage == "accountability_review_learning":
        review = dict(state.get("accountability_review", {})); review["learning"] = None if normal in {"ninguno", "ninguna"} else text.strip()
        if review.get("status") in {"not_done", "renegotiated"} and not (review.get("blocker") or review.get("learning")):
            return "Para un compromiso incompleto necesito al menos el bloqueo o el aprendizaje; no asignaré una calificación vacía. ¿Qué aprendiste?"
        review["reviewed_on"] = str(__import__("datetime").date.today())
        state.update({"stage": "accountability_review_confirm", "accountability_review": review}); _save(base, state)
        return "Calcularé el seguimiento sólo con resultado, evidencia, plazo y aprendizaje, mostrando cada razón. ¿Confirmas guardar esta revisión?"
    if stage == "accountability_review_confirm":
        if _answers_no(text):
            _clear_accountability_state(state); _save(base, state)
            return "De acuerdo. No guardé la revisión."
        if not _answers_yes(text):
            return "No guardaré la revisión sin confirmación. ¿La confirmas?"
        review = state.get("accountability_review", {})
        result = store.review_commitment(str(state.get("accountability_commitment_id")), **review, explicit_confirmation=True) if isinstance(review, dict) else None
        _clear_accountability_state(state); _save(base, state)
        if not result or not result.ready or not result.data:
            return "No pude guardar la revisión: " + ((result.reason if result else None) or "revisa las respuestas")
        rubric = result.data["rubric"]
        reasons = ", ".join(f"{key} {item['points']}/{item['max']}" for key, item in rubric["criteria"].items())
        return f"Guardé la revisión. Seguimiento derivado: {rubric['percent']}% ({reasons}). No es una opinión 1–5; puedes corregir la evidencia y recalcular."

    if re.search(r"\b(?:patrones?|tendencias?|aprendizajes?)\b.*\baccountabil", normal) or re.search(r"\baccountabil.*\b(?:patrones?|tendencias?)\b", normal):
        return _accountability_pattern_reply(store)
    if re.search(r"\b(?:revisar|revisa|calificar|evaluar)\b.*\baccountabil", normal):
        pending = store.latest_pending_commitment()
        if not pending.ready or not pending.data:
            return "No encontré un compromiso pendiente de Accountability. Primero prepara una sesión y confirma quién hará qué, para cuándo y con qué evidencia."
        state.update({"stage": "accountability_review_status", "accountability_commitment_id": pending.data["id"], "accountability_review": {}})
        _save(base, state)
        return f"Revisemos: “{pending.data['statement']}”, con fecha {pending.data['due_on']}. ¿Quedó hecho, parcial, no hecho o renegociado?"
    if re.search(r"\b(?:que|qué)\s+(?:puedes|puede)\s+hacer\b.*\baccountabil", normal):
        return "Sí: puedo ayudarte a preparar una sesión, convertirla en un compromiso verificable, revisar el resultado con evidencia y encontrar patrones entre sesiones. ¿Quieres preparar, revisar o ver patrones?"
    if re.search(r"\b(?:preparar|crear|hacer|iniciar|nuevo|nueva)\b.*\baccountabil", normal):
        state["stage"] = "accountability_prepare_offer"; _save(base, state)
        return "Puedo guiarte una pregunta a la vez con la estructura real de EO y guardar un borrador sólo local. La parte personal no se usará para inferencias. ¿Quieres iniciar?"
    if "accountabil" in normal and ("drive" in normal or "import" in normal or "document" in normal):
        return "Puedo revisar documentos mediante el conector nativo de tu host, pero no importo una carpeta en silencio. Primero mostraré qué se reconoció y qué parece delicado; sólo guardaré cada sesión si tú lo confirmas."
    if "accountabil" in normal:
        return "Sí: puedo ayudarte a preparar una sesión, convertirla en un compromiso verificable, revisar el resultado con evidencia y encontrar patrones entre sesiones. ¿Quieres preparar, revisar o ver patrones?"
    return None


def _cadence_question(step: str) -> str:
    questions = {
        "weekday": "¿Qué día te gustaría hacer esta revisión semanal?",
        "timezone": "¿En qué zona horaria trabajas? Puedes decir, por ejemplo, “Ciudad de México”.",
        "duration": "¿Cuántos minutos quieres reservar? Entre 10 y 180.",
        "owner": "¿Quién será responsable de hacer esta revisión?",
        "priority": "¿Qué prioridad de la empresa debe proteger esta semana?",
        "project": "¿A qué proyecto pertenece ese compromiso?",
        "desired_outcome": "¿Qué resultado observable quieres tener al terminar la semana?",
        "next_action": "¿Cuál es la siguiente acción concreta? Empieza con un verbo, por ejemplo: “Llamar a Ana para revisar vencidos”.",
    }
    return questions[step]


def _parse_cadence_value(step: str, text: str) -> object | None:
    normal = _normalise(text).strip(" .!¡?¿")
    if step == "weekday":
        return next((number for name, number in _WEEKDAYS.items() if name in normal), None)
    if step == "timezone":
        if any(city in normal for city in ("mexico", "cdmx", "monterrey", "guadalajara")):
            return "America/Mexico_City"
        match = re.search(r"\b(?:america|europe|asia|pacific)/[a-z_]+", normal)
        return match.group(0).title().replace("_", "_") if match else None
    if step == "duration":
        match = re.search(r"\b(\d{1,3})\b", normal)
        return int(match.group(1)) if match else None
    return text.strip() if text.strip() else None


def _cadence_turn(base: Path, state: dict[str, Any], text: str) -> str | None:
    stage = state.get("stage")
    store = WeeklyCadenceStore(base)
    normal = _normalise(text).strip(" .!¡?¿")
    if stage == "cadence_setup":
        step = int(state.get("cadence_step", 0))
        key = _CADENCE_STEPS[step]
        value = _parse_cadence_value(key, text)
        if value is None:
            return "No pude entenderlo. " + _cadence_question(key)
        data = dict(state.get("cadence_data", {}))
        data[key] = value
        step += 1
        if step < len(_CADENCE_STEPS):
            state.update({"cadence_step": step, "cadence_data": data})
            _save(base, state)
            return _cadence_question(_CADENCE_STEPS[step])
        state.update({"stage": "cadence_confirm", "cadence_data": data})
        _save(base, state)
        return (
            f"Propongo revisar cada {text.strip()} durante {data['duration']} minutos, "
            f"con {data['owner']} como responsable. El primer compromiso será: {data['next_action']}. "
            "¿Quieres activarlo sólo en la memoria local de este equipo?"
        )
    if stage == "cadence_confirm":
        if _answers_yes(text):
            data = state.get("cadence_data", {})
            if not isinstance(data, dict):
                return "No pude recuperar la propuesta semanal. Empecemos de nuevo."
            data["duration_minutes"] = data.pop("duration")
            result = store.configure(**data, explicit_confirmation=True)
            state.pop("cadence_data", None)
            state.pop("cadence_step", None)
            state["stage"] = "post_plan"
            _save(base, state)
            if not result.ready:
                return "No pude activar la revisión semanal: " + (result.reason or "inténtalo de nuevo")
            return "Listo. La revisión se hará al abrir ScaleUp cuando corresponda; no enviaré notificaciones por mi cuenta."
        if _answers_no(text):
            state.pop("cadence_data", None)
            state.pop("cadence_step", None)
            state["stage"] = "post_plan"
            _save(base, state)
            return "De acuerdo, no activé ninguna cadencia. Puedes hacerlo cuando quieras."
        return "No la activaré sin confirmación. ¿Quieres guardar esta cadencia local? Responde “sí” o “no”."
    if stage == "cadence_review_outcome":
        outcome = {"hecho": "done", "done": "done", "bloqueado": "blocked", "bloqueada": "blocked", "diferido": "deferred", "renegociar": "renegotiated", "renegociado": "renegotiated"}.get(normal)
        if outcome is None:
            return "¿Cómo terminó el compromiso: hecho, bloqueado, diferido o renegociado?"
        review = dict(state.get("cadence_review", {}))
        review["outcome"] = outcome
        state.update({"stage": "cadence_review_result", "cadence_review": review})
        _save(base, state)
        return "¿Qué resultado observaste esta semana?"
    if stage == "cadence_review_result":
        review = dict(state.get("cadence_review", {}))
        review["result"] = text.strip()
        if review.get("outcome") == "blocked":
            state.update({"stage": "cadence_review_blocker", "cadence_review": review})
            _save(base, state)
            return "¿Qué bloqueo concreto quedó pendiente o de quién estás esperando respuesta?"
        state.update({"stage": "cadence_review_next_action", "cadence_review": review})
        _save(base, state)
        return "¿Cuál será tu siguiente acción concreta? Empieza con un verbo y conserva un dueño."
    if stage == "cadence_review_blocker":
        review = dict(state.get("cadence_review", {}))
        review["blocker"] = text.strip()
        state.update({"stage": "cadence_review_next_action", "cadence_review": review})
        _save(base, state)
        return "¿Cuál será tu siguiente acción concreta mientras resuelves ese bloqueo?"
    if stage == "cadence_review_next_action":
        review = dict(state.get("cadence_review", {}))
        review["next_action"] = text.strip()
        state.update({"stage": "cadence_review_confirm", "cadence_review": review})
        _save(base, state)
        return f"Registraré el resultado y propondré como siguiente acción: “{text.strip()}”. ¿Lo confirmas?"
    if stage == "cadence_review_confirm":
        review = state.get("cadence_review", {})
        if _answers_yes(text) and isinstance(review, dict):
            result = store.review(
                outcome=review["outcome"], result=review["result"], blocker=review.get("blocker"),
                priority=review["priority"], project=review["project"],
                desired_outcome=review["desired_outcome"], next_action=review["next_action"],
                owner=review["owner"], explicit_confirmation=True,
            )
            state.pop("cadence_review", None)
            state["stage"] = "post_plan"
            _save(base, state)
            return "Cerramos la revisión y guardé la siguiente acción local." if result.ready else "No pude cerrar la revisión: " + (result.reason or "inténtalo de nuevo")
        if _answers_no(text):
            state.pop("cadence_review", None)
            state["stage"] = "post_plan"
            _save(base, state)
            return "De acuerdo, no guardé esta revisión."
        return "No guardaré la revisión sin tu confirmación. ¿La confirmas?"
    if re.search(r"\b(?:hacer|iniciar|comenzar)\b.*\b(?:revision|revisión) semanal\b", normal):
        current = store.status()
        commitment = current.commitment
        if not current.ready or commitment is None:
            return "Primero necesitas activar una revisión semanal con un compromiso."
        state.update({"stage": "cadence_review_outcome", "cadence_review": {
            "priority": commitment.priority, "project": commitment.project,
            "desired_outcome": commitment.desired_outcome, "owner": commitment.owner,
        }})
        _save(base, state)
        return f"Revisemos tu compromiso: {commitment.next_action}. ¿Cómo terminó: hecho, bloqueado, diferido o renegociado?"
    if re.search(r"\b(?:pausa|pausar)\b.*\b(?:revision|revisión|cadencia)\b", normal):
        return "Pausé la revisión semanal. La historia queda local y puedes reanudarla cuando quieras." if store.pause().ready else "No encontré una revisión semanal activa."
    if re.search(r"\b(?:reanuda|reanudar|reactiva)\b.*\b(?:revision|revisión|cadencia)\b", normal):
        return "Reanudé la revisión semanal. Te la propondré al abrir ScaleUp cuando corresponda." if store.resume().ready else "No encontré una revisión semanal para reanudar."
    if _wants_cadence(text) and "automat" not in normal:
        status = store.status()
        if status.ready and status.cadence_id:
            if status.due:
                return "Tu revisión semanal está pendiente. Puedes decir “hacer mi revisión semanal” para cerrarla con una siguiente acción."
            if status.next_review_on:
                return f"Tu próxima revisión local será el {status.next_review_on}. Puedes decir “pausa mi revisión semanal” cuando quieras."
        state.update({"stage": "cadence_setup", "cadence_step": 0, "cadence_data": {}})
        _save(base, state)
        return "La revisión es opcional y sólo aparecerá al abrir ScaleUp; no enviaré mensajes ni crearé eventos. " + _cadence_question("weekday")
    if re.search(r"\b(?:recordatorio|automatiza|automatizar)\b.*\b(?:revision|revisión|swt|semanal)\b", normal):
        return "Puedo sugerirte cómo configurar un recordatorio nativo en el host que uses, pero no puedo crearlo ni afirmar que se ejecutará. Antes te diré propósito, frecuencia, datos mínimos, alternativa manual y cómo detenerlo."
    return None


def _advance_after_evidence(base: Path, state: dict[str, Any]) -> str:
    """Resume the narrative diagnosis without forcing a score."""
    index = int(state.pop("evidence_narrative_index", state.get("narrative_index", 0))) + 1
    for key in tuple(state):
        if key.startswith(("evidence_", "draft_evidence_")):
            state.pop(key, None)
    state.update({"narrative_index": index, "stage": "diagnosis_narrative"})
    _save(base, state)
    return _narrative_question(index) if index < len(DECISIONS) else _finish_narrative_diagnosis(base, state)


def _offer_evidence(base: Path, state: dict[str, Any], decision: str, text: str) -> str:
    state.update({
        "stage": "evidence_offer",
        "evidence_decision": decision,
        "evidence_narrative_index": int(state.get("narrative_index", 0)),
    })
    _save(base, state)
    label = DIAGNOSE_QUESTIONS[decision]["label"]
    return (
        f"Entendí esto sobre {label}: “{text.strip().replace(chr(10), ' ')[:220]}”. "
        f"¿Quieres mantenerlo como diagnóstico cualitativo o cuantificar {label} ahora con datos reales? "
        "No guardaré ni convertiré nada en una calificación sin que tú lo decidas."
    )


def _cash_data_explanation() -> str:
    return (
        "Para Cash necesito siete variables antes de construir Power of One y el ciclo de efectivo: "
        "precio, volumen, COGS, gastos operativos, días de cobranza (A/R), días de inventario y días de pago (A/P)."
    )


def _start_evidence_capture(base: Path, state: dict[str, Any]) -> str:
    decision = str(state.get("evidence_decision", ""))
    label = DIAGNOSE_QUESTIONS.get(decision, {}).get("label", decision.title())
    state.update({"stage": "evidence_choice", "draft_evidence_values": {}})
    _save(base, state)
    introduction = _cash_data_explanation() + " " if decision == "cash" else ""
    return (
        f"{introduction}Para cuantificar {label}, elige una ruta: captura manual, archivo CSV/XLSX o contenido que ya autorizaste en un conector del host. "
        "Sólo conservaré los campos que confirmes uno por uno; el archivo o contenido original no se guarda. ¿Cuál prefieres?"
    )


def _preview_to_confirmation(base: Path, state: dict[str, Any], preview: Any, source_type: str) -> str:
    decision = str(state.get("evidence_decision", ""))
    if not preview.ready:
        return (preview.reason or "No pude preparar una vista previa.") + " Puedes continuar manualmente o mantener el diagnóstico cualitativo."
    proposed = dict(preview.proposed or {})
    if not proposed:
        return "Vi el archivo, pero no pude asociar columnas con los datos mínimos sin adivinar. Puedes capturarlos manualmente; no guardé ni indexé el archivo."
    state.update({
        "stage": "evidence_confirm_field",
        "draft_evidence_values": proposed,
        "draft_evidence_keys": list(proposed),
        "draft_evidence_field_index": 0,
        "draft_evidence_source_type": source_type,
        "draft_evidence_source_ref": preview.source_ref or "fuente local",
        "draft_evidence_sha256": preview.content_sha256,
    })
    _save(base, state)
    mapped = ", ".join(next(spec.label for spec in field_specs(decision) if spec.key == key) for key in proposed)
    ambiguous = ""
    if preview.ambiguous:
        ambiguous = " No asocié campos ambiguos: " + ", ".join(preview.ambiguous) + "."
    return f"Vista previa lista. Propuse estos campos: {mapped}.{ambiguous} Revisemos uno por uno antes de guardarlos. " + _evidence_field_question(state)


def _evidence_field_question(state: dict[str, Any]) -> str:
    decision = str(state.get("evidence_decision", ""))
    keys = state.get("draft_evidence_keys", [])
    index = int(state.get("draft_evidence_field_index", 0))
    if not isinstance(keys, list) or index >= len(keys):
        return ""
    key = str(keys[index])
    spec = next(item for item in field_specs(decision) if item.key == key)
    value = dict(state.get("draft_evidence_values", {})).get(key)
    return f"{spec.label.capitalize()}: “{value}”. ¿Lo confirmas para {spec.methodology}?"


def _finish_evidence_capture(base: Path, state: dict[str, Any]) -> str:
    decision = str(state.get("evidence_decision", ""))
    snapshot = EvidenceStore(base).snapshot(decision)
    fields = snapshot.get("fields", {}) if isinstance(snapshot, dict) else {}
    confirmed = [item["label"] for item in fields.values() if item.get("state") == "confirmed"]
    pending = [item["label"] for item in fields.values() if item.get("state") != "confirmed"]
    summary = "Guardé localmente los campos confirmados con su fuente y fecha."
    if confirmed:
        summary += " Confirmados: " + ", ".join(confirmed) + "."
    if pending:
        summary += " Pendiente: " + ", ".join(pending) + "."
    return summary + " " + _advance_after_evidence(base, state)


def _wants_evidence(text: str) -> str | None:
    normal = _normalise(text)
    for decision in DECISIONS:
        if re.search(rf"\b(?:trabajar|profundizar|cuantificar|ver)\b.*\b{decision}\b", normal):
            return decision
    if re.search(r"\b(?:caja|efectivo|power of one|ciclo de efectivo)\b", normal):
        return "cash"
    if re.search(r"\b(?:excel|xlsx|csv|archivo|reporte)\b", normal):
        return "cash"
    return None


def _evidence_turn(base: Path, state: dict[str, Any], text: str) -> str | None:
    stage = state.get("stage")
    normal = _normalise(text).strip(" .!¡?¿")
    if stage == "evidence_offer":
        score = _answer_score(text)
        if score is not None:
            decision = str(state.get("evidence_decision", ""))
            answers = dict(state.get("answers", {}))
            answers.update(_score_answers(decision, score))
            state["answers"] = answers
            return _advance_after_evidence(base, state)
        if normal in {"cualitativo", "mantener cualitativo", "sin calificacion", "sin calificación", "omitir", "ahora no", "no"}:
            return _advance_after_evidence(base, state)
        if re.search(r"\b(?:si|sí|cuantificar|datos|real|manual|archivo|excel|conector)\b", normal):
            return _start_evidence_capture(base, state)
        return "Puedes decir “mantener cualitativo”, “cuantificar”, o elegir un número del 1 al 5 si quieres registrar una calificación puntual."
    if stage == "evidence_choice":
        if normal in {"cualitativo", "mantener cualitativo", "cancelar", "ahora no", "no"}:
            return _advance_after_evidence(base, state)
        if re.search(r"\b(?:manual|capturar|escribir)\b", normal):
            state.update({"stage": "evidence_manual", "draft_evidence_field_index": 0, "draft_evidence_values": {}, "draft_evidence_source_type": "manual", "draft_evidence_source_ref": "captura manual"})
            _save(base, state)
            first = field_specs(str(state.get("evidence_decision", "")))[0]
            return "Empecemos con el dato mínimo. " + first.question
        if re.search(r"\b(?:archivo|excel|xlsx|csv|reporte)\b", normal):
            state["stage"] = "evidence_file"
            _save(base, state)
            return "Comparte un archivo CSV o XLSX con las columnas necesarias. Lo previsualizaré localmente y te mostraré el mapeo antes de conservar cualquier campo."
        if re.search(r"\b(?:conector|drive|calendar|calendario|crm|host)\b", normal):
            state["stage"] = "evidence_host"
            _save(base, state)
            return "Autoriza el acceso dentro de tu host y comparte sólo una tabla con los campos necesarios. No abriré cuentas, no instalaré conectores ni asumiré acceso continuo."
        return "Elige captura manual, archivo CSV/XLSX, contenido autorizado por conector, o mantenerlo cualitativo."
    if stage == "evidence_manual":
        decision = str(state.get("evidence_decision", ""))
        specs = field_specs(decision)
        index = int(state.get("draft_evidence_field_index", 0))
        if index >= len(specs):
            return "No pude recuperar el dato pendiente. Empecemos de nuevo con la captura manual."
        if sensitivity_of(text):
            return "Eso parece un dato delicado. No lo guardaré ni indexaré; comparte sólo el valor agregado necesario para la metodología. " + specs[index].question
        preview = EvidenceStore(base).preview_values(decision, {specs[index].key: text})
        if not preview.ready:
            return (preview.reason or "No pude interpretar ese dato.") + " " + specs[index].question
        values = dict(state.get("draft_evidence_values", {}))
        values[specs[index].key] = preview.proposed[specs[index].key]
        index += 1
        if index < len(specs):
            state.update({"draft_evidence_values": values, "draft_evidence_field_index": index})
            _save(base, state)
            return specs[index].question
        final_preview = EvidenceStore(base).preview_values(decision, values)
        return _preview_to_confirmation(base, state, final_preview, "manual")
    if stage == "evidence_file":
        match = re.search(r"(?:archivo|file)\s*[:：]\s*(.+)", text, re.IGNORECASE)
        if not match:
            return "Cuando el archivo esté disponible en esta conversación, lo previsualizaré localmente antes de usarlo. También puedes elegir captura manual."
        return _preview_to_confirmation(base, state, EvidenceStore(base).preview_file(match.group(1).strip(), str(state.get("evidence_decision", ""))), "file_preview")
    if stage == "evidence_host":
        match = re.search(r"(?:contenido|datos)\s*[:：]\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return "Después de autorizarlo en tu host, comparte sólo una tabla con las columnas necesarias. También puedes elegir captura manual."
        return _preview_to_confirmation(base, state, EvidenceStore(base).preview_host_content(match.group(1).strip(), str(state.get("evidence_decision", ""))), "host_connector")
    if stage == "evidence_confirm_field":
        keys = state.get("draft_evidence_keys", [])
        index = int(state.get("draft_evidence_field_index", 0))
        if not isinstance(keys, list) or index >= len(keys):
            return _finish_evidence_capture(base, state)
        key = str(keys[index])
        decision = str(state.get("evidence_decision", ""))
        source_type = str(state.get("draft_evidence_source_type", "manual"))
        source_ref = str(state.get("draft_evidence_source_ref", "captura manual"))
        if _answers_yes(text):
            saved = EvidenceStore(base).confirm_value(decision=decision, field=key, value=dict(state.get("draft_evidence_values", {})).get(key), source_type=source_type, source_ref=source_ref, content_sha256=state.get("draft_evidence_sha256"), source_id=state.get("draft_evidence_source_id"))
            if not saved.ready:
                return "No pude guardar ese campo confirmado: " + (saved.reason or "inténtalo de nuevo")
            state["draft_evidence_source_id"] = saved.source_id
        elif _answers_no(text) or normal in {"omitir", "rechazar"}:
            EvidenceStore(base).reject_value(decision=decision, field=key, source_type=source_type, source_ref=source_ref)
        else:
            return "No lo guardaré sin una decisión clara. Responde “sí” para confirmar o “no” para rechazar este campo."
        state["draft_evidence_field_index"] = index + 1
        _save(base, state)
        return _evidence_field_question(state) if index + 1 < len(keys) else _finish_evidence_capture(base, state)
    if stage not in {"company_name", "company_industry", "company_employees", "diagnosis_narrative", "narrative_score_confirmation", "plan", "diagnosis"}:
        decision = _wants_evidence(text)
        if decision:
            state.update({"stage": "evidence_offer", "evidence_decision": decision, "evidence_narrative_index": len(DECISIONS)})
            _save(base, state)
            return _start_evidence_capture(base, state)
    return None


def _connected_context_turn(base: Path, state: dict[str, Any], text: str) -> str | None:
    normal = _normalise(text)
    pending_need = state.get("connected_guidance_need")
    if pending_need in {"documents", "calendar", "market_research"}:
        if re.search(r"\b(?:acepto|aceptar|si,? acepto|sí,? acepto)\b", normal):
            record_decision(str(base), need=pending_need, state="accepted", explicit_confirmation=True)
            state.pop("connected_guidance_need", None)
            _save(base, state)
            return "Dejé registrada localmente tu decisión. No conecté ninguna cuenta, no instalé nada y no guardé contenido externo."
        if re.search(r"\b(?:rechazo|rechazar|no acepto|ahora no)\b", normal):
            record_decision(str(base), need=pending_need, state="rejected", explicit_confirmation=True)
            state.pop("connected_guidance_need", None)
            _save(base, state)
            return "Dejé registrada localmente tu decisión de no usar esa sugerencia. Puedes retomarla cuando quieras; no conecté ni guardé datos externos."
    need = None
    if "drive" in normal or "document" in normal:
        need = "documents"
    elif "calend" in normal or "agenda" in normal:
        need = "calendar"
    elif "swt" in normal or "deep research" in normal or "investigacion" in normal:
        need = "market_research"
    if need is None:
        return None
    preview_match = re.search(r"(?:compartir|texto|datos)\s*[:：]\s*(.+)", text, re.I)
    if preview_match:
        preview = anonymize_preview(preview_match.group(1))
        if preview is None:
            return "Ese contenido parece incluir un secreto o dato de acceso. No lo guardaré, indexaré ni sugeriré compartirlo."
        return "Vista anonimizada para que la revises antes de compartir fuera de ScaleUp:\n\n" + preview + "\n\nConectarte al host no autoriza guardar ni indexar ese contenido aquí."
    guide = recommend(need, capabilities("none"))
    if need == "market_research":
        guide = swt_recipe(capabilities("none"))
    state["connected_guidance_need"] = need
    _save(base, state)
    return (
        f"Para {guide.purpose.lower()}, el dato mínimo sería: {guide.data_minimum}. "
        f"Riesgo: {guide.risk}. {guide.host_message} "
        f"Alternativa local: {guide.manual_alternative}. Si quieres, pega un texto después de “datos:” y te mostraré una versión anonimizada; no conectaré nada."
    )


def _board_turn(text: str) -> str | None:
    normal = _normalise(text)
    if not re.search(r"\b(?:board|consejo directivo|lente verne|opinion del asesor|opinión del asesor|revisa (?:mi |este )?daily)\b", normal):
        return None
    payload = text.split(":", 1)[1].strip() if ":" in text else text
    packet = BoardContextBuilder(PortableKnowledgeHandler()).build(payload)
    advisor = VerneLensAdvisor()
    response = advisor.daily_review(packet) if "daily" in normal else advisor.decision_consult(packet)
    return advisor.render_markdown(response)


_NARRATIVE_PROMPTS = {
    "people": "Cuéntame cómo está funcionando el equipo: un ejemplo reciente, qué resultado se está logrando y dónde ves el mayor bloqueo.",
    "strategy": "Cuéntame qué cliente atienden, por qué los elige y qué decisión estratégica les cuesta más aclarar hoy.",
    "execution": "Cuéntame cuál es la prioridad más importante, cómo la siguen semana a semana y un ejemplo de algo que se haya atorado.",
    "cash": "Cuéntame cómo entra y sale el dinero: dónde se cobra tarde, qué presiona la caja y qué número revisan hoy.",
}


def _question_for_diagnosis(index: int) -> str:
    decision = DECISIONS[index // 5]
    question = DIAGNOSE_QUESTIONS[decision]["questions"][index % 5]["text"]
    return f"Del 1 al 5 (1 = no existe, 5 = funciona muy bien): {question}"


def _narrative_question(index: int) -> str:
    decision = DECISIONS[index]
    return f"Empecemos por {DIAGNOSE_QUESTIONS[decision]['label']}. {_NARRATIVE_PROMPTS[decision]}"


def _provisional_score(text: str) -> int:
    normal = _normalise(text)
    if re.search(r"\b(?:no|sin|nunca|ningun|ningún)\b", normal):
        return 1
    if re.search(r"\b(?:a veces|informal|ad hoc|depende)\b", normal):
        return 2
    if re.search(r"\b(?:proceso|semanal|cada mes|reunion|reunión)\b", normal):
        return 3
    if re.search(r"\b(?:medimos|sistematic|tablero|indicador)\b", normal):
        return 4
    if re.search(r"\b(?:optim|excelente|siempre)\b", normal):
        return 5
    return 2


def _score_answers(decision: str, score: int) -> dict[str, int]:
    return {question["id"]: score for question in DIAGNOSE_QUESTIONS[decision]["questions"]}


def _finish_narrative_diagnosis(base: Path, state: dict[str, Any]) -> str:
    answers = dict(state.get("answers", {}))
    scored = [decision for decision in DECISIONS if any(key.startswith(decision + "_") for key in answers)]
    notes = dict(state.get("diagnostic_notes", {}))
    profile = _profile(base)
    if profile:
        profile["diagnostic_notes"] = notes
        write_yaml(base / ".scaleup" / "agent" / "memory" / "company-profile.yaml", profile)
    state["stage"] = "post_diagnosis"
    _save(base, state)
    if not scored:
        return "Guardé tu diagnóstico narrativo sin calificaciones. Ya tenemos contexto suficiente para elegir la primera prioridad juntos. ¿Quieres hacer tu plan en una hoja o profundizar en una de las cuatro áreas?"
    result = run_diagnose({"base_path": base, "answers": answers, "decisions": scored, "mode": "partial"})
    return result["output"] + "\n\nLas calificaciones son provisionales y se basan en lo que me contaste. Puedes revisarlas cuando quieras o pasar a tu plan en una hoja."


def _continue_narrative_diagnosis(base: Path, state: dict[str, Any], text: str) -> str:
    index = int(state.get("narrative_index", 0))
    decision = DECISIONS[index]
    score = _answer_score(text)
    if score is not None:
        answers = dict(state.get("answers", {}))
        answers.update(_score_answers(decision, score))
        state.update({"answers": answers, "narrative_index": index + 1})
        _save(base, state)
        return _narrative_question(index + 1) if index + 1 < len(DECISIONS) else _finish_narrative_diagnosis(base, state)
    notes = dict(state.get("diagnostic_notes", {}))
    notes[decision] = text.strip()
    state["diagnostic_notes"] = notes
    return _offer_evidence(base, state, decision, text)


def _confirm_narrative_score(base: Path, state: dict[str, Any], text: str) -> str:
    decision = str(state.get("pending_decision", ""))
    index = int(state.get("narrative_index", 0))
    normal = _normalise(text).strip(" .!¡?¿")
    score = _answer_score(text)
    if _answers_yes(text):
        score = int(state.get("pending_score", 0))
    if normal in {"sin calificacion", "sin calificación", "omitir", "sin numero", "sin número"}:
        score = None
    if score is None and normal not in {"sin calificacion", "sin calificación", "omitir", "sin numero", "sin número"}:
        return "Puedes responder “sí”, otro número del 1 al 5, o “sin calificación”."
    answers = dict(state.get("answers", {}))
    if score is not None:
        answers.update(_score_answers(decision, score))
    state.update({"answers": answers, "narrative_index": index + 1, "stage": "diagnosis_narrative"})
    state.pop("pending_decision", None)
    state.pop("pending_score", None)
    _save(base, state)
    return _narrative_question(index + 1) if index + 1 < len(DECISIONS) else _finish_narrative_diagnosis(base, state)


def _plan_question(step: int) -> str:
    return PLAN_STEPS[step][1]


def _answer_score(text: str) -> int | None:
    match = re.fullmatch(r"\s*([1-5])\s*(?:/\s*5)?\s*", text)
    return int(match.group(1)) if match else None


def _parts(text: str, count: int, *, trim_values_intro: bool = False) -> list[str]:
    prepared = text.strip()
    if trim_values_intro:
        prepared = re.sub(
            r"^\s*(?:nos importan|nuestros valores son|valoramos)\s+",
            "",
            prepared,
            flags=re.IGNORECASE,
        )
    values = [
        part.strip(" .")
        for part in re.split(r"\s*(?:[;,]|\s+\b(?:y|e)\b\s+)\s*", prepared)
        if part.strip(" .")
    ]
    return values if len(values) >= count else []


def _plan_data(state: dict[str, Any], answer: str) -> dict[str, Any]:
    step = int(state.get("plan_step", 0))
    key = PLAN_STEPS[step][0]
    data = dict(state.get("plan", {}))
    if key == "core_values":
        values = _parts(answer, 3, trim_values_intro=True)
        if not values:
            return {}
        data[key] = values[:5]
    elif key == "market":
        data["sandbox"] = {**data.get("sandbox", {}), "market": answer.strip()}
    elif key == "brand_promise":
        values = _parts(answer, 2)
        if not values:
            return {}
        data[key] = {"promise": values[0], "kpi": values[1]}
    elif key in {"annual_priority", "quarterly_priority"}:
        values = _parts(answer, 3)
        if not values:
            return {}
        data[f"{key.replace('_priority', '')}_priorities"] = [
            {"priority": values[0], "owner": values[1], "kpi": values[2]}
        ]
    else:
        data[key] = answer.strip()
    return data


def _start_plan(base: Path, state: dict[str, Any]) -> str:
    state.update({"stage": "plan", "plan_step": 0, "plan": state.get("plan", {})})
    profile = _profile(base)
    company = profile.get("company", {}).get("name", "")
    if company:
        state["plan"] = {"company_name": company, **state["plan"]}
    _save(base, state)
    update_opsp({"base_path": base, "data": state["plan"]})
    return "Vamos a construir tu plan en una hoja paso a paso. " + _plan_question(0)


def _continue_plan(base: Path, state: dict[str, Any], text: str) -> str:
    if _normalise(text).strip() in {"terminar", "finalizar", "listo"}:
        result = update_opsp(
            {"base_path": base, "data": state.get("plan", {}), "complete": True}
        )
        _save(base, state)
        return result["output"]
    data = _plan_data(state, text)
    if not data:
        return "No pude guardar esa respuesta con claridad. " + _plan_question(
            int(state.get("plan_step", 0))
        )
    state["plan"] = data
    step = int(state.get("plan_step", 0)) + 1
    state["plan_step"] = step
    completed = step >= len(PLAN_STEPS)
    result = update_opsp({"base_path": base, "data": data, "complete": completed})
    if completed:
        state["stage"] = "post_plan"
        _save(base, state)
        return (
            result["output"]
            + " ¿Quieres activar una revisión semanal breve para mantener este plan en movimiento, revisar tu progreso o seguir afinándolo?"
        )
    _save(base, state)
    return "Guardé tu avance. " + _plan_question(step)


def _begin_diagnosis(base: Path, state: dict[str, Any]) -> str:
    state.update({"stage": "diagnosis_narrative", "narrative_index": 0, "answers": {}, "diagnostic_notes": {}})
    _save(base, state)
    return "Ahora voy a escucharte antes de poner números. " + _narrative_question(0)


def _continue_diagnosis(base: Path, state: dict[str, Any], text: str) -> str:
    score = _answer_score(text)
    index = int(state.get("diagnosis_index", 0))
    if score is None:
        return "Respóndeme sólo con un número del 1 al 5. " + _question_for_diagnosis(
            index
        )
    decision = DECISIONS[index // 5]
    question_id = DIAGNOSE_QUESTIONS[decision]["questions"][index % 5]["id"]
    answers = dict(state.get("answers", {}))
    answers[question_id] = score
    index += 1
    state.update({"answers": answers, "diagnosis_index": index})
    if index < 20:
        _save(base, state)
        return _question_for_diagnosis(index)
    result = run_diagnose({"base_path": base, "answers": answers, "mode": "full"})
    state["stage"] = "post_diagnosis"
    _save(base, state)
    return (
        result["output"]
        + "\n\nPuedes decir “quiero hacer mi plan en una hoja” cuando quieras."
    )



def _record_intake_sources(state: dict[str, Any], text: str) -> None:
    sources = list(state.get("intake_sources", []))
    for url in re.findall(r"https?://[^\s)>]+", text):
        entry = {"kind": "url", "value": url.rstrip(".,")}
        if entry not in sources:
            sources.append(entry)
    if re.search(r"\b(?:logo|archivo|adjunto|\.svg|\.png|\.jpg|\.pdf)\b", _normalise(text)):
        entry = {"kind": "attachment_reference", "value": "archivo o logo declarado por la persona"}
        if entry not in sources:
            sources.append(entry)
    if sources:
        state["intake_sources"] = sources


def _attach_intake_sources(base: Path, state: dict[str, Any]) -> None:
    sources = state.pop("intake_sources", [])
    if not sources:
        return
    profile = _profile(base)
    company = profile.get("company") if isinstance(profile, dict) else None
    if isinstance(company, dict):
        company["declared_references"] = sources
        write_yaml(base / ".scaleup" / "agent" / "memory" / "company-profile.yaml", profile)



def _intake(base: Path, state: dict[str, Any], text: str) -> str:
    stage = state.get("stage", "company_name")
    normal = _normalise(text).strip(" .!¡?¿")
    _record_intake_sources(state, text)
    unknown = normal in {
        "no se",
        "todavia no lo se",
        "aun no lo se",
        "no estoy seguro",
        "no tengo idea",
    }
    if stage == "company_name":
        if unknown:
            return "No pasa nada. ¿Cómo se llama tu empresa?"
        name = re.search(
            r"(?:mi empresa )?se llama\s+(.+?)(?=[.;!…]|,?\s+(?:vendemos|somos|tenemos)\b|\Z)",
            text,
            re.IGNORECASE,
        )
        industry = re.search(
            r"(?:vendemos|ofrecemos|nos dedicamos a|hacemos)\s+(.+?)(?=[.;!…]|,?\s+(?:somos|tenemos)\b|\Z)",
            text,
            re.IGNORECASE,
        )
        employees = re.search(
            r"(?:somos|tenemos)\s+(\d+)\s*(?:personas|empleados|colaboradores)?\b",
            text,
            re.IGNORECASE,
        )
        if name:
            state["company_name"] = name.group(1).strip(" ,")
        elif not (industry or employees):
            candidate = re.split(r"\s+(?:te dejo|logo|adjunto|archivo|https?://)", text, maxsplit=1, flags=re.IGNORECASE)[0]
            state["company_name"] = candidate.strip(" ,.")
        if industry:
            state["industry"] = industry.group(1).strip(" ,")
        if employees and int(employees.group(1)) > 0:
            state["employees"] = int(employees.group(1))
        if {"company_name", "industry", "employees"} <= state.keys():
            result = run_welcome(
                {
                    "base_path": base,
                    "company_name": state["company_name"],
                    "industry": state["industry"],
                    "employees": state["employees"],
                    "entry_methodology": "bmc",
                }
            )
            if result["errors"]:
                return "No pude guardar el perfil. Empecemos de nuevo: ¿cómo se llama tu empresa?"
            _attach_intake_sources(base, state)
            if state.pop("after_intake", None) == "plan":
                return _start_plan(base, state)
            return _offer_human_context(base, state)
        if "company_name" not in state:
            _save(base, state)
            return "¿Cómo se llama tu empresa?"
        if "industry" not in state:
            state["stage"] = "company_industry"
            _save(base, state)
            return f"¿A qué se dedica {state['company_name']}?"
        state["stage"] = "company_employees"
        _save(base, state)
        return "¿Cuántas personas trabajan allí?"
    if stage == "company_industry":
        if unknown:
            return "Está bien. ¿A qué se dedica tu empresa, en palabras sencillas?"
        if re.fullmatch(r"\s*https?://\S+\s*", text):
            _save(base, state)
            return "Recibí ese enlace como referencia. No lo tomaré como la descripción de tu empresa ni lo revisaré automáticamente. ¿A qué se dedica la empresa, en tus palabras?"
        state.update({"stage": "company_employees", "industry": text.strip()})
        _save(base, state)
        return "¿Cuántas personas trabajan allí?"
    match = re.search(r"\d+", text)
    if not match or int(match.group()) < 1:
        return "Necesito un número de personas para continuar. ¿Cuántas personas trabajan allí?"
    state["employees"] = int(match.group())
    result = run_welcome(
        {
            "base_path": base,
            "company_name": state.get("company_name", ""),
            "industry": state.get("industry", ""),
            "employees": state["employees"],
            "entry_methodology": "bmc",
        }
    )
    if result["errors"]:
        return (
            "No pude guardar el perfil. Empecemos de nuevo: ¿cómo se llama tu empresa?"
        )
    _attach_intake_sources(base, state)
    if state.pop("after_intake", None) == "plan":
        return _start_plan(base, state)
    return _offer_human_context(base, state)


def _run_existing(message: str, base_path: str | Path = ".") -> str:
    """Consume one user turn and return exactly one human-friendly next message."""
    base = Path(base_path)
    text = str(message or "").strip()
    if not text:
        return "Cuéntame qué quieres lograr con tu empresa y empezamos por ahí."
    state = _load(base)
    profile = _profile(base)
    stage = state.get("stage")
    if _wants_plan(text) and stage != "plan":
        if not profile.get("company", {}).get("name") and stage not in {
            "company_name",
            "company_industry",
            "company_employees",
        }:
            state.update({"stage": "company_name", "after_intake": "plan"})
            _save(base, state)
            return "Para preparar tu plan en una hoja, primero necesito conocer tu empresa. ¿Cómo se llama?"
        return _start_plan(base, state)
    if (
        _wants_progress(text)
        and stage
        not in {
            "company_name",
            "company_industry",
            "company_employees",
            "diagnosis",
            "plan",
        }
        and profile
    ):
        result = run_progress({"base_path": base})
        _save(base, state)
        return result["output"]
    if not stage:
        if profile.get("company", {}).get("name"):
            return _begin_diagnosis(base, state)
        state["stage"] = "company_name"
        _save(base, state)
        return "Para orientarte bien, empecemos por tu empresa. ¿Cómo se llama y a qué se dedica? Primero dime el nombre."
    if stage in {"company_name", "company_industry", "company_employees"}:
        return _intake(base, state, text)
    if stage == "diagnosis":
        return _continue_diagnosis(base, state, text)
    if stage == "diagnosis_narrative":
        return _continue_narrative_diagnosis(base, state, text)
    if stage == "narrative_score_confirmation":
        return _confirm_narrative_score(base, state, text)
    if stage == "plan":
        return _continue_plan(base, state, text)
    if profile.get("company", {}).get("name"):
        return "Retomemos desde donde quedamos. Puedes decir “quiero hacer mi plan en una hoja” o “ver mi progreso”."
    state["stage"] = "company_name"
    _save(base, state)
    return "¿Cómo se llama tu empresa?"


def _wants_pause(text: str) -> bool:
    normal = _normalise(text).strip(" .!¡?¿")
    return bool(
        re.fullmatch(
            r"(?:quiero |vamos a |podemos |necesito )?(?:pausar|pausa)", normal
        )
        or re.search(
            r"\b(?:cerrar(?: la)? (?:sesion|conversacion)|terminar por hoy|dejemos (?:aqui|por hoy))\b",
            normal,
        )
    )


def _wants_continue_without_memory(text: str) -> bool:
    """Recognise an explicit choice to leave an unresolved proposal behind."""
    normal = _normalise(text).strip(" .!¡?¿")
    return bool(
        re.fullmatch(
            r"(?:mejor )?(?:sigamos|seguimos|seguir|continuemos|continuar|retomemos)(?: con lo que estabamos trabajando)?",
            normal,
        )
    )


def _wants_resume(text: str) -> bool:
    return bool(
        re.search(
            r"\b(retomar|retomemos|donde nos quedamos|continuemos)\b", _normalise(text)
        )
    )


def _restore_after_memory(base: Path, state: dict[str, Any]) -> None:
    previous = state.pop("memory_return_stage", None)
    state.pop("memory_session_id", None)
    state.pop("memory_proposal_id", None)
    if previous is None:
        state.pop("stage", None)
    else:
        state["stage"] = previous
    _save(base, state)


def run(message: str, base_path: str | Path = ".") -> str:
    """Consume one public turn, adding local continuity only when requested."""
    base = Path(base_path)
    text = str(message or "").strip()
    state = _load(base)
    accountability_reply = _accountability_turn(base, state, text)
    if accountability_reply is not None:
        return accountability_reply
    board_reply = _board_turn(text)
    if board_reply is not None:
        return board_reply
    human_context_reply = _human_context_turn(base, state, text)
    if human_context_reply is not None:
        return human_context_reply
    cadence_reply = _cadence_turn(base, state, text)
    if cadence_reply is not None:
        return cadence_reply
    evidence_reply = _evidence_turn(base, state, text)
    if evidence_reply is not None:
        return evidence_reply
    connected_reply = _connected_context_turn(base, state, text)
    if connected_reply is not None:
        return connected_reply
    workspace_reply = _workspace_turn(base, state, text)
    if workspace_reply is not None:
        return workspace_reply
    weekly_status = WeeklyCadenceStore(base).status()
    if weekly_status.ready and weekly_status.due and not state.get("stage"):
        return "Tu revisión semanal está pendiente. Puedes decir “hacer mi revisión semanal” para cerrarla con una siguiente acción."
    continuity = ProjectMemoryContinuity(base)
    if state.get("stage") == "memory_capture":
        session_id = state.get("memory_session_id")
        if not isinstance(session_id, str):
            _restore_after_memory(base, state)
            return _run_existing(text, base)
        turn = continuity.capture_statement(session_id, text)
        if turn.stage == "confirm" and turn.proposal_id:
            state.update(
                {"stage": "memory_confirm", "memory_proposal_id": turn.proposal_id}
            )
            _save(base, state)
        else:
            _restore_after_memory(base, state)
        return turn.next_question or _run_existing(text, base)
    if state.get("stage") == "memory_confirm":
        session_id = state.get("memory_session_id")
        proposal_id = state.get("memory_proposal_id")
        if not isinstance(session_id, str) or not isinstance(proposal_id, str):
            _restore_after_memory(base, state)
            return _run_existing(text, base)
        if _wants_continue_without_memory(text):
            _restore_after_memory(base, state)
            return _run_existing(text, base)
        turn = continuity.answer_confirmation(session_id, proposal_id, text)
        if turn.stage == "confirm":
            _save(base, state)
        else:
            _restore_after_memory(base, state)
        return turn.next_question or _run_existing(text, base)
    if text and _wants_pause(text):
        turn = continuity.begin_pause()
        if turn.stage == "capture" and turn.session_id:
            state.update(
                {
                    "memory_return_stage": state.get("stage"),
                    "memory_session_id": turn.session_id,
                    "stage": "memory_capture",
                }
            )
            _save(base, state)
            return turn.next_question or _run_existing(text, base)
    if text and _wants_resume(text):
        turn = continuity.resume()
        reply = _run_existing(text, base)
        return f"{turn.prefix}\n\n{reply}" if turn.prefix else reply
    return _run_existing(text, base)
