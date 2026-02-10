# src/siva_guard/pipeline/risk_v2.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from siva_guard.pipeline.single_identity_risk import score_single_identity


@dataclass
class RiskV2:
    substitution_risk: float
    authenticity_risk: float
    overall_risk: float
    confidence: float
    reasons: List[Dict[str, Any]]


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_risk_v2(graph_metrics: Dict[str, Any], per_identity: Dict[str, Any]) -> RiskV2:
    """
    Deterministic:
    - substitution_risk: set-based substitution risk (confusables, low coverage, mismatches)
    - authenticity_risk: per-identity low-trust signal (works even for single identity)
    - overall_risk: max(substitution_risk, authenticity_risk)
    - confidence: confidence in the decision given observable evidence quality
    """
    num = int(graph_metrics.get("num_identities", 0) or 0)
    public_cov = float(graph_metrics.get("public_coverage", 0.0) or 0.0)
    confusable = int(graph_metrics.get("confusable_pairs", 0) or 0)
    name_mismatch = int(graph_metrics.get("name_mismatch_pairs", 0) or 0)
    avatar_mismatch = int(graph_metrics.get("avatar_mismatch_pairs", 0) or 0)
    crosslinks = int(graph_metrics.get("crosslink_hits", 0) or 0)

    reasons: List[Dict[str, Any]] = []

    # -------------------------
    # A) Substitution risk
    # -------------------------
    substitution = 0.10

    if num > 1 and public_cov < 0.5:
        substitution += 0.25
        reasons.append({"code": "low_public_coverage", "detail": f"public_coverage={public_cov:.2f}"})

    if confusable > 0:
        substitution += 0.30
        reasons.append({"code": "confusable_identifiers", "detail": f"confusable_pairs={confusable}"})

    if name_mismatch > 0:
        substitution += 0.20
        reasons.append({"code": "name_mismatch_under_confusable", "detail": f"name_mismatch_pairs={name_mismatch}"})

    if avatar_mismatch > 0:
        substitution += 0.20
        reasons.append({"code": "avatar_mismatch_under_confusable", "detail": f"avatar_mismatch_pairs={avatar_mismatch}"})

    if crosslinks > 0:
        substitution -= 0.10
        reasons.append({"code": "crosslink_support", "detail": f"crosslink_hits={crosslinks}"})

    substitution = clamp01(substitution)

    # -------------------------
    # B) Authenticity risk (single-identity capable)
    # -------------------------
    authenticity = 0.0
    top_single_reasons: List[Dict[str, Any]] = []

    for _, item in per_identity.items():
        r = score_single_identity(item)
        if r.authenticity_risk > authenticity:
            authenticity = r.authenticity_risk
            top_single_reasons = r.reasons[:]  # keep the strongest identity's reasons

    authenticity = clamp01(authenticity)

    if authenticity > 0.25:
        reasons.append(
            {"code": "low_trust_single_identity_signals", "detail": f"authenticity_risk={authenticity:.2f}"}
        )
        # attach a few explainers (bounded)
        reasons.extend(top_single_reasons[:3])

    # -------------------------
    # C) Overall risk
    # -------------------------
    overall = max(substitution, authenticity)

    # -------------------------
    # D) Confidence (fix #2)
    # -------------------------
    # Baseline confidence mainly reflects evidence availability (public coverage),
    # reduced by collection errors.
    fetch_errors = 0
    for _, item in per_identity.items():
        errs = item.get("errors") or []
        if errs:
            fetch_errors += 1

    conf = 0.40 + 0.50 * public_cov  # ranges 0.40..0.90
    if fetch_errors > 0:
        conf -= min(0.20, 0.05 * fetch_errors)

    conf = clamp01(conf)

    # ✅ Fix #2: If we are flagging high authenticity risk AND evidence is weak/generic,
    # cap confidence so it doesn't look like we are "sure it's fake".
    if authenticity >= 0.70:
        reason_codes = {r.get("code") for r in reasons if isinstance(r, dict)}
        weak_evidence = (
            "generic_platform_bio" in reason_codes
            or "no_bio_linkouts" in reason_codes
            or "low_trust_single_identity_signals" in reason_codes
        )
        if weak_evidence:
            conf = min(conf, 0.75)

    return RiskV2(
        substitution_risk=substitution,
        authenticity_risk=authenticity,
        overall_risk=overall,
        confidence=conf,
        reasons=reasons,
    )
