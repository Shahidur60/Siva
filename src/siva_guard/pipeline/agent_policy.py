from __future__ import annotations
from typing import Dict


def agent_decision(metrics: Dict[str, float]) -> Dict:
    """
    Deterministic agent policy (NO LLM).
    """
    action = "ALLOW"
    reasons = []

    if metrics["confusable_pairs"] > 0:
        action = "WARN"
        reasons.append("Multiple identities are highly confusable.")

    if metrics["public_coverage"] < 0.5 and metrics["num_identities"] > 1:
        action = "REQUEST_STRONGER_PROOF"
        reasons.append("Insufficient public evidence across identities.")

    return {
        "action": action,
        "reasons": reasons,
        "metrics": metrics,
    }
