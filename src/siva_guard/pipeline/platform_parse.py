# src/siva_guard/pipeline/platform_parse.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, parse_qs
import re


@dataclass(frozen=True)
class PlatformParsed:
    platform: Optional[str]
    claimed: str
    domain: Optional[str]
    handle: Optional[str]
    kind: str  # "url" | "email" | "handle" | "other"


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_HANDLE_RE = re.compile(r"^[a-zA-Z0-9._-]{2,64}$")


def _clean_handle(h: Optional[str]) -> Optional[str]:
    if not h:
        return None
    h = h.strip()
    if h.startswith("@"):
        h = h[1:]
    h = h.strip().strip("/")
    return h or None


def extract_handle(platform: Optional[str], claimed: str) -> PlatformParsed:
    """
    Best-effort deterministic extraction. No guessing beyond URL rules.
    """
    c = (claimed or "").strip()
    p = (platform or "").lower() if platform else None

    # Email
    if _EMAIL_RE.match(c):
        local = c.split("@", 1)[0].lower()
        return PlatformParsed(platform=p, claimed=c, domain=None, handle=local, kind="email")

    # URL
    if c.lower().startswith(("http://", "https://")):
        u = urlparse(c)
        domain = (u.netloc or "").lower()
        path = (u.path or "").strip("/")
        segs = [s for s in path.split("/") if s]
        qs = parse_qs(u.query or "")

        # Platform-specific rules
        if p in ("linkedin",):
            # common: /in/<handle>/, /company/<handle>/
            if len(segs) >= 2 and segs[0] in ("in", "company"):
                return PlatformParsed(p, c, domain, _clean_handle(segs[1]), "url")

        if p in ("github",):
            # /<user>/
            if len(segs) >= 1:
                return PlatformParsed(p, c, domain, _clean_handle(segs[0]), "url")

        if p in ("instagram",):
            # /<user>/
            if len(segs) >= 1:
                return PlatformParsed(p, c, domain, _clean_handle(segs[0]), "url")

        if p in ("x", "twitter"):
            # /<user>/ or /@user
            if len(segs) >= 1:
                return PlatformParsed(p, c, domain, _clean_handle(segs[0]), "url")

        if p in ("facebook",):
            # /<vanity> OR /profile.php?id=...
            if segs:
                if segs[0].lower() == "profile.php":
                    # use id if present
                    fb_id = qs.get("id", [None])[0]
                    return PlatformParsed(p, c, domain, _clean_handle(fb_id), "url")
                return PlatformParsed(p, c, domain, _clean_handle(segs[0]), "url")

        # Fallback: first segment if it looks like a handle
        if segs:
            return PlatformParsed(p, c, domain, _clean_handle(segs[0]), "url")

        return PlatformParsed(p, c, domain, None, "url")

    # Handle-ish
    h = _clean_handle(c)
    if h and _HANDLE_RE.match(h):
        return PlatformParsed(platform=p, claimed=c, domain=None, handle=h, kind="handle")

    return PlatformParsed(platform=p, claimed=c, domain=None, handle=None, kind="other")
