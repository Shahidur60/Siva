from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _get(d: Dict[str, Any], key: str, default=None):
    return d.get(key, default) if isinstance(d, dict) else default


def _extract_reason_codes(siva_output: Dict[str, Any]) -> List[str]:
    reasons = _get(siva_output, "reasons", []) or []
    out: List[str] = []
    for r in reasons:
        if isinstance(r, dict):
            code = r.get("code")
            if isinstance(code, str):
                out.append(code)
    return out


def _extract_agent_action(siva_output: Dict[str, Any]) -> Optional[str]:
    agent = _get(siva_output, "agent", {}) or {}
    action = _get(agent, "action", None)
    return action if isinstance(action, str) else None


def _extract_graph_metrics(siva_output: Dict[str, Any]) -> Dict[str, Any]:
    # prefer top-level graph_metrics if present
    gm = _get(siva_output, "graph_metrics", None)
    if isinstance(gm, dict):
        return gm
    # fallback to evidence_graph.metrics
    eg = _get(siva_output, "evidence_graph", {}) or {}
    metrics = _get(eg, "metrics", {}) or {}
    return metrics if isinstance(metrics, dict) else {}


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _as_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default


def judge_v1(siva_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Judge v1: deterministic, auditable verdict layer on top of SIVA output.

    Goal:
      - Only return FAKE when there is positive evidence of substitution / contradiction,
        NOT merely weak evidence (generic bios, no linkouts, etc.).
      - If evidence is weak/non-informative, abstain and emit LOW certainty.

    Output:
      verdict: REAL | FAKE
      certainty: HIGH | MEDIUM | LOW
      abstained: bool
      standard: evaluator definition
      explanation: primary reasons + supporting metrics
      siva_passthrough: minimal SIVA values for convenience
    """
    overall_risk = _as_float(_get(siva_output, "overall_risk", 0.0))
    authenticity_risk = _as_float(_get(siva_output, "authenticity_risk", 0.0))
    substitution_risk = _as_float(_get(siva_output, "substitution_risk", 0.0))
    confidence = _as_float(_get(siva_output, "confidence", 0.0))

    reason_codes = _extract_reason_codes(siva_output)
    agent_action = _extract_agent_action(siva_output) or "UNKNOWN"
    metrics = _extract_graph_metrics(siva_output)

    num_identities = _as_int(_get(metrics, "num_identities", 0))
    public_coverage = _as_float(_get(metrics, "public_coverage", 0.0))
    confusable_pairs = _as_int(_get(metrics, "confusable_pairs", 0))
    name_mismatch_pairs = _as_int(_get(metrics, "name_mismatch_pairs", 0))
    avatar_mismatch_pairs = _as_int(_get(metrics, "avatar_mismatch_pairs", 0))
    crosslink_hits = _as_int(_get(metrics, "crosslink_hits", 0))

    # ---- Standard evaluator definition (v1) ----
    standard = {
        "definition": "substitution_fake_or_contradiction",
        "evidence_scope": "public_profile_only",
        "policy": {
            "fake_requires_positive_substitution_evidence": True,
            "weak_evidence_alone_is_not_fake": True,
        },
        "criteria": {
            "min_identities_for_substitution": 2,
            "min_public_coverage": 0.50,
            "fake_overall_risk_threshold": 0.70,
            "fake_requires_confusable_pairs": True,
            "fake_requires_any_contradiction_signal": [
                "name_mismatch_pairs>0",
                "avatar_mismatch_pairs>0",
                "crosslink_hits==0",
            ],
        },
    }

    # ---- Decision logic ----
    # "Positive evidence" for substitution-style fake requires:
    # - multi-identity context
    # - confusable identifiers
    # - at least one contradiction/instability signal
    # - sufficiently high overall risk
    # - and at least moderate public coverage (avoid judging from nothing)
    contradiction = (name_mismatch_pairs > 0) or (avatar_mismatch_pairs > 0) or (crosslink_hits == 0)

    fake_high = (
        num_identities >= 2
        and public_coverage >= 0.50
        and confusable_pairs > 0
        and contradiction
        and overall_risk >= 0.70
    )

    fake_medium = (
        num_identities >= 2
        and public_coverage >= 0.50
        and confusable_pairs > 0
        and contradiction
        and overall_risk >= 0.55
    )

    # If single identity, do NOT call fake based solely on generic/weak evidence.
    # Instead, abstain with LOW certainty.
    if fake_high:
        verdict = "FAKE"
        certainty = "HIGH"
        abstained = False
    elif fake_medium:
        verdict = "FAKE"
        certainty = "MEDIUM"
        abstained = False
    else:
        verdict = "REAL"
        # If evidence is weak/non-informative or SIVA escalates, abstain.
        weak_evidence = ("generic_platform_bio" in reason_codes) or ("no_bio_linkouts" in reason_codes)
        if agent_action in ("WARN", "REQUEST_STRONGER_PROOF") or weak_evidence or public_coverage < 0.50:
            certainty = "LOW"
            abstained = True
        else:
            certainty = "MEDIUM"
            abstained = False

    # Primary reasons: reuse SIVA reasons as explanation payload (do not invent)
    primary_reasons: List[Dict[str, Any]] = []
    for r in (_get(siva_output, "reasons", []) or []):
        if isinstance(r, dict) and "code" in r:
            primary_reasons.append({"code": r.get("code"), "detail": r.get("detail")})

    supporting_metrics = {
        "overall_risk": overall_risk,
        "substitution_risk": substitution_risk,
        "authenticity_risk": authenticity_risk,
        "confidence": confidence,
        "num_identities": num_identities,
        "public_coverage": public_coverage,
        "confusable_pairs": confusable_pairs,
        "name_mismatch_pairs": name_mismatch_pairs,
        "avatar_mismatch_pairs": avatar_mismatch_pairs,
        "crosslink_hits": crosslink_hits,
        "agent_action": agent_action,
    }

    return {
        "verdict": verdict,
        "certainty": certainty,
        "abstained": abstained,
        "judge_version": "judge_v1",
        "standard": standard,
        "explanation": {
            "primary_reasons": primary_reasons,
            "supporting_metrics": supporting_metrics,
        },
        "siva_passthrough": {
            "overall_risk": overall_risk,
            "confidence": confidence,
            "action": agent_action,
        },
    }


def judge_from_siva_output(siva_output: Dict[str, Any]) -> Dict[str, Any]:
    # wrapper for API usage; future versions can switch on judge_version
    return judge_v1(siva_output)
