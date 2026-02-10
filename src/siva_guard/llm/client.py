from __future__ import annotations

import os
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


class LLMClient:
    """
    Minimal wrapper around OpenAI Responses API.
    Uses OPENAI_API_KEY from env.

    This is intentionally tiny and side-effect free.
    """

    def __init__(self, model: str = "gpt-4.1-mini"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.enabled = bool(self.api_key) and OpenAI is not None
        self._client = OpenAI(api_key=self.api_key) if self.enabled else None  # type: ignore

    def text(self, *, instructions: str, user_input: str, max_output_tokens: int = 350) -> Optional[str]:
        """
        Returns output_text or None if disabled / failed.
        """
        if not self.enabled or self._client is None:
            return None

        try:
            resp = self._client.responses.create(
                model=self.model,
                instructions=instructions,
                input=user_input,
                max_output_tokens=max_output_tokens,
            )
            # Official SDK provides output_text convenience. :contentReference[oaicite:1]{index=1}
            out = getattr(resp, "output_text", None)
            if out is None:
                return None
            return str(out).strip()
        except Exception:
            return None
