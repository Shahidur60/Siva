from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .state import CeremonyState


@dataclass(frozen=True)
class Plan:
    """
    A deterministic plan = ordered tool names.
    """
    tools: List[str]


class Planner:
    """
    Deterministic planner:
    choose the next tool(s) based on what is missing in state.
    """

    def plan(self, st: CeremonyState) -> Plan:
        tools: List[str] = []

        # 1) Need evidence collection first
        if not st.evidences:
            tools.append("collect_evidence")
            return Plan(tools)

        # 2) Need per_identity view (derived from evidences)
        if not st.per_identity:
            tools.append("build_per_identity")
            return Plan(tools)

        # 3) Need evidence graph + metrics
        if st.evidence_graph is None or not st.graph_metrics:
            tools.append("build_graph")
            return Plan(tools)

        # 4) Need risk
        if st.overall_risk is None:
            tools.append("score_risk")
            return Plan(tools)

        # 5) Need agent decision
        if st.agent is None:
            tools.append("decide_action")
            return Plan(tools)

        return Plan(tools=[])
