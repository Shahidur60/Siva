# src/siva_guard/pipeline/identifiers.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import re

from siva_guard.pipeline.platform_parse import extract_handle


@dataclass(frozen=True)
class ParsedIdentifier:
    raw_claimed: str
    kind: str  # "url" | "email" | "handle" | "other"
    domain: Optional[str]
    handle: Optional[str]  # best-effort username/slug
    normalized: str        # normalization target for comparisons


def _normalize_basic(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "", s)

    # If it's purely numeric (e.g., Facebook id=...), keep as-is
    if s.isdigit():
        return s

    s = s.replace("0", "o").replace("1", "l")
    return s

def parse_claimed(claimed: str, platform: Optional[str] = None) -> ParsedIdentifier:
    """
    Phase 6: platform-aware deterministic parsing.

    - If platform is provided, use platform-specific URL rules via extract_handle().
    - If platform is None, still parses deterministically using generic rules inside extract_handle().
    - Never guesses beyond these deterministic rules.
    """
    raw = claimed or ""
    pp = extract_handle(platform, raw)

    handle_norm = _normalize_basic(pp.handle) if pp.handle else ""
    norm = handle_norm if handle_norm else _normalize_basic(pp.claimed)

    return ParsedIdentifier(
        raw_claimed=raw,
        kind=pp.kind,
        domain=pp.domain,
        handle=pp.handle,
        normalized=norm,
    )


def best_compare_key(claimed: str, platform: Optional[str] = None) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Convenience: returns (normalized, domain, handle) for comparisons.

    Pass platform when known for best handle extraction.
    """
    p = parse_claimed(claimed, platform=platform)
    return p.normalized, p.domain, p.handle
