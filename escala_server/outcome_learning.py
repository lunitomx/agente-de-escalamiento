"""Local, owner-confirmed decision-to-learning cycles for E44.

This module deliberately keeps recommendation, decision, observed result,
interpretation, and reusable learning as separate records.  It stores one
portable JSON ledger per company; it never treats an observed change as proof
of causality or promotes a People learning without explicit consent.
"""

from __future__ import annotations

from datetime import date
import html
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
from typing import Any, Literal


DecisionStatus = Literal["accepted", "rejected", "deferred", "needs_information"]
Cadence = Literal["daily", "weekly", "monthly", "quarterly"]
ResultStatus = Literal["observed", "no_result_yet"]
LearningStatus = Literal["confirmed", "corrected", "rejected"]

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DECISIONS = {"people", "strategy", "execution", "cash"}
_CADENCE_DAYS = {"daily": 1, "weekly": 7, "monthly": 30, "quarterly": 90}


class OutcomeLearningError(ValueError):
    """Raised when a business cycle would become ambiguous or unsafe."""


def render_learning_cockpit_html(cockpit: dict[str, Any]) -> str:
    """Render an owner-facing E44 summary without internal identifiers."""
    next_review = cockpit.get("next_review")
    if next_review:
        next_html = (
            "<section><h2>Siguiente revisión</h2>"
            f"<p>{html.escape(str(next_review['decision']))}</p>"
            f"<p>Responsable: {html.escape(str(next_review['owner']))} · "
            f"{html.escape(str(next_review['review_on']))} "
            f"({html.escape(str(next_review['cadence']))})</p>"
            f"<p>Esperamos: {html.escape(str(next_review['expected_result']))}</p>"
            "</section>"
        )
    else:
        next_html = "<section><h2>Siguiente revisión</h2><p>No hay revisiones pendientes.</p></section>"
    cards = (
        ("Decisiones por resolver", cockpit["open_decisions"]),
        ("Acciones vencidas", cockpit["actions_overdue"]),
        ("Revisiones pendientes", cockpit["reviews_due"]),
        ("Resultados observados", cockpit["observed_results"]),
        ("Aprendizajes por confirmar", cockpit["learnings_pending"]),
    )
    items = "".join(
        f"<li><strong>{html.escape(label)}:</strong> {count}</li>"
        for label, count in cards
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        "<title>ESCALA · Seguimiento</title></head><body><main>"
        "<h1>Seguimiento de decisiones</h1>"
        f"<ul>{items}</ul>{next_html}</main></body></html>\n"
    )


class OutcomeLearningLedger:
    """Persist explicit, company-scoped E44 cycles in a portable JSON ledger."""

    def __init__(self, root: Path, company_id: str) -> None:
        if (
            _SAFE_ID.fullmatch(company_id) is None
            or "/" in company_id
            or "\\" in company_id
        ):
            raise OutcomeLearningError(
                "company_id must be a stable non-path identifier"
            )
        self._path = (
            root.expanduser().resolve(strict=False)
            / company_id
            / "outcome-learning.json"
        )

    def register_decision(
        self,
        *,
        recommendation: str,
        decision: str,
        area: str,
        status: DecisionStatus,
        decided_by: str,
        reason: str,
        evidence_ids: tuple[str, ...] = (),
        today: date | None = None,
    ) -> dict[str, Any]:
        """Record a human decision without confusing it with the recommendation."""
        self._require_text(recommendation, "recommendation")
        self._require_text(decision, "decision")
        self._require_text(decided_by, "decided_by")
        self._require_text(reason, "reason")
        if area not in _DECISIONS:
            raise OutcomeLearningError("area must be one of the four decisions")
        if status not in {"accepted", "rejected", "deferred", "needs_information"}:
            raise OutcomeLearningError("decision status is not supported")
        self._validate_ids(evidence_ids, "evidence_id")
        record = {
            "id": self._new_id("cycle"),
            "area": area,
            "recommendation": recommendation.strip(),
            "decision": decision.strip(),
            "decision_status": status,
            "decided_by": decided_by.strip(),
            "reason": reason.strip(),
            "evidence_ids": list(evidence_ids),
            "decided_on": (today or date.today()).isoformat(),
            "actions": [],
            "results": [],
            "learning": None,
        }
        ledger = self._load()
        ledger["cycles"].append(record)
        self._save(ledger)
        return record

    def add_action(
        self,
        cycle_id: str,
        *,
        description: str,
        owner: str,
        review_on: date,
        cadence: Cadence,
        expected_result: str,
        metric: str | None = None,
    ) -> dict[str, Any]:
        """Turn an accepted decision into one accountable, reviewable action."""
        cycle, ledger = self._cycle(cycle_id)
        if cycle["decision_status"] != "accepted":
            raise OutcomeLearningError("only accepted decisions can create actions")
        self._require_text(description, "description")
        self._require_text(owner, "owner")
        self._require_text(expected_result, "expected_result")
        if cadence not in _CADENCE_DAYS:
            raise OutcomeLearningError("cadence is not supported")
        action = {
            "id": self._new_id("action"),
            "description": description.strip(),
            "owner": owner.strip(),
            "review_on": review_on.isoformat(),
            "cadence": cadence,
            "expected_result": expected_result.strip(),
            "metric": metric.strip() if metric and metric.strip() else None,
            "status": "open",
        }
        cycle["actions"].append(action)
        self._save(ledger)
        return action

    def reviews_due(self, on: date) -> list[dict[str, Any]]:
        """Return only open actions due by *on*, with business-facing context."""
        due: list[dict[str, Any]] = []
        for cycle in self._load()["cycles"]:
            for action in cycle["actions"]:
                if (
                    action["status"] == "open"
                    and date.fromisoformat(action["review_on"]) <= on
                ):
                    due.append(
                        {
                            "cycle_id": cycle["id"],
                            "area": cycle["area"],
                            "decision": cycle["decision"],
                            "action_id": action["id"],
                            "owner": action["owner"],
                            "review_on": action["review_on"],
                            "cadence": action["cadence"],
                            "expected_result": action["expected_result"],
                        }
                    )
        return sorted(due, key=lambda item: (item["review_on"], item["action_id"]))

    def record_result(
        self,
        cycle_id: str,
        action_id: str,
        *,
        status: ResultStatus,
        observed: str | None,
        evidence_ids: tuple[str, ...] = (),
        interpretation: str | None = None,
        today: date | None = None,
    ) -> dict[str, Any]:
        """Record an observation without automatically claiming causal effect."""
        cycle, ledger = self._cycle(cycle_id)
        action = self._action(cycle, action_id)
        self._validate_ids(evidence_ids, "evidence_id")
        if status not in {"observed", "no_result_yet"}:
            raise OutcomeLearningError("result status is not supported")
        if status == "observed" and not (observed and observed.strip()):
            raise OutcomeLearningError("an observed result requires an observation")
        if status == "no_result_yet" and observed:
            raise OutcomeLearningError("no_result_yet cannot contain an observation")
        result = {
            "id": self._new_id("result"),
            "action_id": action_id,
            "status": status,
            "observed": observed.strip() if observed else None,
            "evidence_ids": list(evidence_ids),
            "interpretation": interpretation.strip() if interpretation else None,
            "causality": "unconfirmed",
            "recorded_on": (today or date.today()).isoformat(),
        }
        cycle["results"].append(result)
        if status == "observed":
            action["status"] = "reviewed"
        self._save(ledger)
        return result

    def confirm_learning(
        self,
        cycle_id: str,
        result_id: str,
        *,
        statement: str,
        status: LearningStatus,
        confirmed_by: str,
        confidence: int,
        valid_until: date | None = None,
        people_consent: bool = False,
        causal_confirmation: bool = False,
        today: date | None = None,
    ) -> dict[str, Any]:
        """Store an owner-reviewed lesson; only confirmed lessons are reusable."""
        cycle, ledger = self._cycle(cycle_id)
        if not any(item["id"] == result_id for item in cycle["results"]):
            raise OutcomeLearningError("result does not belong to cycle")
        self._require_text(statement, "statement")
        self._require_text(confirmed_by, "confirmed_by")
        if not 0 <= confidence <= 100:
            raise OutcomeLearningError("confidence must be between 0 and 100")
        if status not in {"confirmed", "corrected", "rejected"}:
            raise OutcomeLearningError("learning status is not supported")
        if cycle["area"] == "people" and not people_consent:
            raise OutcomeLearningError("people learning requires explicit consent")
        learning = {
            "result_id": result_id,
            "statement": statement.strip(),
            "status": status,
            "confirmed_by": confirmed_by.strip(),
            "confidence": confidence,
            "confirmed_on": (today or date.today()).isoformat(),
            "valid_until": valid_until.isoformat() if valid_until else None,
            "causality": "owner_confirmed" if causal_confirmation else "not_claimed",
        }
        cycle["learning"] = learning
        self._save(ledger)
        return learning

    def reusable_learnings(self, on: date) -> list[dict[str, Any]]:
        """Return only confirmed, non-expired lessons, never raw observations."""
        results: list[dict[str, Any]] = []
        for cycle in self._load()["cycles"]:
            learning = cycle["learning"]
            if not learning or learning["status"] != "confirmed":
                continue
            if (
                learning["valid_until"]
                and date.fromisoformat(learning["valid_until"]) < on
            ):
                continue
            results.append({"cycle_id": cycle["id"], "area": cycle["area"], **learning})
        return results

    def cockpit(self, on: date) -> dict[str, Any]:
        """Project the next business conversation without exposing storage internals."""
        cycles = self._load()["cycles"]
        due = self.reviews_due(on)
        return {
            "open_decisions": sum(
                item["decision_status"] in {"deferred", "needs_information"}
                for item in cycles
            ),
            "actions_overdue": sum(
                date.fromisoformat(item["review_on"]) < on for item in due
            ),
            "reviews_due": len(due),
            "observed_results": sum(len(item["results"]) for item in cycles),
            "learnings_pending": sum(
                bool(item["results"]) and not item["learning"] for item in cycles
            ),
            "next_review": (
                {
                    "area": due[0]["area"],
                    "decision": due[0]["decision"],
                    "owner": due[0]["owner"],
                    "review_on": due[0]["review_on"],
                    "cadence": due[0]["cadence"],
                    "expected_result": due[0]["expected_result"],
                }
                if due
                else None
            ),
        }

    def _cycle(self, cycle_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        ledger = self._load()
        for cycle in ledger["cycles"]:
            if cycle["id"] == cycle_id:
                return cycle, ledger
        raise OutcomeLearningError("cycle not found")

    @staticmethod
    def _action(cycle: dict[str, Any], action_id: str) -> dict[str, Any]:
        for action in cycle["actions"]:
            if action["id"] == action_id:
                return action
        raise OutcomeLearningError("action does not belong to cycle")

    @staticmethod
    def _require_text(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise OutcomeLearningError(f"{label} is required")

    @staticmethod
    def _validate_ids(values: tuple[str, ...], label: str) -> None:
        if any(_SAFE_ID.fullmatch(item) is None for item in values):
            raise OutcomeLearningError(f"{label} must be a stable identifier")

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}:{uuid.uuid4().hex[:12]}"

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {"schema_version": 1, "cycles": []}
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OutcomeLearningError("outcome ledger is unreadable") from exc
        if payload.get("schema_version") != 1 or not isinstance(
            payload.get("cycles"), list
        ):
            raise OutcomeLearningError("outcome ledger contract is invalid")
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=self._path.parent, prefix=".outcome-learning.", delete=False
            ) as handle:
                temporary = Path(handle.name)
                handle.write(
                    json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                )
                handle.write(b"\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
