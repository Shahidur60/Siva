from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import re


@dataclass
class SingleIdentityRisk:
    authenticity_risk: float
    reasons: List[Dict[str, Any]]


# Generic/template bio snippets (deterministic, low false-positive)
_GENERIC_BIO_PATTERNS = [
    # Facebook OG template pattern
    "is on facebook. join facebook to connect with",
    "facebook gives people the power to share",
    # Instagram / LinkedIn common template phrases (kept minimal)
    "see instagram photos and videos from",
    "view",
    "profile",
    "on linkedin",
]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _norm_platform(p: Any) -> str:
    """
    Your output sometimes has 'Platform.FACEBOOK' (Enum leakage).
    Normalize to simple lowercase keyword.
    """
    s = str(p or "").lower()
    if "facebook" in s:
        return "facebook"
    if "instagram" in s:
        return "instagram"
    if "linkedin" in s:
        return "linkedin"
    if "github" in s:
        return "github"
    if "tiktok" in s:
        return "tiktok"
    if "youtube" in s:
        return "youtube"
    if s in ("x", "twitter") or "twitter" in s:
        return "x"
    return s


def _is_generic_bio(bio: str) -> bool:
    b = (bio or "").strip().lower()
    if not b:
        return True
    return any(p in b for p in _GENERIC_BIO_PATTERNS)


def _name_repetition_score(name: str) -> float:
    """
    Detect repeated tokens like:
      - 'X X'  -> 1.0
      - 'A B A B' -> 0.8
    Returns 0..1
    """
    t = re.sub(r"\s+", " ", (name or "").strip())
    if not t:
        return 0.0
    toks = t.split(" ")
    if len(toks) < 2:
        return 0.0

    # exact immediate repetition
    if len(toks) >= 2 and toks[0] == toks[1]:
        return 1.0

    # repeated sequence: first half == second half (e.g., "A B A B")
    if len(toks) % 2 == 0:
        half = len(toks) // 2
        if toks[:half] == toks[half:]:
            return 0.8

    return 0.0


def score_single_identity(per_identity_item: Dict[str, Any]) -> SingleIdentityRisk:
    """
    Deterministic single-identity scoring using extracted evidence only.
    Does NOT claim 'fake'. Produces a low-trust / weak-evidence signal.
    """
    platform = _norm_platform(per_identity_item.get("platform"))
    claimed = per_identity_item.get("claimed") or ""
    pub = per_identity_item.get("public") or {}
    ui = per_identity_item.get("ui") or {}

    display_name = (pub.get("display_name") or ui.get("display_name") or "").strip()
    bio = (pub.get("bio") or ui.get("snippet") or "").strip()
    avatar_url = (pub.get("avatar_url") or ui.get("avatar_url") or "").strip()

    reasons: List[Dict[str, Any]] = []
    risk = 0.10  # base

    # 1) Facebook numeric-id URL pattern (weak binding, easy to substitute)
    # This is NOT a "fake" claim; it's a deterministic low-trust signal.
    if platform == "facebook":
        if "profile.php" in claimed and "id=" in claimed:
            risk += 0.20
            reasons.append(
                {"code": "facebook_numeric_id_profile", "detail": "profile.php?id=... pattern"}
            )

    # 2) Generic/template bio
    if _is_generic_bio(bio):
        risk += 0.20
        reasons.append(
            {"code": "generic_platform_bio", "detail": "bio looks like platform template / non-specific"}
        )

    # 3) Repeated name tokens
    rep = _name_repetition_score(display_name)
    if rep > 0:
        risk += 0.15 * rep
        reasons.append({"code": "repeated_name_tokens", "detail": f"repetition_score={rep:.2f}"})

    # 4) No linkouts / crosslinks visible
    # Prefer structured fields if present; otherwise fallback to raw bio
    bio_link_domains = per_identity_item.get("bio_link_domains")
    bio_link_handles = per_identity_item.get("bio_link_handles")
    external_links = pub.get("external_links") or per_identity_item.get("external_links") or []

    if bio_link_domains is not None or bio_link_handles is not None:
        if not (bio_link_domains or bio_link_handles or external_links):
            risk += 0.10
            reasons.append({"code": "no_bio_linkouts", "detail": "no URLs or @handles in bio"})
    else:
        if ("http://" not in bio.lower()) and ("https://" not in bio.lower()) and ("@" not in bio) and not external_links:
            risk += 0.10
            reasons.append({"code": "no_bio_linkouts", "detail": "no URLs or @handles in bio"})

    # 5) Missing avatar URL reduces corroboration ability (low trust, not suspicious)
    if not avatar_url:
        risk += 0.05
        reasons.append({"code": "missing_avatar_url", "detail": "no avatar_url extracted"})

    return SingleIdentityRisk(authenticity_risk=_clamp01(risk), reasons=reasons)
