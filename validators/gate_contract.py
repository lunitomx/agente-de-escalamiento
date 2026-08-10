"""Local gate boundary types owned by the ESCALA package.

RaiSE passes a structurally compatible context to entry-point gates.  Keeping
the small data contract here prevents the product and its tests from importing
RaiSE implementation modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GateContext:
    """Context required by ESCALA's qualification gates."""

    gate_id: str
    working_dir: Path = field(default_factory=Path.cwd)
    extra_args: tuple[str, ...] = field(default_factory=tuple)
    workflow_point: str | None = None
    changed_files: tuple[Path, ...] | None = None
    session_id: str | None = None
    issue_id: str | None = None


@dataclass(frozen=True)
class GateResult:
    """Structured result returned by ESCALA's qualification gates."""

    passed: bool
    gate_id: str
    message: str = ""
    details: tuple[str, ...] = ()
    advisory: bool = False
    skipped: bool = False
