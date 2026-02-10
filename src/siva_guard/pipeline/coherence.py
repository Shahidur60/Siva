from __future__ import annotations
from typing import Dict
from siva_guard.pipeline.evidence_graph import EvidenceGraph


def compute_coherence(graph: EvidenceGraph) -> Dict[str, float]:
    """
    Returns interpretable coherence metrics.
    """
    g = graph.graph

    num_nodes = g.number_of_nodes()
    has_public = sum(1 for _, d in g.nodes(data=True) if d.get("has_public"))

    # Handle similarity risk
    high_confusable_edges = 0
    for _, _, d in g.edges(data=True):
        if d.get("handle_similarity", 0) >= 0.92:
            high_confusable_edges += 1

    return {
        "num_identities": num_nodes,
        "public_coverage": has_public / num_nodes if num_nodes else 0.0,
        "confusable_pairs": high_confusable_edges,
    }
