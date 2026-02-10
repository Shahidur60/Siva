from __future__ import annotations

from typing import Any, Dict

from siva_guard.pipeline.evidence_graph_v2 import build_evidence_graph_v2

from ..trace import AgentTraceEvent
from ..state import CeremonyState
from ..config import AgentConfig
from .base import Tool


class BuildGraphTool(Tool):
    name = "build_graph"

    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        g2 = build_evidence_graph_v2(st.per_identity)

        st.graph_metrics = dict(g2.metrics)
        st.evidence_graph = {
            "nodes": g2.nodes_out,
            "edges": g2.edges_out,
            "metrics": g2.metrics,
        }

        st.trace.add(
            AgentTraceEvent(
                step=st.steps_run,
                tool=self.name,
                decision="built",
                inputs={"num_identities": st.graph_metrics.get("num_identities", 0)},
                outputs={
                    "public_coverage": st.graph_metrics.get("public_coverage"),
                    "confusable_pairs": st.graph_metrics.get("confusable_pairs"),
                    "crosslink_hits": st.graph_metrics.get("crosslink_hits"),
                },
            )
        )
        return {"metrics": st.graph_metrics}
