from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple


@dataclass(frozen=True)
class NextStep:
    code: str
    title: str
    detail: str
    priority: int  # lower is higher priority


# Deterministic mapping: reason_code -> list of NextStep templates
_REASON_TO_STEPS: Dict[str, List[NextStep]] = {
    "facebook_numeric_id_profile": [
        NextStep(
            code="request_in_band_confirmation",
            title="Request in-band confirmation",
            detail="Ask the person to send a one-time phrase from that Facebook account (DM/comment) to confirm control.",
            priority=1,
        ),
        NextStep(
            code="temporary_bio_crosslink",
            title="Request a temporary bio crosslink",
            detail="Ask them to add a temporary crosslink in the bio (e.g., a URL/@handle you specify) and re-run verification.",
            priority=2,
        ),
    ],
    "no_bio_linkouts": [
        NextStep(
            code="add_bio_linkout",
            title="Ask them to add a bio linkout",
            detail="Ask them to add a URL or @handle in the bio that links to another identity or a stable website, then re-run verification.",
            priority=1,
        ),
    ],
    "generic_platform_bio": [
        NextStep(
            code="ask_for_specific_bio_signal",
            title="Request a specific, non-template bio signal",
            detail="Ask them to add a short, unique phrase or reference (time-bounded) to the bio, then re-run verification.",
            priority=2,
        ),
    ],
    "repeated_name_tokens": [
        NextStep(
            code="request_secondary_identity",
            title="Request a second identity for cross-checking",
            detail="Ask for a second account (e.g., Instagram/GitHub/website) to improve public coherence checks.",
            priority=2,
        ),
    ],
    "missing_avatar_url": [
        NextStep(
            code="request_avatar_or_second_identity",
            title="Request an additional corroboration signal",
            detail="Because avatar evidence is missing, request a second identity or a temporary crosslink to strengthen verification.",
            priority=5,
        ),
    ],

    # ---- Set-level substitution signals ----
    "low_public_coverage": [
        NextStep(
            code="request_screenshot_or_public_view",
            title="Request a public-view screenshot",
            detail="Ask for a screenshot of the profile page (public-view) or a stable public link to improve evidence coverage.",
            priority=1,
        ),
        NextStep(
            code="add_second_identity",
            title="Request a second identity",
            detail="Ask them to provide a second identity so SIVA can compute coherence across identities.",
            priority=2,
        ),
    ],
    "confusable_identifiers": [
        NextStep(
            code="require_stronger_proof_before_accept",
            title="Require stronger proof before accepting",
            detail="Do not rely on identifiers alone; require crosslinks or in-band confirmation before proceeding.",
            priority=1,
        ),
        NextStep(
            code="temporary_mutual_crosslink",
            title="Request mutual crosslinking",
            detail="Ask them to reference Identity A from Identity B (bio link or @mention) and re-run verification.",
            priority=2,
        ),
    ],

    # These are the codes emitted by risk_v2.py
    "name_mismatch_under_confusable": [
        NextStep(
            code="resolve_name_discrepancy",
            title="Resolve the name discrepancy",
            detail="Confusable identifiers but mismatching names: request a temporary crosslink or in-band confirmation.",
            priority=2,
        ),
    ],
    "avatar_mismatch_under_confusable": [
        NextStep(
            code="resolve_avatar_discrepancy",
            title="Resolve the avatar discrepancy",
            detail="Confusable identifiers but mismatching avatars: request a temporary crosslink or in-band confirmation.",
            priority=1,
        ),
    ],

    # Higher-level “single identity weak evidence” umbrella code
    "low_trust_single_identity_signals": [
        NextStep(
            code="strengthen_single_identity_proof",
            title="Strengthen proof for this identity",
            detail="Because public signals are weak/generic, request an in-band confirmation or a temporary bio crosslink.",
            priority=1,
        ),
    ],

    # Positive evidence: crosslink exists. Usually no escalation needed, but provide guidance for cautious users.
    "crosslink_support": [
        NextStep(
            code="crosslink_observed",
            title="Crosslink evidence observed",
            detail="SIVA observed crosslinking evidence. If this is high impact, still consider a lightweight in-band confirmation.",
            priority=20,
        ),
    ],
}


_ACTION_DEFAULTS: Dict[str, List[NextStep]] = {
    "REQUEST_STRONGER_PROOF": [
        NextStep(
            code="stronger_proof_required",
            title="Stronger proof required",
            detail="Ask for crosslink evidence or in-band confirmation before proceeding.",
            priority=0,
        ),
    ],
    "WARN": [
        NextStep(
            code="proceed_with_caution",
            title="Proceed with caution",
            detail="If this is a high-impact decision, request a temporary crosslink or second identity as a lightweight check.",
            priority=10,
        ),
    ],
    "ALLOW": [],
}


def generate_next_steps(
    action: str,
    reasons: Iterable[dict],
    *,
    max_steps: int = 6,
) -> List[dict]:
    """
    Deterministically generate actionable next steps from agent action + reason codes.

    Returns list of dicts for JSON friendliness:
    [{code, title, detail}, ...]
    """
    reason_codes: List[str] = []
    for r in reasons or []:
        code = (r or {}).get("code")
        if isinstance(code, str) and code:
            reason_codes.append(code)

    seen: Set[str] = set()
    collected: List[Tuple[int, NextStep]] = []

    # 1) action defaults
    for st in _ACTION_DEFAULTS.get(action, []):
        if st.code not in seen:
            seen.add(st.code)
            collected.append((st.priority, st))

    # 2) reason-based steps
    for rc in reason_codes:
        for st in _REASON_TO_STEPS.get(rc, []):
            if st.code not in seen:
                seen.add(st.code)
                collected.append((st.priority, st))

    collected.sort(key=lambda x: (x[0], x[1].code))

    out: List[dict] = []
    for _, st in collected[:max_steps]:
        out.append({"code": st.code, "title": st.title, "detail": st.detail})

    return out
