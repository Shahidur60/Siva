from __future__ import annotations

from typing import Dict

from .config import AgentConfig
from .planner import Planner
from .state import CeremonyState

from .tools.collect_evidence import CollectEvidenceTool
from .tools.build_per_identity import BuildPerIdentityTool
from .tools.build_graph import BuildGraphTool
from .tools.score_risk import ScoreRiskTool
from .tools.decide_action import DecideActionTool


class Executor:
    """
    Plan → Act → Observe loop with budgets.
    Deterministic, bounded, traceable.
    """

    def __init__(self) -> None:
        self.planner = Planner()
        self.tools: Dict[str, object] = {
            "collect_evidence": CollectEvidenceTool(),
            "build_per_identity": BuildPerIdentityTool(),
            "build_graph": BuildGraphTool(),
            "score_risk": ScoreRiskTool(),
            "decide_action": DecideActionTool(),
        }

    def run(self, st: CeremonyState, cfg: AgentConfig) -> CeremonyState:
        while (not st.done()) and st.steps_run < cfg.max_steps:
            plan = self.planner.plan(st)
            if not plan.tools:
                break

            # One tool per step (simple, auditable)
            tool_name = plan.tools[0]
            tool = self.tools.get(tool_name)
            if tool is None:
                break

            st.steps_run += 1
            tool.run(st, cfg)

        return st
