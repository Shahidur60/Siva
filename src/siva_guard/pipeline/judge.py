from __future__ import annotations

from typing import List, Dict
from siva_guard.core.schema import IdentityEvidence, RiskResult, RiskReason
from siva_guard.pipeline.similarity import confusability



def judge_identity_set(evidences: List[IdentityEvidence]) -> RiskResult:
    reasons: List[RiskReason] = []
    per_identity: Dict[str, dict] = {}

    ids = [e.claim.claimed for e in evidences]
    n = len(ids)

    for i in range(n):
        for j in range(i + 1, n):
            c = confusability(ids[i], ids[j])
            if c["ratio"] is not None and c["ratio"] >= 0.92 and (c["lev"] is not None and c["lev"] <= 2):
                reasons.append(RiskReason(
                    code="IDENTIFIERS_CONFUSABLE",
                    severity="high",
                    message=f"Two claimed identifiers are extremely similar: '{ids[i]}' and '{ids[j]}'."
                ))

    missing_public = sum(1 for e in evidences if e.public is None)
    if missing_public == n:
        reasons.append(RiskReason(
            code="IN_APP_ONLY_LIMITATION",
            severity="medium",
            message="Only in-app identity info is available; substitution risk is harder to rule out without external evidence."
        ))

    risk = 0.10
    risk += 0.55 if any(r.code == "IDENTIFIERS_CONFUSABLE" for r in reasons) else 0.0
    risk += 0.15 if missing_public == n and n >= 2 else 0.0
    risk = min(1.0, risk)

    confidence = 0.75 if missing_public < n else 0.45

    for e in evidences:
        per_identity[e.claim.claimed] = {
            "platform": e.claim.platform,
            "mode": e.mode,
            "errors": e.errors,
            "has_public": e.public is not None,
        }

    return RiskResult(
        substitution_risk=risk,
        confidence=confidence,
        reasons=reasons,
        per_identity=per_identity
    )
