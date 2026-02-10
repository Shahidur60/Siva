from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentConfig:
    # Runner controls
    max_steps: int = 6
    include_trace: bool = True
    include_baseline: bool = True

    # --- LLM augmentation (optional) ---
    enable_llm: bool = False
    llm_model: str = "gpt-4.1-mini"
    llm_max_planner_steps: int = 3
