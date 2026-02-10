from __future__ import annotations

import json
from typing import Any, Dict, List

from .client import LLMClient
from .schemas import PlannerDecision


_PLANNER_INSTRUCTIONS = """
You are a security verification planner.

You must output STRICT JSON (no markdown) with keys:
- decisions: array of objects {step:int, planner_decision:str, justification:str}

Constraints:
- You do NOT decide allow/deny. You do NOT claim "fake".
- You only suggest what checks to attempt next given current evidence.
- Keep each justification <= 200 characters.
- Use conservative language and assume evidence can be incomplete.

Allowed planner_decision values:
- "stop"
- "parse_external_links"
- "reverse_link_check"
- "request_secondary_identity"
- "request_temporary_bio_crosslink"
- "request_in_band_confirmation"
"""


def plan_next_steps(
    llm: LLMClient,
    *,
    per_identity: Dict[str, Any],
    graph_metrics: Dict[str, Any],
    reasons: List[Dict[str, Any]],
    max_steps: int = 3,
) -> List[PlannerDecision]:
    """
    Returns a small planning trace. If LLM disabled/unavailable returns empty list.
    """
    payload = {
        "per_identity_summary": _summarize_per_identity(per_identity),
        "graph_metrics": graph_metrics,
        "reasons": reasons,
        "max_steps": max_steps,
    }

    out = llm.text(instructions=_PLANNER_INSTRUCTIONS, user_input=json.dumps(payload), max_output_tokens=300)
    if not out:
        return []

    try:
        obj = json.loads(out)
        decisions = obj.get("decisions", [])
        # hard sanitize
        cleaned: List[PlannerDecision] = []
        for d in decisions[:max_steps]:
            cleaned.append(
                {
                    "step": int(d.get("step", len(cleaned) + 1)),
                    "planner_decision": str(d.get("planner_decision", "stop"))[:64],
                    "justification": str(d.get("justification", ""))[:200],
                }
            )
        return cleaned
    except Exception:
        return []


def _summarize_per_identity(per_identity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimize what we send to the LLM (privacy + cost + reproducibility).
    Only include high-level evidence, not raw HTML.
    """
    out: Dict[str, Any] = {}
    for k, v in (per_identity or {}).items():
        pub = (v or {}).get("public") or {}
        ui = (v or {}).get("ui") or {}
        out[k] = {
            "platform": v.get("platform"),
            "has_public": v.get("has_public"),
            "display_name": pub.get("display_name") or ui.get("display_name"),
            "bio": (pub.get("bio") or "")[:240],
            "avatar_present": bool(pub.get("avatar_url") or ui.get("avatar_url")),
            "external_links_count": len(pub.get("external_links") or []),
        }
    return out
