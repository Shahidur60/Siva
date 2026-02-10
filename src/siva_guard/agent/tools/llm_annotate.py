from __future__ import annotations

from typing import Any, Dict

from ..config import AgentConfig
from ..state import CeremonyState
from ..trace import AgentTraceEvent
from .base import Tool

from siva_guard.llm.client import LLMClient
from siva_guard.llm.annotator import annotate


class LLMAnnotateTool(Tool):
    name = "llm_annotate"

    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        if not cfg.enable_llm:
            return {"skipped": True}

        llm = LLMClient(model=cfg.llm_model)
        ann = annotate(llm, per_identity=st.per_identity, reasons=st.reasons)

        st.llm_annotations = ann
        st.result["llm_annotations"] = ann

        st.trace.add(
            AgentTraceEvent(
                step=st.steps_run,
                tool=self.name,
                decision="annotated",
                inputs={"llm_enabled": llm.enabled},
                outputs={"has_annotations": bool(ann)},
            )
        )
        return {"has_annotations": bool(ann), "llm_enabled": llm.enabled}
