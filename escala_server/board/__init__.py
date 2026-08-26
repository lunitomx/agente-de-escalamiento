"""Synthetic, evidence-grounded board lens for ScaleUp."""

from .context import BoardContextBuilder, PortableKnowledgeHandler
from .contracts import AdviceItem, BoardResponse, CompanyFact, EvidencePacket, EvidenceRef
from .verne import VerneLensAdvisor, validate_profile
from .session import BoardHookResult, optional_board_review

__all__ = [
    "AdviceItem",
    "BoardContextBuilder",
    "BoardHookResult",
    "BoardResponse",
    "CompanyFact",
    "EvidencePacket",
    "EvidenceRef",
    "PortableKnowledgeHandler",
    "VerneLensAdvisor",
    "optional_board_review",
    "validate_profile",
]
