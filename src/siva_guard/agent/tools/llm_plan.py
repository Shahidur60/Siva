from __future__ import annotations

from typing import Any, Dict

from ..config import AgentConfig
from ..state import CeremonyState
from ..trace import AgentTraceEvent
from .base import Tool

from siva_guard.llm.client import LLMClient
from siva_guard.llm.planner import plan_next_steps


class LLMPlanTool(Tool):
    name = "llm_plan"

    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        if not cfg.enable_llm:
            return {"skipped": True}

        llm = LLMClient(model=cfg.llm_model)
        decisions = plan_next_steps(
            llm,
            per_identity=st.per_identity,
            graph_metrics=st.graph_metrics,
            reasons=st.reasons,
            max_steps=cfg.llm_max_planner_steps,
        )
        st.agent_planning_trace = decisions
        st.result["agent_planning_trace"] = decisions

        st.trace.add(
            AgentTraceEvent(
                step=st.steps_run,
                tool=self.name,
                decision="planned",
                inputs={"llm_enabled": llm.enabled},
                outputs={"planning_steps": len(decisions)},
            )
        )
        return {"planning_steps": len(decisions), "llm_enabled": llm.enabled}
