from __future__ import annotations

import requests_cache

# A small on-disk cache so repeated checks are fast and reduce block risk.
# Cache lives in project folder as siva_http_cache.sqlite
SESSION = requests_cache.CachedSession(
    cache_name="siva_http_cache",
    backend="sqlite",
    expire_after=3600,  # seconds (1 hour)
)

DEFAULT_HEADERS = {
    "User-Agent": "SIVA/0.2 (identity-verification; public-web)",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ✅ NEW: make headers apply globally to this session
SESSION.headers.update(DEFAULT_HEADERS)


def get_cached_session() -> requests_cache.CachedSession:
    """
    Phase 5+ uses this accessor so all modules share the same cached session + headers.
    """
    return SESSION
