# src/siva_guard/connectors/social_url.py
from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from siva_guard.core.schema import (
    IdentityClaim, IdentityEvidence, PublicEvidence,
    CollectionMode, Platform
)
from siva_guard.connectors.base import Connector
from siva_guard.connectors.resolver import resolve_to_url
from siva_guard.connectors.http_client import get_cached_session


SUPPORTED = {
    Platform.FACEBOOK,
    Platform.INSTAGRAM,
    Platform.X,
    Platform.LINKEDIN,
    Platform.GITHUB,
    Platform.TIKTOK,
    Platform.YOUTUBE,
    Platform.WEBSITE,
    Platform.OTHER,
}


def _extract_external_links(html: str, *, base_url: str, cap: int = 50) -> list[str]:
    """
    Phase 7.2: bounded extraction of external outbound links from <a href="...">.
    Deterministic:
      - first-seen order
      - http/https only
      - excludes same-host links, fragments, mailto/javascript/tel
      - strips URL fragments
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    base_host = (urlparse(base_url).netloc or "").lower()

    out: list[str] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        if len(out) >= cap:
            break

        href = (a.get("href") or "").strip()
        if not href:
            continue

        low = href.lower()
        if href.startswith("#") or low.startswith("javascript:") or low.startswith("mailto:") or low.startswith("tel:"):
            continue

        abs_url = urljoin(base_url, href)
        p = urlparse(abs_url)
        if p.scheme not in ("http", "https"):
            continue

        host = (p.netloc or "").lower()
        if not host or host == base_host:
            continue

        norm = p._replace(fragment="").geturl()
        if norm not in seen:
            seen.add(norm)
            out.append(norm)

    return out


class SocialUrlConnector(Connector):
    """
    Universal public-web connector:
    - resolves handle -> URL when possible
    - fetches page
    - extracts OpenGraph metadata (og:title, og:description, og:image)

    Phase 6.3 additions:
    - Records cache metadata (r.from_cache) into PublicEvidence.fetch_cached
      (and also keeps a numeric signal in field_confidence for backward compatibility).

    Phase 7.2 additions:
    - Populates PublicEvidence.external_links using bounded <a href> parsing.
    """

    def supports(self, claim: IdentityClaim) -> bool:
        return claim.platform in SUPPORTED and bool((claim.claimed or "").strip())

    def collect(self, claim: IdentityClaim) -> IdentityEvidence:
        ev = IdentityEvidence(claim=claim, mode=CollectionMode.PUBLIC_WEB)

        url = resolve_to_url(claim.platform, claim.claimed) or claim.claimed.strip()

        try:
            sess = get_cached_session()
            r = sess.get(url, timeout=12, allow_redirects=True)

            fetch_cached = getattr(r, "from_cache", None)

            html = r.text or ""
            soup = BeautifulSoup(html, "lxml")

            public = PublicEvidence(
                canonical_url=str(r.url),
                raw_excerpt=(html[:2000] if html else None),
                field_confidence={"canonical_url": 0.9, "raw_excerpt": 0.3},
            )

            def meta(prop: str):
                tag = soup.find("meta", attrs={"property": prop})
                return tag.get("content").strip() if tag and tag.get("content") else None

            og_title = meta("og:title")
            og_desc = meta("og:description")
            og_img = meta("og:image")

            if og_title:
                public.display_name = og_title
                public.field_confidence["display_name"] = 0.55

            if og_desc:
                public.bio = og_desc
                public.field_confidence["bio"] = 0.55

            if og_img:
                public.avatar_url = og_img
                public.field_confidence["avatar_url"] = 0.45

            # Fallback: <title>
            if not getattr(public, "display_name", None) and soup.title and soup.title.string:
                public.display_name = soup.title.string.strip()
                public.field_confidence["display_name"] = 0.35

            # Phase 7.2: external_links (best-effort)
            try:
                public.external_links = _extract_external_links(html, base_url=str(r.url), cap=50)  # type: ignore[attr-defined]
                public.field_confidence["external_links"] = 0.35 if public.external_links else 0.0
            except Exception:
                public.field_confidence["external_links"] = 0.0

            # Phase 6.3: expose caching
            public.field_confidence["fetch_cached"] = 1.0 if fetch_cached else 0.0
            try:
                public.fetch_cached = fetch_cached  # type: ignore[attr-defined]
            except Exception:
                pass

            ev.public = public

        except Exception as e:
            ev.errors.append(f"public_fetch_failed: {type(e).__name__}: {e}")
            ev.mode = CollectionMode.IN_APP_ONLY

        return ev


__all__ = ["SocialUrlConnector"]
