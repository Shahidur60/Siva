from __future__ import annotations

from typing import Any, Dict, List

from siva_guard.core.schema import IdentityEvidence

from ..trace import AgentTraceEvent
from ..state import CeremonyState
from ..config import AgentConfig
from .base import Tool


def _evidence_to_per_identity(evidences: List[IdentityEvidence]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}

    for ev in evidences:
        claim = getattr(ev, "claim", None)
        claimed = getattr(claim, "claimed", None) or "unknown_claimed"

        ui_obj = getattr(claim, "ui", None)
        ui = ui_obj.model_dump() if hasattr(ui_obj, "model_dump") else (ui_obj if isinstance(ui_obj, dict) else None)

        pub_obj = getattr(ev, "public", None)
        public = pub_obj.model_dump() if hasattr(pub_obj, "model_dump") else (pub_obj if isinstance(pub_obj, dict) else None)

        mode = getattr(ev, "mode", None)
        errors = getattr(ev, "errors", None) or []

        if hasattr(ev, "has_public"):
            has_public = bool(getattr(ev, "has_public"))
        else:
            has_public = bool(public)

        platform_obj = getattr(claim, "platform", None)
        # Make platform JSON-serializable and stable (Enum -> string).
        platform = str(platform_obj) if platform_obj is not None else None

        out[claimed] = {
            "platform": platform,
            "claimed": claimed,
            "ui": ui,
            "mode": mode,
            "has_public": has_public,
            "public": public,
            "errors": errors,
        }

    return out


class BuildPerIdentityTool(Tool):
    name = "build_per_identity"

    def run(self, st: CeremonyState, cfg: AgentConfig) -> Dict[str, Any]:
        st.per_identity = _evidence_to_per_identity(st.evidences)

        st.trace.add(
            AgentTraceEvent(
                step=st.steps_run,
                tool=self.name,
                decision="built",
                inputs={"num_evidences": len(st.evidences)},
                outputs={"num_per_identity": len(st.per_identity)},
            )
        )
        return {"num_per_identity": len(st.per_identity)}
