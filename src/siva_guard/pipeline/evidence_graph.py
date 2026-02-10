from __future__ import annotations
from typing import List, Dict, Tuple
import networkx as nx

from siva_guard.core.schema import IdentityEvidence
from siva_guard.pipeline.similarity import confusability


class EvidenceGraph:
    """
    Graph where:
    - nodes = identities
    - edges = similarity / coherence signals
    """

    def __init__(self, evidences: List[IdentityEvidence]):
        self.evidences = evidences
        self.graph = nx.Graph()
        self._build()

    def _build(self):
        # Add nodes
        for ev in self.evidences:
            self.graph.add_node(
                ev.claim.claimed,
                platform=ev.claim.platform,
                has_public=(ev.public is not None),
                display_name=ev.public.display_name if ev.public else ev.claim.ui.display_name,
                avatar_url=ev.public.avatar_url if ev.public else None,
            )

        # Add edges (pairwise analysis)
        for i in range(len(self.evidences)):
            for j in range(i + 1, len(self.evidences)):
                a = self.evidences[i]
                b = self.evidences[j]

                sim = confusability(
                    a.claim.claimed,
                    b.claim.claimed
                )

                if sim["ratio"] is not None:
                    self.graph.add_edge(
                        a.claim.claimed,
                        b.claim.claimed,
                        handle_similarity=sim["ratio"],
                        edit_distance=sim["lev"],
                    )

    def summary(self) -> Dict:
        return {
            "nodes": list(self.graph.nodes(data=True)),
            "edges": list(self.graph.edges(data=True)),
        }
