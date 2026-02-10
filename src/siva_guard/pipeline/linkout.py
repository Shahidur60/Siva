# src/siva_guard/pipeline/linkout.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set
import re
from urllib.parse import urlparse


_URL_RE = re.compile(r"(https?://[^\s)]+)", re.IGNORECASE)
_HANDLE_RE = re.compile(r"@([a-zA-Z0-9._-]{2,64})")


@dataclass
class LinkOuts:
    urls: List[str]
    domains: List[str]
    handles: List[str]


def extract_linkouts(text: Optional[str]) -> LinkOuts:
    """
    Deterministic extraction of URLs and @handles from a bio/description string.
    """
    t = text or ""
    urls = _URL_RE.findall(t)
    handles = _HANDLE_RE.findall(t)

    domains: List[str] = []
    seen: Set[str] = set()
    for u in urls:
        try:
            d = (urlparse(u).netloc or "").lower()
            if d and d not in seen:
                domains.append(d)
                seen.add(d)
        except Exception:
            continue

    # unique handles (preserve order)
    h_seen: Set[str] = set()
    h2: List[str] = []
    for h in handles:
        hl = h.lower()
        if hl not in h_seen:
            h2.append(hl)
            h_seen.add(hl)

    return LinkOuts(urls=urls, domains=domains, handles=h2)
