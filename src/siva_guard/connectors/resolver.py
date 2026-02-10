from __future__ import annotations

from siva_guard.core.schema import Platform

def resolve_to_url(platform: Platform, claimed: str) -> str | None:
    c = (claimed or "").strip()

    # Already a URL
    if c.startswith("http://") or c.startswith("https://"):
        return c

    # Normalize @handle
    if c.startswith("@"):
        c = c[1:]

    if not c:
        return None

    # Platform-specific URL patterns (public profile URLs)
    if platform == Platform.X:
        return f"https://x.com/{c}"
    if platform == Platform.INSTAGRAM:
        return f"https://www.instagram.com/{c}/"
    if platform == Platform.GITHUB:
        return f"https://github.com/{c}"
    if platform == Platform.TIKTOK:
        # TikTok commonly uses @handle in URL
        return f"https://www.tiktok.com/@{c}"
    if platform == Platform.YOUTUBE:
        # many forms exist; this is best-effort
        return f"https://www.youtube.com/@{c}"
    if platform == Platform.LINKEDIN:
        # LinkedIn profiles are often /in/<handle>
        return f"https://www.linkedin.com/in/{c}/"
    if platform == Platform.FACEBOOK:
        return f"https://www.facebook.com/{c}"

    # For website/other/email we won't guess here
    return None
