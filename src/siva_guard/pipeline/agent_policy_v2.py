from __future__ import annotations

from typing import Any, Dict, List


def decide_action_v2(metrics: Dict[str, Any], overall_risk: float) -> Dict[str, Any]:
    """
    Deterministic policy:
    - REQUEST_STRONGER_PROOF for high overall risk or weak evidence coverage
    - WARN for moderate risk
    - ALLOW for low risk
    """
    num = int(metrics.get("num_identities", 0) or 0)
    public_cov = float(metrics.get("public_coverage", 0.0) or 0.0)
    confusable = int(metrics.get("confusable_pairs", 0) or 0)

    reasons: List[str] = []

    if num > 1 and public_cov < 0.5:
        reasons.append("low_public_coverage_multi_identity")

    if confusable > 0:
        reasons.append("confusable_identifiers_present")

    # Risk thresholds
    if overall_risk >= 0.70:
        action = "REQUEST_STRONGER_PROOF"
    elif overall_risk >= 0.40:
        action = "WARN"
    else:
        action = "ALLOW"

    return {
        "action": action,
        "reasons": reasons,
        "metrics": metrics,
    }
