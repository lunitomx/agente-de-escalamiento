"""A small, deterministic conversation layer for the public ScaleUp door.

The language model only passes the latest user sentence to this module.  The
state machine owns field names, persistence and the next question, so a
beginner never has to construct a tool payload.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from escala_server.project_memory_continuity import ProjectMemoryContinuity

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


def _question_for_diagnosis(index: int) -> str:
    decision = DECISIONS[index // 5]
    question = DIAGNOSE_QUESTIONS[decision]["questions"][index % 5]["text"]
    return f"Del 1 al 5 (1 = no existe, 5 = funciona muy bien): {question}"


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
            + " ¿Quieres revisar tu progreso o seguir afinando el plan?"
        )
    _save(base, state)
    return "Guardé tu avance. " + _plan_question(step)


def _begin_diagnosis(base: Path, state: dict[str, Any]) -> str:
    state.update({"stage": "diagnosis", "diagnosis_index": 0, "answers": {}})
    _save(base, state)
    return (
        "Ahora revisaremos cuatro áreas con una pregunta a la vez. "
        + _question_for_diagnosis(0)
    )


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


def _intake(base: Path, state: dict[str, Any], text: str) -> str:
    stage = state.get("stage", "company_name")
    normal = _normalise(text).strip(" .!¡?¿")
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
            state["company_name"] = text.strip()
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
            if state.pop("after_intake", None) == "plan":
                return _start_plan(base, state)
            return _begin_diagnosis(base, state)
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
    if state.pop("after_intake", None) == "plan":
        return _start_plan(base, state)
    return _begin_diagnosis(base, state)


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
            continuity.answer_confirmation(session_id, proposal_id, "no")
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
