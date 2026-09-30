"""Canonical capability catalog and deterministic public-intent routing.

E56 deliberately keeps the business procedures in the repository while exposing
only one public skill.  This module is the auditable seam between that public
conversation and the internal procedures: it validates the catalog, resolves
legacy aliases, and gives the orchestrator an explainable next capability.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG_PATH = REPOSITORY_ROOT / "escala-skills" / "catalog.yaml"
DEFAULT_LEGACY_ALIAS_PATH = (
    REPOSITORY_ROOT / ".claude" / "legacy-skills" / "e56-legacy-aliases.yaml"
)
LEGACY_PREFIX = "scale" + "up-"


class CatalogError(ValueError):
    """Raised when the catalog would make routing ambiguous or incomplete."""


class Capability(BaseModel):
    """One procedure preserved behind the ESCALA public front door."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    visibility: str
    owner: str
    disposition: str
    reason: str

    @model_validator(mode="after")
    def validate_lifecycle(self) -> Capability:
        if self.id != "escala" and not self.id.startswith("escala-"):
            raise ValueError("capability id must use the escala- prefix")
        if self.visibility not in {"public", "internal", "deprecated", "retired"}:
            raise ValueError("unknown capability visibility")
        if self.disposition not in {"keep", "internalize", "merge", "retire"}:
            raise ValueError("unknown Bitter Pill disposition")
        return self


class LegacyAlias(BaseModel):
    """A finite, visible compatibility mapping; it never owns logic itself."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    alias: str
    target: str
    sunset: str
    notice: str

    @model_validator(mode="after")
    def validate_alias(self) -> LegacyAlias:
        if not self.alias.startswith(LEGACY_PREFIX):
            raise ValueError("legacy alias has an invalid prefix")
        if not self.target.startswith("escala-"):
            raise ValueError("legacy alias target must use the escala- prefix")
        return self


class IntentRoute(BaseModel):
    """A deliberate conversational route, not a model guess or hidden prompt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    keywords: tuple[str, ...] = ()
    target: str
    message: str


class CapabilityCatalog(BaseModel):
    """Versioned catalog that controls the public surface of ESCALA."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int
    baseline: dict[str, int]
    public_entrypoint: str
    capabilities: tuple[Capability, ...]
    routes: tuple[IntentRoute, ...]

    @model_validator(mode="after")
    def validate_references(self) -> CapabilityCatalog:
        ids = [capability.id for capability in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate capability id")
        if self.public_entrypoint not in ids:
            raise ValueError("public entrypoint is not a capability")
        if self.capability(self.public_entrypoint).visibility != "public":
            raise ValueError("public entrypoint must be public")
        route_names = [route.id for route in self.routes]
        if len(route_names) != len(set(route_names)):
            raise ValueError("duplicate route id")
        for route in self.routes:
            if route.target not in ids:
                raise ValueError(f"route target missing: {route.target}")
        return self

    def capability(self, capability_id: str) -> Capability:
        for capability in self.capabilities:
            if capability.id == capability_id:
                return capability
        raise CatalogError(f"unknown_capability:{capability_id}")


@dataclass(frozen=True)
class RouteResult:
    """Explainable route returned to the public orchestrator."""

    capability_id: str
    reason: str
    message: str
    legacy_alias: str | None = None


def load_capability_catalog(path: Path = DEFAULT_CATALOG_PATH) -> CapabilityCatalog:
    """Load a closed catalog; malformed or missing data is never guessed."""

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CatalogError("catalog_unavailable") from exc
    if not isinstance(raw, dict):
        raise CatalogError("catalog_invalid")
    try:
        return CapabilityCatalog.model_validate(raw)
    except ValueError as exc:
        raise CatalogError(f"catalog_invalid:{exc}") from exc


def load_legacy_aliases(
    catalog: CapabilityCatalog,
    path: Path = DEFAULT_LEGACY_ALIAS_PATH,
) -> tuple[LegacyAlias, ...]:
    """Load compatibility names from the internal migration layer only."""

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CatalogError("legacy_aliases_unavailable") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("aliases"), list):
        raise CatalogError("legacy_aliases_invalid")
    try:
        aliases = tuple(LegacyAlias.model_validate(item) for item in raw["aliases"])
    except ValueError as exc:
        raise CatalogError(f"legacy_aliases_invalid:{exc}") from exc
    names = [alias.alias for alias in aliases]
    if len(names) != len(set(names)):
        raise CatalogError("legacy_aliases_invalid:duplicate")
    for alias in aliases:
        if alias.target not in {capability.id for capability in catalog.capabilities}:
            raise CatalogError(f"legacy_alias_target_missing:{alias.target}")
    return aliases


def validate_catalog_sources(
    catalog: CapabilityCatalog, skills_root: Path = DEFAULT_CATALOG_PATH.parent
) -> tuple[str, ...]:
    """Return deterministic errors for catalog/source drift.

    The public front door is a skill too.  Every skill folder below the canonical
    root must appear exactly once in the catalog, and each non-retired entry must
    point at a real ``SKILL.md``.  This makes accidental copies or silent removals
    observable in CI before they reach an installation.
    """

    source_ids = {
        path.parent.name
        for path in skills_root.glob("escala-*/SKILL.md")
        if path.is_file()
    }
    if (skills_root / "escala" / "SKILL.md").is_file():
        source_ids.add("escala")
    catalog_ids = {capability.id for capability in catalog.capabilities}
    errors: list[str] = []
    for missing in sorted(source_ids - catalog_ids):
        errors.append(f"source_not_cataloged:{missing}")
    for orphan in sorted(catalog_ids - source_ids):
        errors.append(f"catalog_skill_missing:{orphan}")
    if catalog.baseline.get("canonical_procedures") != 62:
        errors.append("baseline_canonical_procedures_mismatch")
    if catalog.baseline.get("legacy_aliases") != 39:
        errors.append("baseline_legacy_aliases_mismatch")
    return tuple(errors)


def route_request(
    request: str, catalog: CapabilityCatalog | None = None
) -> RouteResult:
    """Route a natural request while preserving uncertainty and compatibility.

    The function intentionally routes only the stable first decision.  A more
    specialized procedure is selected after the chosen capability loads the
    company's permitted context and asks a single focused question if needed.
    """

    active_catalog = catalog or load_capability_catalog()
    normalized = _normalize(request)
    alias = next(
        (
            item
            for item in load_legacy_aliases(active_catalog)
            if item.alias == normalized
        ),
        None,
    )
    if alias:
        return RouteResult(
            capability_id=alias.target,
            reason="legacy_alias",
            message=alias.notice,
            legacy_alias=alias.alias,
        )
    for route in active_catalog.routes:
        if any(_normalize(keyword) in normalized for keyword in route.keywords):
            return RouteResult(
                capability_id=route.target,
                reason=f"intent:{route.id}",
                message=route.message,
            )
    return RouteResult(
        capability_id="escala-welcome",
        reason="intent:clarify",
        message=(
            "Cuéntame qué te preocupa más hoy: tu equipo, tu rumbo, tu "
            "operación o tu efectivo. Empezaremos por una sola cosa."
        ),
    )


def public_install_skills(catalog: CapabilityCatalog | None = None) -> tuple[str, ...]:
    """The default installer surface: exactly the public front door."""

    active_catalog = catalog or load_capability_catalog()
    return tuple(
        capability.id
        for capability in active_catalog.capabilities
        if capability.visibility == "public"
    )


def _normalize(value: str) -> str:
    lowered = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", lowered.lower().strip().lstrip("/"))
