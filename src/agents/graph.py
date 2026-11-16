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
) -> CryptoIntelState:
    """Execute end-to-end multi-agent audit through the compiled LangGraph pipeline."""
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

    final_state: CryptoIntelState = cast(CryptoIntelState, await audit_workflow_app.ainvoke(initial_state))
    return final_state
