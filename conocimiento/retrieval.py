"""
Deterministic retrieval engine for the Scaling Up knowledge ontology.
Zero external dependencies — pure file-based, pure Python.
"""

from __future__ import annotations

import pathlib
from collections import deque
from typing import Iterator

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML required: pip install pyyaml") from e

_DEFAULT_KNOWLEDGE_DIR = pathlib.Path(__file__).parent


class KnowledgeGraph:
    """In-memory graph built from `.scaleup/knowledge/` YAML files.

    Load once, query many times — all graph traversals are O(E) worst case.
    """

    def __init__(self, knowledge_dir: str | pathlib.Path | None = None) -> None:
        self._dir = (
            pathlib.Path(knowledge_dir) if knowledge_dir else _DEFAULT_KNOWLEDGE_DIR
        )
        self._nodes: dict[str, dict] = {}
        self._by_decision: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}
        self._adjacency: dict[str, list[dict]] = {}  # id → [{type, target}]
        self._registry: list[dict] = []
        self._load()

    # ── Public API ─────────────────────────────────────────────────────────

    def get(self, node_id: str) -> dict | None:
        """Return a single node by ID, or None if not found."""
        return self._nodes.get(node_id)

    def query(
        self,
        decision: str | None = None,
        node_type: str | None = None,
    ) -> list[dict]:
        """Return nodes matching decision and/or type filters.

        Both filters are optional — omitting both returns all nodes.
        """
        if decision and node_type:
            d_ids = set(self._by_decision.get(decision, []))
            t_ids = set(self._by_type.get(node_type, []))
            ids = d_ids & t_ids
        elif decision:
            ids = set(self._by_decision.get(decision, []))
        elif node_type:
            ids = set(self._by_type.get(node_type, []))
        else:
            ids = set(self._nodes.keys())
        return [self._nodes[i] for i in sorted(ids)]

    def traverse(
        self,
        start_id: str,
        rel_type: str | None = None,
        depth: int = 1,
    ) -> list[dict]:
        """BFS traversal from start_id following edges of rel_type.

        Returns nodes reachable within `depth` hops (excluding start).
        If rel_type is None, follows all edge types.
        """
        if start_id not in self._nodes:
            return []
        visited: set[str] = {start_id}
        queue: deque[tuple[str, int]] = deque([(start_id, 0)])
        result: list[dict] = []
        while queue:
            current_id, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            for edge in self._adjacency.get(current_id, []):
                if rel_type and edge["type"] != rel_type:
                    continue
                target_id = edge["target"]
                if target_id in visited or target_id not in self._nodes:
                    continue
                visited.add(target_id)
                result.append(self._nodes[target_id])
                queue.append((target_id, current_depth + 1))
        return result

    def path(self, from_id: str, to_id: str) -> list[dict]:
        """Return shortest undirected path between two nodes (BFS).

        Returns empty list if no path exists.
        """
        if from_id not in self._nodes or to_id not in self._nodes:
            return []
        if from_id == to_id:
            return [self._nodes[from_id]]
        parent: dict[str, str | None] = {from_id: None}
        queue: deque[str] = deque([from_id])
        while queue:
            current = queue.popleft()
            for edge in self._adjacency.get(current, []):
                nb = edge["target"]
                if nb in parent or nb not in self._nodes:
                    continue
                parent[nb] = current
                if nb == to_id:
                    return self._reconstruct_path(parent, from_id, to_id)
                queue.append(nb)
        return []

    def worksheets(self, decision: str | None = None) -> list[dict]:
        """Return worksheet registry entries, optionally filtered by decision.

        Uses the pre-built registry index (O(1) per entry); faster than
        scanning all nodes when you only need worksheet metadata.
        """
        if not decision:
            return list(self._registry)
        return [w for w in self._registry if w.get("decision") == decision]

    def neighbors(self, node_id: str) -> list[dict]:
        """Return all direct neighbors of a node (one-hop, any edge type)."""
        return self.traverse(node_id, rel_type=None, depth=1)

    def edges(self, node_id: str) -> list[dict]:
        """Return raw edge descriptors [{type, target}] for a node."""
        return list(self._adjacency.get(node_id, []))

    def all_ids(self) -> list[str]:
        """Return sorted list of all node IDs in the graph."""
        return sorted(self._nodes.keys())

    def stats(self) -> dict:
        """Return basic graph statistics."""
        total_edges = sum(len(v) for v in self._adjacency.values())
        cross_decision_edges = sum(
            1
            for nid, edges in self._adjacency.items()
            for e in edges
            if (
                nid in self._nodes
                and e["target"] in self._nodes
                and self._nodes[nid].get("decision")
                != self._nodes[e["target"]].get("decision")
                and self._nodes[nid].get("decision") is not None
                and self._nodes[e["target"]].get("decision") is not None
            )
        )
        return {
            "total_nodes": len(self._nodes),
            "total_edges": total_edges,
            "cross_decision_edges": cross_decision_edges,
            "decisions": {d: len(ids) for d, ids in self._by_decision.items()},
            "node_types": {t: len(ids) for t, ids in self._by_type.items()},
            "worksheets_in_registry": len(self._registry),
        }

    # ── Internal ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        for path in self._dir.rglob("*.yaml"):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict) or "id" not in data:
                continue
            node_id: str = data["id"]
            self._nodes[node_id] = data
            if decision := data.get("decision"):
                self._by_decision.setdefault(decision, []).append(node_id)
            if node_type := data.get("type"):
                self._by_type.setdefault(node_type, []).append(node_id)
            for rel in data.get("relationships", []) or []:
                if "target" in rel and "type" in rel:
                    self._adjacency.setdefault(node_id, []).append(
                        {"type": rel["type"], "target": rel["target"]}
                    )
        # Load worksheet registry for fast worksheet queries
        registry_path = self._dir / "registry" / "worksheets.yaml"
        if registry_path.exists():
            try:
                reg = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
                if isinstance(reg, dict):
                    self._registry = reg.get("worksheets", [])
            except Exception:
                pass

    def _reconstruct_path(
        self, parent: dict[str, str | None], from_id: str, to_id: str
    ) -> list[dict]:
        path: list[dict] = []
        current: str | None = to_id
        while current is not None:
            path.append(self._nodes[current])
            current = parent[current]
        path.reverse()
        return path


def _iter_nodes(graph: KnowledgeGraph) -> Iterator[dict]:
    for nid in graph.all_ids():
        node = graph.get(nid)
        if node:
            yield node


# Module-level singleton — import and use directly for simple scripts
_default: KnowledgeGraph | None = None


def default_graph() -> KnowledgeGraph:
    """Return (lazily initialized) module-level graph from default knowledge dir."""
    global _default
    if _default is None:
        _default = KnowledgeGraph()
    return _default
