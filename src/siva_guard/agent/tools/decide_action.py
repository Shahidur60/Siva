from __future__ import annotations

from typing import Any, Dict

from siva_guard.pipeline.agent_policy_v2 import decide_action_v2

from ..config import AgentConfig
from ..state import CeremonyState
from ..trace import AgentTraceEvent
from .base import Tool


class DecideActionTool(Tool):
    """
    Deterministically decide action and persist a coherent, client-friendly result.

    Professionalism guarantees:
      - result includes agent {action, reasons, metrics}
      - agent.reasons mirrors top-level reasons (no empty mismatch)
      - risk fields + evidence artifacts are present in the main response
    """

    name = "decide_action"

    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        overall = float(getattr(st, "overall_risk", 0.0) or 0.0)
        metrics = getattr(st, "graph_metrics", None) or {}

        # 1) deterministic policy decision
        st.agent = decide_action_v2(metrics, overall)

        # 2) attach reasons so agent payload is self-contained
        reasons = getattr(st, "reasons", None)
        if reasons is None:
            reasons = []
        st.agent["reasons"] = reasons

        # 3) write a coherent top-level output contract
        result = getattr(st, "result", None)
        if not isinstance(result, dict):
            result = {}

        # mirror risk fields for robustness
        if getattr(st, "substitution_risk", None) is not None:
            result["substitution_risk"] = st.substitution_risk
        if getattr(st, "authenticity_risk", None) is not None:
            result["authenticity_risk"] = st.authenticity_risk
        if getattr(st, "overall_risk", None) is not None:
            result["overall_risk"] = st.overall_risk
        if getattr(st, "confidence", None) is not None:
            result["confidence"] = st.confidence

        result["reasons"] = reasons

        # include evidence artifacts
        if getattr(st, "per_identity", None) is not None:
            result["per_identity"] = st.per_identity
        if getattr(st, "evidence_graph", None) is not None:
            result["evidence_graph"] = st.evidence_graph
        if getattr(st, "graph_metrics", None) is not None:
            result["graph_metrics"] = st.graph_metrics

        # agent decision
        result["agent"] = st.agent

        st.result = result

        # trace event
        st.trace.add(
            AgentTraceEvent(
                step=st.steps_run,
                tool=self.name,
                decision="decided",
                inputs={"overall_risk": overall},
                outputs={"action": (st.agent or {}).get("action")},
            )
        )

        return {"agent_action": (st.agent or {}).get("action")}
