# src/siva_guard/pipeline/reverse_links.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from siva_guard.connectors.http_client import get_cached_session


_URL_RE = re.compile(r"(https?://[^\s\"'<>]+)", re.IGNORECASE)


@dataclass
class ReverseLinkResult:
    url: str
    outbound_urls: List[str]
    outbound_domains: List[str]
    error: Optional[str]
    fetch_cached: Optional[bool]


def fetch_outbound_links(url: str, timeout_s: float = 8.0, max_links: int = 80) -> ReverseLinkResult:
    """
    Fetch a webpage and extract outbound links. Deterministic, best-effort.
    """
    try:
        sess = get_cached_session()
        r = sess.get(url, timeout=timeout_s, allow_redirects=True)

        fetch_cached = getattr(r, "from_cache", None)
        if r.status_code != 200 or not r.text:
            return ReverseLinkResult(url, [], [], f"http_{r.status_code}", fetch_cached)

        soup = BeautifulSoup(r.text, "lxml")
        hrefs: List[str] = []

        for a in soup.find_all("a", href=True):
            href = a.get("href") or ""
            href = href.strip()
            if href.startswith("http://") or href.startswith("https://"):
                hrefs.append(href)
            if len(hrefs) >= max_links:
                break

        # also include raw URLs in text (some sites)
        for m in _URL_RE.findall(r.text):
            hrefs.append(m)
            if len(hrefs) >= max_links:
                break

        # uniq preserve order
        seen: Set[str] = set()
        out_urls: List[str] = []
        for h in hrefs:
            if h not in seen:
                out_urls.append(h)
                seen.add(h)

        domains_seen: Set[str] = set()
        out_domains: List[str] = []
        for h in out_urls:
            try:
                d = (urlparse(h).netloc or "").lower()
                if d and d not in domains_seen:
                    out_domains.append(d)
                    domains_seen.add(d)
            except Exception:
                continue

        return ReverseLinkResult(url, out_urls, out_domains, None, fetch_cached)

    except Exception as e:
        return ReverseLinkResult(url, [], [], f"fetch_failed:{type(e).__name__}", None)
