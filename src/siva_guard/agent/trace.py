# from __future__ import annotations

# from dataclasses import dataclass, field
# from datetime import datetime, timezone
# from typing import Any, Dict, List, Optional


# @dataclass
# class AgentTraceEvent:
#     step: int
#     tool: str
#     decision: str
#     inputs: Dict[str, Any] = field(default_factory=dict)
#     outputs: Dict[str, Any] = field(default_factory=dict)
#     note: Optional[str] = None
#     ts_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# @dataclass
# class AgentTrace:
#     events: List[AgentTraceEvent] = field(default_factory=list)

#     def add(self, ev: AgentTraceEvent) -> None:
#         self.events.append(ev)

#     def to_list(self) -> List[Dict[str, Any]]:
#         return [ev.__dict__ for ev in self.events]
# src/siva_guard/agent/trace.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


class TraceLog(list):
    """
    Backward-compatible trace container.
    Tools may call state.trace.add(...)
    Runner may call list(state.trace)
    """

    def add(self, item):  # type: ignore[override]
        self.append(item)


@dataclass
class AgentTraceEvent:
    """
    Optional structured trace event (some tools create these).
    If your tools don't use it, it still doesn't hurt to have it.
    """
    step: int
    tool: str
    decision: str
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    ts_utc: Optional[str] = None
