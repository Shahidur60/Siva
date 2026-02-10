from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..state import CeremonyState
from ..config import AgentConfig


class Tool(ABC):
    name: str = "tool"

    @abstractmethod
    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        ...
