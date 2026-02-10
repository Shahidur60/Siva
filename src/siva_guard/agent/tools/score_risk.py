from __future__ import annotations

from typing import Any, Dict

from siva_guard.pipeline.risk_v2 import compute_risk_v2

from ..trace import AgentTraceEvent
from ..state import CeremonyState
from ..config import AgentConfig
from .base import Tool


class ScoreRiskTool(Tool):
    name = "score_risk"

    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        risk2 = compute_risk_v2(st.graph_metrics, st.per_identity)

        st.substitution_risk = risk2.substitution_risk
        st.authenticity_risk = risk2.authenticity_risk
        st.overall_risk = risk2.overall_risk
        st.confidence = risk2.confidence
        st.reasons = risk2.reasons

        # Persist into the output payload so downstream tools (e.g., NextStepsTool)
        # and the API response have professional, self-contained fields.
        result = getattr(st, "result", None)
        if not isinstance(result, dict):
            result = {}
        result.update(
            {
                "substitution_risk": st.substitution_risk,
                "authenticity_risk": st.authenticity_risk,
                "overall_risk": st.overall_risk,
                "confidence": st.confidence,
                "reasons": st.reasons,
            }
        )
        st.result = result

        st.trace.add(
            AgentTraceEvent(
                step=st.steps_run,
                tool=self.name,
                decision="scored",
                inputs={"public_coverage": st.graph_metrics.get("public_coverage")},
                outputs={
                    "substitution_risk": st.substitution_risk,
                    "authenticity_risk": st.authenticity_risk,
                    "overall_risk": st.overall_risk,
                    "confidence": st.confidence,
                    "num_reasons": len(st.reasons),
                },
            )
        )
        return {"overall_risk": st.overall_risk, "confidence": st.confidence}
