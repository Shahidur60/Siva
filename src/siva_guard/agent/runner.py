# src/siva_guard/agent/runner.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from siva_guard.agent.config import AgentConfig
from siva_guard.agent.state import CeremonyState


def _trace_event(tool_name: str, status: str = "ok", detail: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ev: Dict[str, Any] = {"tool": tool_name, "status": status}
    if isinstance(detail, dict) and detail:
        safe_detail: Dict[str, Any] = {}
        for k, v in detail.items():
            ks = str(k)
            if len(ks) <= 64:
                safe_detail[ks] = v
        ev["detail"] = safe_detail
    return ev


class SivaAgentRunner:
    def __init__(self, tools: List[Any], cfg: Optional[AgentConfig] = None):
        self.tools = tools
        self.cfg = cfg or AgentConfig(max_steps=6, include_trace=True, include_baseline=True)

    def run(self, request_payload: Union[Dict[str, Any], List[Any]]) -> Dict[str, Any]:
        if isinstance(request_payload, list):
            request_payload = {"identities": request_payload}

        state = CeremonyState(request=request_payload)

        # Backward-compatible: tools expect state.claims
        claims = request_payload.get("identities") or request_payload.get("claims") or []
        state.claims = claims
        state.identities = claims

        if not getattr(self.cfg, "include_baseline", True):
            state.baseline = {}

        agent_trace: List[Dict[str, Any]] = []
        steps_run = 0
        max_steps = getattr(self.cfg, "max_steps", 6)
        include_trace = getattr(self.cfg, "include_trace", True)

        # expose counters to tools
        state.max_steps = max_steps
        state.steps_run = steps_run

        for tool in self.tools:
            if steps_run >= max_steps:
                break

            tool_name = getattr(tool, "name", tool.__class__.__name__)

            try:
                # cache per request so tools don't refetch
                if tool_name in state.tool_cache:
                    summary = state.tool_cache[tool_name]
                else:
                    try:
                        summary = tool.run(state, self.cfg)
                    except TypeError:
                        summary = tool.run(state)
                    state.tool_cache[tool_name] = summary

                steps_run += 1
                state.steps_run = steps_run

                if include_trace:
                    agent_trace.append(_trace_event(tool_name, "ok", summary if isinstance(summary, dict) else None))

            except Exception as e:
                steps_run += 1
                state.steps_run = steps_run

                if include_trace:
                    agent_trace.append(_trace_event(tool_name, "error", {"error": f"{type(e).__name__}: {e}"}))

                state.result = state.result or {}
                state.result.setdefault("errors", [])
                state.result["errors"].append(f"agent_tool_failed:{tool_name}:{type(e).__name__}:{e}")
                break

        # runner footer
        state.result = state.result or {}
        state.result["agentic"] = {"steps_run": steps_run, "max_steps": max_steps}
        if include_trace:
            state.result["agent_trace"] = agent_trace

        # include tool-side trace if populated
        if state.trace:
            state.result["trace"] = list(state.trace)

        # baseline debug (only if enabled and non-empty)
        if getattr(self.cfg, "include_baseline", True) and state.baseline:
            state.result["baseline"] = state.baseline

        return state.result


def build_default_runner(
    *,
    max_steps: int = 6,
    include_trace: bool = True,
    include_baseline: bool = True,
    enable_llm: bool = False,
    llm_model: str = "gpt-4.1-mini",
    llm_max_planner_steps: int = 3,
) -> SivaAgentRunner:
    from siva_guard.agent.tools.collect_evidence import CollectEvidenceTool
    from siva_guard.agent.tools.build_per_identity import BuildPerIdentityTool
    from siva_guard.agent.tools.build_graph import BuildGraphTool
    from siva_guard.agent.tools.score_risk import ScoreRiskTool
    from siva_guard.agent.tools.decide_action import DecideActionTool

    tools: List[Any] = [
        CollectEvidenceTool(),
        BuildPerIdentityTool(),
        BuildGraphTool(),
    ]

    # optional LLM planning trace
    if enable_llm:
        try:
            from siva_guard.agent.tools.llm_plan import LLMPlanTool
            tools.append(LLMPlanTool())
        except Exception:
            pass

    tools.append(ScoreRiskTool())

    # optional LLM annotations
    if enable_llm:
        try:
            from siva_guard.agent.tools.llm_annotate import LLMAnnotateTool
            tools.append(LLMAnnotateTool())
        except Exception:
            pass

    tools.append(DecideActionTool())

    # optional LLM explanation
    if enable_llm:
        try:
            from siva_guard.agent.tools.llm_explain import LLMExplainTool
            tools.append(LLMExplainTool())
        except Exception:
            pass

    # existing optional next_steps
    try:
        from siva_guard.agent.tools.next_steps import NextStepsTool
        tools.append(NextStepsTool())
    except Exception:
        pass

    cfg = AgentConfig(
        max_steps=max_steps,
        include_trace=include_trace,
        include_baseline=include_baseline,
        enable_llm=enable_llm,
        llm_model=llm_model,
        llm_max_planner_steps=llm_max_planner_steps,
    )

    return SivaAgentRunner(tools=tools, cfg=cfg)
