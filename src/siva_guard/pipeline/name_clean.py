from __future__ import annotations

import re
from typing import Optional

_PLATFORM_TOKENS = {
    "facebook": ["facebook"],
    "instagram": ["instagram"],
    "twitter": ["twitter", "x"],
    "github": ["github"],
    "linkedin": ["linkedin"],
}

_SPLIT_MARKERS = ["|", "•", "-", "—", "–", "·", ":", "(", "["]


def clean_display_name(raw: Optional[str], *, platform: str) -> str:
    """
    Best-effort deterministic cleaning for platform-templated OG titles.
    Goal: remove common suffixes and platform labels, reduce mismatch noise.

    Returns empty string if input is missing.
    """
    if not raw or not isinstance(raw, str):
        return ""

    s = raw.strip()
    s = re.sub(r"\s+", " ", s)

    # Split on common template markers; keep the first chunk (deterministic)
    for m in _SPLIT_MARKERS:
        if m in s:
            s = s.split(m, 1)[0].strip()

    # Remove trailing platform token if present
    tokens = _PLATFORM_TOKENS.get((platform or "").lower(), [])
    lower = s.lower().strip()
    for t in tokens:
        if lower.endswith(" " + t):
            s = s[: -(len(t) + 1)].strip()
            break

    # Final normalize spacing
    s = re.sub(r"\s+", " ", s).strip()
    return s
