from __future__ import annotations

from typing import Any, Dict, List

from siva_guard.core.schema import IdentityEvidence
from siva_guard.connectors.social_url import SocialUrlConnector
from siva_guard.pipeline.judge import judge_identity_set

from ..trace import AgentTraceEvent
from ..state import CeremonyState
from ..config import AgentConfig
from .base import Tool


class CollectEvidenceTool(Tool):
    name = "collect_evidence"

    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        connectors = [SocialUrlConnector()]
        evidences: List[IdentityEvidence] = []

        for claim in st.claims:
            collected = None
            for c in connectors:
                if c.supports(claim):
                    collected = c.collect(claim)
                    break
            if collected is None:
                collected = IdentityEvidence(claim=claim)  # in-app only
            evidences.append(collected)

        st.evidences = evidences

        # Keep baseline continuity (your current server returns this)
        if cfg.include_baseline:
            baseline_result = judge_identity_set(evidences)
            st.baseline = baseline_result.model_dump()

        st.trace.add(
            AgentTraceEvent(
                step=st.steps_run,
                tool=self.name,
                decision="collected",
                inputs={"num_identities": len(st.claims)},
                outputs={"num_evidences": len(st.evidences), "baseline_included": bool(st.baseline)},
            )
        )
        return {"num_evidences": len(st.evidences)}
