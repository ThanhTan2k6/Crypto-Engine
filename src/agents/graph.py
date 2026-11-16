"""
LangGraph Multi-Agent StateGraph Workflow for CryptoIntel-Engine.
Orchestrates parallel specialist analysis, fan-in barrier, Socratic cross-examination, and synthesis.
"""

from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from src.agents.nodes import (
    futures_node,
    socratic_node,
    spot_node,
    supervisor_node,
    synthesis_node,
    whale_node,
)
from src.agents.state import CryptoIntelState, create_initial_state
from src.llmops.cache import audit_cache
from src.llmops.langfuse_tracer import llmops_tracer


def build_crypto_audit_graph() -> Any:
    """Build and wire the multi-agent StateGraph workflow."""
    workflow = StateGraph(CryptoIntelState)

    # Register nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("spot_specialist", spot_node)
    workflow.add_node("futures_specialist", futures_node)
    workflow.add_node("whale_specialist", whale_node)
    workflow.add_node("socratic_devil", socratic_node)
    workflow.add_node("synthesis", synthesis_node)

    # Pipeline flow: Supervisor -> Specialists -> Socratic Inquisitor -> Synthesis
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "spot_specialist")
    workflow.add_edge("spot_specialist", "futures_specialist")
    workflow.add_edge("futures_specialist", "whale_specialist")
    workflow.add_edge("whale_specialist", "socratic_devil")
    workflow.add_edge("socratic_devil", "synthesis")
    workflow.add_edge("synthesis", END)

    return workflow


# Compile the singleton app workflow
audit_workflow_app = build_crypto_audit_graph().compile()


def strip_transient_fields(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Recursively strip non-deterministic timestamp and latency fields for cache hashing."""
    if not isinstance(payload, dict):
        return payload
    return {
        k: strip_transient_fields(v) if isinstance(v, dict) else v
        for k, v in payload.items()
        if k not in ["timestamp", "generated_at", "execution_latency_ms"]
    }


async def run_crypto_audit(
    symbol: str,
    execution_mode: str = "DUAL_AUDIT",
    spot_valuation_data: dict[str, Any] | None = None,
    futures_squeeze_data: dict[str, Any] | None = None,
    etf_flow_data: dict[str, Any] | None = None,
    whale_flow_data: dict[str, Any] | None = None,
    token_vesting_data: dict[str, Any] | None = None,
    proposed_action: str | None = None,
    proposed_entry: float | None = None,
    time_horizon_days: int = 30,
    hard_red_flags: list[str] | None = None,
    use_cache: bool = True,
) -> CryptoIntelState:
    """Execute end-to-end multi-agent audit through the compiled LangGraph pipeline."""
    payload_hash = audit_cache.compute_payload_hash({
        "spot": strip_transient_fields(spot_valuation_data),
        "futures": strip_transient_fields(futures_squeeze_data),
        "whale": strip_transient_fields(whale_flow_data),
        "etf": strip_transient_fields(etf_flow_data),
        "vesting": strip_transient_fields(token_vesting_data),
        "action": proposed_action,
        "entry": proposed_entry,
        "horizon": time_horizon_days,
        "flags": hard_red_flags,
    })

    if use_cache:
        cached_audit = await audit_cache.get("audit", f"{symbol.upper()}:{execution_mode}", payload_hash)
        if cached_audit is not None:
            return cast(CryptoIntelState, cached_audit)

    initial_state = create_initial_state(
        symbol=symbol,
        execution_mode=execution_mode,
        spot_valuation_data=spot_valuation_data,
        futures_squeeze_data=futures_squeeze_data,
        etf_flow_data=etf_flow_data,
        whale_flow_data=whale_flow_data,
        token_vesting_data=token_vesting_data,
        proposed_action=proposed_action,
        proposed_entry=proposed_entry,
        time_horizon_days=time_horizon_days,
        hard_red_flags=hard_red_flags,
    )

    trace_id = initial_state["trace_id"]
    llmops_tracer.trace_audit_start(
        trace_id=trace_id,
        symbol=symbol,
        execution_mode=execution_mode,
        proposed_action=proposed_action,
    )

    try:
        final_state: CryptoIntelState = cast(CryptoIntelState, await audit_workflow_app.ainvoke(initial_state))
        llmops_tracer.trace_audit_end(
            trace_id=trace_id,
            anti_fomo_verdict=final_state.get("anti_fomo_verdict", "UNKNOWN"),
            fomo_index=final_state.get("fomo_index", 0.0),
            fatal_questions=final_state.get("fatal_socratic_questions", []),
            errors=final_state.get("errors"),
        )
    except Exception as e:
        llmops_tracer.trace_audit_end(
            trace_id=trace_id,
            anti_fomo_verdict="REJECT_SETUP_TOO_RISKY",
            fomo_index=100.0,
            fatal_questions=[],
            errors=[str(e)],
        )
        raise

    if use_cache and not final_state.get("errors"):
        await audit_cache.set(
            "audit",
            f"{symbol.upper()}:{execution_mode}",
            dict(final_state),
            ttl_seconds=300,
            payload_hash=payload_hash,
        )

    return final_state
