from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ...pipeline.next_steps import generate_next_steps


@dataclass
class NextStepsTool:
    name: str = "next_steps"

    def run(self, state: Any) -> Dict[str, Any]:
        """
        Attaches result["next_steps"] deterministically based on:
          - result["agent"]["action"] (preferred)
          - result["reasons"]         (preferred)
        Falls back to state.agent/state.reasons if needed.
        """
        result = getattr(state, "result", None)
        if not isinstance(result, dict):
            result = {}

        agent = result.get("agent") or getattr(state, "agent", None) or {}
        action = (agent or {}).get("action") or "WARN"

        reasons = result.get("reasons")
        if reasons is None:
            reasons = getattr(state, "reasons", None) or []

        result["next_steps"] = generate_next_steps(action=action, reasons=reasons)
        state.result = result
        return {"next_steps_count": len(result["next_steps"])}
