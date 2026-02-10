# src/siva_guard/pipeline/avatar_hash.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import hashlib

from siva_guard.connectors.http_client import get_cached_session


@dataclass
class AvatarHashResult:
    avatar_url: Optional[str]
    sha256: Optional[str]
    error: Optional[str]


def hash_avatar_url(avatar_url: Optional[str], timeout_s: float = 8.0) -> AvatarHashResult:
    """
    Deterministic: if avatar_url missing or fetch fails, return error; no guessing.
    Uses cached HTTP session (requests-cache) to reduce repeat fetches.
    """
    if not avatar_url:
        return AvatarHashResult(avatar_url=None, sha256=None, error="avatar_url_missing")

    try:
        sess = get_cached_session()
        r = sess.get(avatar_url, timeout=timeout_s)
        if r.status_code != 200 or not r.content:
            return AvatarHashResult(
                avatar_url=avatar_url,
                sha256=None,
                error=f"avatar_fetch_failed:http_{r.status_code}",
            )
        h = hashlib.sha256(r.content).hexdigest()
        return AvatarHashResult(avatar_url=avatar_url, sha256=h, error=None)
    except Exception as e:
        return AvatarHashResult(avatar_url=avatar_url, sha256=None, error=f"avatar_fetch_failed:{type(e).__name__}")
