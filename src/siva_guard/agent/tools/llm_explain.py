from __future__ import annotations

from typing import Any, Dict

from ..config import AgentConfig
from ..state import CeremonyState
from ..trace import AgentTraceEvent
from .base import Tool

from siva_guard.llm.client import LLMClient
from siva_guard.llm.explainer import explain


class LLMExplainTool(Tool):
    name = "llm_explain"

    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        if not cfg.enable_llm:
            return {"skipped": True}

        llm = LLMClient(model=cfg.llm_model)
        action = (st.agent or {}).get("action") or "WARN"

        hx = explain(
            llm,
            action=action,
            reasons=st.reasons,
            per_identity=st.per_identity,
            graph_metrics=st.graph_metrics,
        )

        st.human_explanation = hx
        if hx is not None:
            st.result["human_explanation"] = hx

        st.trace.add(
            AgentTraceEvent(
                step=st.steps_run,
                tool=self.name,
                decision="explained" if hx else "skipped",
                inputs={"llm_enabled": llm.enabled},
                outputs={"has_explanation": bool(hx)},
            )
        )
        return {"has_explanation": bool(hx), "llm_enabled": llm.enabled}
