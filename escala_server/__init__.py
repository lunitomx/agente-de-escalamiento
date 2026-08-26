"""Escala Server — Local HTTP server for coaching dashboards."""

from .project_memory import MemoryResult, ProjectMemoryRuntime
from .workspace import WorkspaceIndexer, create_contribution, create_workspace

__version__ = "0.1.0"

__all__ = [
    "MemoryResult",
    "ProjectMemoryRuntime",
    "WorkspaceIndexer",
    "create_contribution",
    "create_workspace",
]
