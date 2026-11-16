"""
Unit and Integration Tests for LangGraph Multi-Agent Architecture.
Verifies StateGraph compilation, parallel node execution, and Socratic Inquisitor invariants.
"""

import pytest

from src.agents.graph import audit_workflow_app, build_crypto_audit_graph, run_crypto_audit
from src.engine.core_quant import CoreQuantEngine


def test_build_and_compile_crypto_audit_graph():
    """Verify that the StateGraph builds and compiles without error."""
    graph = build_crypto_audit_graph()
    app = graph.compile()
    assert app is not None
    assert audit_workflow_app is not None


@pytest.mark.asyncio
async def test_run_crypto_audit_dual_mode():
    """Verify end-to-end execution of DUAL_AUDIT through LangGraph."""
    engine = CoreQuantEngine()
    quant_audit = engine.run_full_quant_audit(symbol="BTCUSDT")

    state = await run_crypto_audit(
        symbol="BTCUSDT",
        execution_mode="DUAL_AUDIT",
        spot_valuation_data=quant_audit["spot"].model_dump(),
        futures_squeeze_data=quant_audit["futures"].model_dump(),
        whale_flow_data=quant_audit["whale"].model_dump(),
        etf_flow_data=quant_audit["etf"].model_dump(),
        token_vesting_data=quant_audit["vesting"].model_dump(),
        proposed_action="LONG_BTC_5X",
    )

    # Invariants verification
    assert state["symbol"] == "BTCUSDT"
    assert state["spot_dossier"] is not None
    assert state["futures_dossier"] is not None
    assert state["whale_etf_dossier"] is not None

    # Socratic Devil's Advocate Invariants
    assert len(state["fatal_socratic_questions"]) == 3
    assert 0.0 <= state["fomo_index"] <= 100.0
    assert state["anti_fomo_verdict"] in [
        "SCALE_IN_SPOT",
        "PROCEED_WITH_CAUTION",
        "REJECT_SETUP_TOO_RISKY",
    ]
    assert state["worst_case_invalidation_price"] > 0.0

    # Deliverables verification
    assert state["investment_memo"] is not None
    assert "Digital Asset Risk Disclaimer" in state["investment_memo"]["disclaimer"]
    assert state["telegram_alert_payload"] is not None


@pytest.mark.asyncio
async def test_run_crypto_audit_spot_mode():
    """Verify execution of MODE_SPOT."""
    engine = CoreQuantEngine()
    quant_audit = engine.run_full_quant_audit(symbol="ETHUSDT")

    state = await run_crypto_audit(
        symbol="ETHUSDT",
        execution_mode="MODE_SPOT",
        spot_valuation_data=quant_audit["spot"].model_dump(),
        proposed_action="DCA_BUY_SPOT",
    )

    assert state["symbol"] == "ETHUSDT"
    assert state["spot_dossier"] is not None
    assert len(state["fatal_socratic_questions"]) == 3
    assert state["anti_fomo_verdict"] in [
        "SCALE_IN_SPOT",
        "PROCEED_WITH_CAUTION",
        "REJECT_SETUP_TOO_RISKY",
    ]


@pytest.mark.asyncio
async def test_run_crypto_audit_futures_mode():
    """Verify execution of MODE_FUTURES."""
    engine = CoreQuantEngine()
    quant_audit = engine.run_full_quant_audit(symbol="SOLUSDT")

    state = await run_crypto_audit(
        symbol="SOLUSDT",
        execution_mode="MODE_FUTURES",
        futures_squeeze_data=quant_audit["futures"].model_dump(),
        proposed_action="SCALP_SHORT",
    )

    assert state["symbol"] == "SOLUSDT"
    assert state["futures_dossier"] is not None
    assert len(state["fatal_socratic_questions"]) == 3
    assert state["fomo_index"] >= 0.0
