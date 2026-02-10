from __future__ import annotations

from html.parser import HTMLParser
from typing import List, Optional
from urllib.parse import urljoin, urlparse


class _AnchorParser(HTMLParser):
    def __init__(self, base_url: str, limit: int):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.limit = limit
        self.links: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a" or len(self.links) >= self.limit:
            return
        href: Optional[str] = None
        for k, v in attrs:
            if k.lower() == "href":
                href = v
                break
        if not href:
            return
        href = href.strip()
        if href.startswith("#") or href.lower().startswith("javascript:") or href.lower().startswith("mailto:"):
            return

        abs_url = urljoin(self.base_url, href)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            return
        # Normalize: drop fragments
        norm = parsed._replace(fragment="").geturl()
        self.links.append(norm)


def extract_external_links(html: str, *, base_url: str, limit: int = 80) -> List[str]:
    """
    Returns bounded list of absolute http(s) links.
    Dedup preserves first-seen order deterministically.
    """
    parser = _AnchorParser(base_url=base_url, limit=limit)
    parser.feed(html or "")

    seen = set()
    out: List[str] = []
    for u in parser.links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def filter_external_to_host(links: List[str], *, base_url: str) -> List[str]:
    """
    Keep only links whose host != base_url host (best-effort).
    """
    base_host = urlparse(base_url).netloc.lower()
    out: List[str] = []
    for u in links:
        host = urlparse(u).netloc.lower()
        if host and host != base_host:
            out.append(u)
    return out
