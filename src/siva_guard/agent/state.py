# from __future__ import annotations

# from dataclasses import dataclass, field
# from typing import Any, Dict, List, Optional

# from .trace import TraceLog


# @dataclass
# class CeremonyState:
#     identities: List[Any] = field(default_factory=list)

#     evidences: List[Any] = field(default_factory=list)
#     per_identity: Dict[str, Any] = field(default_factory=dict)

#     evidence_graph: Optional[Dict[str, Any]] = None
#     graph_metrics: Dict[str, Any] = field(default_factory=dict)

#     substitution_risk: float = 0.0
#     authenticity_risk: float = 0.0
#     overall_risk: float = 0.0
#     confidence: float = 0.0
#     reasons: List[Dict[str, Any]] = field(default_factory=list)

#     agent: Dict[str, Any] = field(default_factory=dict)
#     result: Dict[str, Any] = field(default_factory=dict)

#     # tracing
#     steps_run: int = 0
#     trace: TraceLog = field(default_factory=TraceLog)

#     # --- LLM augmentation outputs (new) ---
#     agent_planning_trace: List[Dict[str, Any]] = field(default_factory=list)
#     llm_annotations: Dict[str, Any] = field(default_factory=dict)
#     human_explanation: Optional[Dict[str, Any]] = None
# src/siva_guard/agent/state.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .trace import TraceLog


@dataclass
class CeremonyState:
    """
    Canonical shared state used by tools + runner.

    Backward-compatible with existing tools expecting:
      - state.request
      - state.claims / state.identities
      - state.trace.add(...)
      - state.steps_run / state.max_steps
      - state.result dict
    """

    request: Dict[str, Any]

    # step counters (tools may read these)
    steps_run: int = 0
    max_steps: int = 0

    # Backward-compatible aliases
    claims: List[Any] = field(default_factory=list)
    identities: List[Any] = field(default_factory=list)

    # Tool-side trace list (supports .add())
    trace: TraceLog = field(default_factory=TraceLog)

    # Optional baseline/debug storage
    baseline: Dict[str, Any] = field(default_factory=dict)

    # Pipeline artifacts populated by tools
    evidence: Any = None
    per_identity: Optional[Dict[str, Any]] = None
    evidence_graph: Optional[Dict[str, Any]] = None

    # Common outputs (score_risk / build_graph tools may populate these)
    substitution_risk: Optional[float] = None
    authenticity_risk: Optional[float] = None
    overall_risk: Optional[float] = None
    confidence: Optional[float] = None
    reasons: List[Dict[str, Any]] = field(default_factory=list)
    graph_metrics: Dict[str, Any] = field(default_factory=dict)
    agent: Dict[str, Any] = field(default_factory=dict)

    # LLM augmentation (optional, additive)
    agent_planning_trace: List[Dict[str, Any]] = field(default_factory=list)
    llm_annotations: Dict[str, Any] = field(default_factory=dict)
    human_explanation: Optional[Dict[str, Any]] = None

    # Final response payload
    result: Dict[str, Any] = field(default_factory=dict)

    # Runner caching
    tool_cache: Dict[str, Any] = field(default_factory=dict)
