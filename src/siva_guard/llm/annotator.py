from __future__ import annotations

import json
from typing import Any, Dict, List

from .client import LLMClient
from .schemas import LLMAnnotations


_ANNOTATE_INSTRUCTIONS = """
You are a cautious semantic annotator for a security verification system.

Output STRICT JSON (no markdown) with keys:
- bio_semantic_specificity: {label:"low|medium|high", confidence:0..1, evidence:string}
- name_quality: {label:"low|medium|high", confidence:0..1, evidence:string}
- linkout_expectation: {label:"low|medium|high", confidence:0..1, evidence:string}

Rules:
- Do NOT claim "fake". Do NOT infer identity beyond given text.
- Only judge specificity/quality of the provided bio/name/linkouts.
- evidence strings <= 180 characters.
"""


def annotate(
    llm: LLMClient,
    *,
    per_identity: Dict[str, Any],
    reasons: List[Dict[str, Any]],
) -> LLMAnnotations:
    payload = {
        "per_identity_summary": _summarize(per_identity),
        "reasons": reasons,
    }

    out = llm.text(instructions=_ANNOTATE_INSTRUCTIONS, user_input=json.dumps(payload), max_output_tokens=260)
    if not out:
        return {}

    try:
        obj = json.loads(out)
        return _sanitize(obj)
    except Exception:
        return {}


def _summarize(per_identity: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in (per_identity or {}).items():
        pub = (v or {}).get("public") or {}
        ui = (v or {}).get("ui") or {}
        out[k] = {
            "display_name": (pub.get("display_name") or ui.get("display_name") or "")[:120],
            "bio": (pub.get("bio") or "")[:320],
            "external_links": (pub.get("external_links") or [])[:8],
        }
    return out


def _sanitize(obj: Dict[str, Any]) -> LLMAnnotations:
    def clamp01(x: Any) -> float:
        try:
            v = float(x)
            return max(0.0, min(1.0, v))
        except Exception:
            return 0.0

    def clean_block(b: Any) -> Dict[str, Any]:
        if not isinstance(b, dict):
            return {"label": "low", "confidence": 0.0, "evidence": ""}
        label = str(b.get("label", "low"))
        if label not in ("low", "medium", "high"):
            label = "low"
        return {
            "label": label,
            "confidence": clamp01(b.get("confidence", 0.0)),
            "evidence": str(b.get("evidence", ""))[:180],
        }

    return {
        "bio_semantic_specificity": clean_block(obj.get("bio_semantic_specificity")),
        "name_quality": clean_block(obj.get("name_quality")),
        "linkout_expectation": clean_block(obj.get("linkout_expectation")),
    }
