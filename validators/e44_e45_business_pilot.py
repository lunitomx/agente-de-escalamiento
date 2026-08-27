"""Privacy-bounded acceptance evidence for the human E44/E45 business pilot."""

from __future__ import annotations

from datetime import date
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


_REFERENCE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_AREAS = {"people", "strategy", "execution", "cash"}


class PilotCycle(_StrictModel):
    area: Literal["people", "strategy", "execution", "cash"]
    outcome_status: Literal["observed", "no_result_yet"]
    owner_review: Literal["confirmed", "corrected", "rejected"]
    people_consent: bool = False


class TeamScenario(_StrictModel):
    scenario_id: Literal["cash-execution", "growth-cross-decision"]
    areas: list[Literal["people", "strategy", "execution", "cash"]] = Field(
        min_length=2, max_length=4
    )
    single_coach_completed: bool
    team_completed: bool
    one_executive_response: bool
    additional_risk_found: bool
    owner_value: Literal["higher", "equal", "lower", "inconclusive"]
    conclusion: Literal["retain-team", "reduce-team", "needs-more-evidence"]
    rounds_used: int = Field(ge=0, le=1)
    elapsed_minutes: int = Field(ge=1, le=120)
    data_minimized: bool

    @model_validator(mode="after")
    def validate_scenario_contract(self) -> "TeamScenario":
        if len(self.areas) != len(set(self.areas)):
            raise ValueError("pilot scenario repeats a decision area")
        expected = (
            {"cash", "execution"}
            if self.scenario_id == "cash-execution"
            else {"people", "strategy", "execution"}
        )
        if set(self.areas) != expected:
            raise ValueError("pilot scenario does not match its required decisions")
        if not (
            self.single_coach_completed
            and self.team_completed
            and self.one_executive_response
            and self.data_minimized
        ):
            raise ValueError("pilot scenario lacks an acceptance safeguard")
        if self.owner_value == "higher" and self.conclusion != "retain-team":
            raise ValueError("higher owner value must retain the team")
        if self.owner_value == "lower" and self.conclusion != "reduce-team":
            raise ValueError("lower owner value must reduce the team")
        if (
            self.owner_value in {"equal", "inconclusive"}
            and self.conclusion != "needs-more-evidence"
        ):
            raise ValueError("non-decisive owner value needs more evidence")
        return self


class E44E45BusinessPilotReceipt(_StrictModel):
    schema_version: Literal[1]
    status: Literal["pass"]
    participant_ref: str = Field(min_length=3, max_length=64)
    company_ref: str = Field(min_length=3, max_length=64)
    reviewed_on: date
    data_storage: Literal["private-local-only"]
    owner_acceptance: bool
    retrospective_completed: bool
    cycles: list[PilotCycle] = Field(min_length=4, max_length=4)
    team_scenarios: list[TeamScenario] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_pilot_contract(self) -> "E44E45BusinessPilotReceipt":
        if not _REFERENCE.fullmatch(self.participant_ref) or not _REFERENCE.fullmatch(
            self.company_ref
        ):
            raise ValueError(
                "pilot references must be opaque, non-personal identifiers"
            )
        if not self.owner_acceptance or not self.retrospective_completed:
            raise ValueError("pilot requires owner acceptance and retrospective")
        if self.data_storage != "private-local-only":
            raise ValueError("pilot data must remain private and local")
        areas = [cycle.area for cycle in self.cycles]
        if set(areas) != _AREAS or len(areas) != len(set(areas)):
            raise ValueError("pilot must cover each decision area exactly once")
        people_cycle = next(cycle for cycle in self.cycles if cycle.area == "people")
        if not people_cycle.people_consent:
            raise ValueError("People pilot cycle requires explicit consent")
        scenario_ids = {scenario.scenario_id for scenario in self.team_scenarios}
        if scenario_ids != {"cash-execution", "growth-cross-decision"}:
            raise ValueError("pilot requires both E45 comparison scenarios")
        return self


def validate_business_pilot(receipt: E44E45BusinessPilotReceipt) -> None:
    """Keep a named boundary for callers and future receipt versions."""
    E44E45BusinessPilotReceipt.model_validate(receipt.model_dump(mode="json"))
