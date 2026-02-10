from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


class PlannerDecision(TypedDict):
    step: int
    planner_decision: str
    justification: str


class LLMAnnotations(TypedDict, total=False):
    bio_semantic_specificity: Dict[str, Any]   # {"label": "low|medium|high", "confidence": 0..1, "evidence": "..."}
    name_quality: Dict[str, Any]               # {"label": "...", "confidence": 0..1, "evidence": "..."}
    linkout_expectation: Dict[str, Any]        # {"label": "...", "confidence": 0..1, "evidence": "..."}


class HumanExplanation(TypedDict):
    summary: str
    why: List[str]
    what_to_do_next: str
    safety_note: str
