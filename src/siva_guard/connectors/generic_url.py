from __future__ import annotations

import re
import requests
from bs4 import BeautifulSoup

from siva_guard.core.schema import (
    IdentityClaim, IdentityEvidence, PublicEvidence,
    CollectionMode, Platform
)
from siva_guard.connectors.base import Connector


_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


class GenericUrlConnector(Connector):
    """
    Best-effort public URL evidence collector.
    Works for any platform when the claim is a URL (website / profile link).
    """

    def supports(self, claim: IdentityClaim) -> bool:
        c = (claim.claimed or "").strip()
        return bool(_URL_RE.match(c)) and claim.platform in {Platform.WEBSITE, Platform.OTHER, Platform.FACEBOOK,
                                                            Platform.INSTAGRAM, Platform.X, Platform.LINKEDIN,
                                                            Platform.GITHUB, Platform.TIKTOK, Platform.YOUTUBE}

    def collect(self, claim: IdentityClaim) -> IdentityEvidence:
        ev = IdentityEvidence(claim=claim, mode=CollectionMode.PUBLIC_WEB)

        url = (claim.claimed or "").strip()
        try:
            headers = {
                "User-Agent": "SIVA/0.1 (public-evidence-collector)"
            }
            r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            ev_public = PublicEvidence(
                canonical_url=str(r.url),
                raw_excerpt=(r.text[:2000] if r.text else None),
                field_confidence={"canonical_url": 0.9, "raw_excerpt": 0.3},
            )

            # Parse basic metadata
            soup = BeautifulSoup(r.text or "", "lxml")

            title = soup.title.string.strip() if soup.title and soup.title.string else None
            if title:
                ev_public.display_name = title
                ev_public.field_confidence["display_name"] = 0.4

            # meta description
            desc_tag = soup.find("meta", attrs={"name": "description"})
            if desc_tag and desc_tag.get("content"):
                ev_public.bio = desc_tag.get("content").strip()
                ev_public.field_confidence["bio"] = 0.4

            # og:image (often profile image / page image)
            og_img = soup.find("meta", attrs={"property": "og:image"})
            if og_img and og_img.get("content"):
                ev_public.avatar_url = og_img.get("content").strip()
                ev_public.field_confidence["avatar_url"] = 0.3

            # og:title may be better than <title>
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title and og_title.get("content"):
                ev_public.display_name = og_title.get("content").strip()
                ev_public.field_confidence["display_name"] = 0.5

            # og:description may be better
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc and og_desc.get("content"):
                ev_public.bio = og_desc.get("content").strip()
                ev_public.field_confidence["bio"] = 0.5

            ev.public = ev_public

        except Exception as e:
            ev.errors.append(f"url_fetch_failed: {type(e).__name__}: {e}")
            # Degrade gracefully: keep mode as IN_APP_ONLY if fetch failed
            ev.mode = CollectionMode.IN_APP_ONLY

        return ev
