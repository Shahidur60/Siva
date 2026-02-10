from __future__ import annotations

import json
from typing import Any, Dict, List

from .client import LLMClient
from .schemas import HumanExplanation


_EXPLAIN_INSTRUCTIONS = """
You write concise, grounded security explanations.

Output STRICT JSON (no markdown) with keys:
- summary: string (<=180 chars)
- why: array of 2-4 short bullets (<=120 chars each)
- what_to_do_next: string (<=180 chars)
- safety_note: string (<=180 chars)

Rules:
- Do NOT say the identity is real/fake.
- Only explain the deterministic reasons provided.
- Use cautious language like "signals suggest" / "evidence is limited".
"""


def explain(
    llm: LLMClient,
    *,
    action: str,
    reasons: List[Dict[str, Any]],
    per_identity: Dict[str, Any],
    graph_metrics: Dict[str, Any],
) -> HumanExplanation | None:
    payload = {
        "action": action,
        "reasons": reasons,
        "per_identity_summary": _summarize(per_identity),
        "graph_metrics": graph_metrics,
    }

    out = llm.text(instructions=_EXPLAIN_INSTRUCTIONS, user_input=json.dumps(payload), max_output_tokens=320)
    if not out:
        return None

    try:
        obj = json.loads(out)
        return _sanitize(obj)
    except Exception:
        return None


def _summarize(per_identity: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in (per_identity or {}).items():
        pub = (v or {}).get("public") or {}
        ui = (v or {}).get("ui") or {}
        out[k] = {
            "platform": v.get("platform"),
            "display_name": (pub.get("display_name") or ui.get("display_name") or "")[:120],
            "bio_present": bool(pub.get("bio")),
            "external_links_count": len(pub.get("external_links") or []),
        }
    return out


def _sanitize(obj: Dict[str, Any]) -> HumanExplanation:
    why = obj.get("why", [])
    if not isinstance(why, list):
        why = []
    why2 = [str(x)[:120] for x in why[:4]]

    return {
        "summary": str(obj.get("summary", ""))[:180],
        "why": why2,
        "what_to_do_next": str(obj.get("what_to_do_next", ""))[:180],
        "safety_note": str(obj.get("safety_note", ""))[:180],
    }
