# # src/siva_guard/api/server.py
# from __future__ import annotations

# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import Any, Dict, List

# from siva_guard.core.schema import IdentityClaim, IdentityEvidence
# from siva_guard.pipeline.judge import judge_identity_set
# from siva_guard.connectors.social_url import SocialUrlConnector

# from siva_guard.pipeline.evidence_graph_v2 import build_evidence_graph_v2
# from siva_guard.pipeline.risk_v2 import compute_risk_v2
# from siva_guard.pipeline.agent_policy_v2 import decide_action_v2


# app = FastAPI(title="SIVA – Social Identity Verification Assistance")


# class CeremonyRequest(BaseModel):
#     identities: List[IdentityClaim]


# @app.get("/health")
# def health():
#     return {"ok": True}


# def _evidence_to_per_identity(evidences: List[IdentityEvidence]) -> Dict[str, Dict[str, Any]]:
#     out: Dict[str, Dict[str, Any]] = {}

#     for ev in evidences:
#         claim = getattr(ev, "claim", None)
#         claimed = getattr(claim, "claimed", None) or "unknown_claimed"

#         ui_obj = getattr(claim, "ui", None)
#         ui = ui_obj.model_dump() if hasattr(ui_obj, "model_dump") else (ui_obj if isinstance(ui_obj, dict) else None)

#         pub_obj = getattr(ev, "public", None)
#         public = pub_obj.model_dump() if hasattr(pub_obj, "model_dump") else (pub_obj if isinstance(pub_obj, dict) else None)

#         mode = getattr(ev, "mode", None)
#         errors = getattr(ev, "errors", None) or []

#         if hasattr(ev, "has_public"):
#             has_public = bool(getattr(ev, "has_public"))
#         else:
#             has_public = bool(public)

#         out[claimed] = {
#             "platform": getattr(claim, "platform", None),
#             "claimed": claimed,
#             "ui": ui,
#             "mode": mode,
#             "has_public": has_public,
#             "public": public,
#             "errors": errors,
#         }

#     return out


# @app.post("/verify")
# def verify(req: CeremonyRequest):
#     connectors = [SocialUrlConnector()]

#     evidences: List[IdentityEvidence] = []

#     for claim in req.identities:
#         collected = None
#         for c in connectors:
#             if c.supports(claim):
#                 collected = c.collect(claim)
#                 break
#         if collected is None:
#             collected = IdentityEvidence(claim=claim)  # in-app only
#         evidences.append(collected)

#     # Baseline output kept for debugging continuity
#     baseline_result = judge_identity_set(evidences)
#     out = baseline_result.model_dump()

#     per_identity = _evidence_to_per_identity(evidences)

#     g2 = build_evidence_graph_v2(per_identity)

#     risk2 = compute_risk_v2(g2.metrics, per_identity)

#     # Publish updated risk fields
#     out["substitution_risk"] = risk2.substitution_risk
#     out["authenticity_risk"] = risk2.authenticity_risk
#     out["overall_risk"] = risk2.overall_risk
#     out["confidence"] = risk2.confidence
#     out["reasons"] = risk2.reasons

#     # Agent now uses overall risk
#     out["agent"] = decide_action_v2(g2.metrics, risk2.overall_risk)

#     out["evidence_graph"] = {
#         "nodes": g2.nodes_out,
#         "edges": g2.edges_out,
#         "metrics": g2.metrics,
#     }

#     out["per_identity"] = per_identity

#     # Optional baseline debug block
#     out["baseline"] = baseline_result.model_dump()

#     return out


# src/siva_guard/api/server.py
# from __future__ import annotations

# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import List

# from siva_guard.core.schema import IdentityClaim
# from siva_guard.agent.runner import build_default_runner

# app = FastAPI(title="SIVA – Social Identity Verification Assistance")


# class CeremonyRequest(BaseModel):
#     identities: List[IdentityClaim]


# @app.get("/health")
# def health():
#     return {"ok": True}


# @app.post("/verify")
# def verify(req: CeremonyRequest):
#     runner = build_default_runner(max_steps=6, include_trace=True, include_baseline=True)
#     payload = {"identities": req.identities}   # pass objects
#     return runner.run(payload)
# # src/siva_guard/api/server.py

# from __future__ import annotations

# from fastapi import FastAPI
# from pydantic import BaseModel

# from siva_guard.agent.runner import build_default_runner
# from siva_guard.pipeline.judge_v1 import judge_from_siva_output


# app = FastAPI(title="SIVA Guard", version="0.2.0")


# class VerifyRequest(BaseModel):
#     identities: list[dict]


# class JudgeRequest(BaseModel):
#     # full /verify output JSON
#     siva_output: dict


# @app.get("/health")
# def health():
#     return {"ok": True}


# @app.post("/verify")
# def verify(req: VerifyRequest):
#     """
#     Runs deterministic SIVA pipeline (agent tools):
#       collect_evidence -> build_per_identity -> build_graph -> score_risk -> decide_action -> next_steps
#     Returns the full structured SIVA output.
#     """
#     runner = build_default_runner(
#         max_steps=6,
#         include_trace=True,
#         include_baseline=True,
#         enable_llm=False,
#     )
#     result = runner.run({"identities": req.identities})
#     return result


# @app.post("/judge")
# def judge(req: JudgeRequest):
#     """
#     Deterministic Judge layer on top of SIVA output.
#     Keeps SIVA output intact; returns verdict+certainty+standard+explanation.
#     """
#     return judge_from_siva_output(req.siva_output)


# # ---- helpers (kept for compatibility with older code paths) ----

# def _safe_dict(obj):
#     if obj is None:
#         return None
#     if isinstance(obj, dict):
#         return obj
#     if hasattr(obj, "model_dump"):
#         return obj.model_dump()
#     return None


# def _safe_public(pub_obj):
#     return pub_obj.model_dump() if hasattr(pub_obj, "model_dump") else (pub_obj if isinstance(pub_obj, dict) else None)

# siva_guard/api/server.py

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from siva_guard.agent.runner import build_default_runner
from siva_guard.core.schema import IdentityClaim
from siva_guard.pipeline.judge_v1 import judge_from_siva_output

app = FastAPI(title="SIVA Guard", version="0.2.0")


class VerifyRequest(BaseModel):
    # IMPORTANT: must be IdentityClaim objects, not dicts
    identities: list[IdentityClaim]


class JudgeRequest(BaseModel):
    # Full /verify output JSON
    siva_output: dict


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/verify")
def verify(req: VerifyRequest):
    """
    Runs deterministic SIVA pipeline (agent tools):
      collect_evidence -> build_per_identity -> build_graph -> score_risk -> decide_action -> next_steps
    Returns the full structured SIVA output.
    """
    runner = build_default_runner(
        max_steps=6,
        include_trace=True,
        include_baseline=True,
        enable_llm=False,
    )

    # req.identities is a list[IdentityClaim] (Pydantic objects)
    result = runner.run({"identities": req.identities})
    return result


@app.post("/judge")
def judge(req: JudgeRequest):
    """
    Deterministic Judge layer on top of SIVA output.
    Keeps SIVA output intact; returns verdict+certainty+standard+explanation.
    """
    return judge_from_siva_output(req.siva_output)
