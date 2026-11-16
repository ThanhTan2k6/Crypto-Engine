"""
Golden Historical Stress-Test Evaluation Harness.
Evaluates Socratic Devil's Advocate Agent performance across all 10 Golden Cases.
Verifies Anti-FOMO Verdict calibration, FOMO Index bounds, and 3 Fatal Socratic Questions.
"""

import json
from pathlib import Path

import pytest

from src.agents.graph import run_crypto_audit

GOLDEN_EVAL_DIR = Path("data/golden_eval")


@pytest.mark.asyncio
async def test_all_10_golden_cases_socratic_evaluation():
    """Run full evaluation suite over all 10 Golden Cases."""
    golden_files = sorted(GOLDEN_EVAL_DIR.glob("gc*.json"))
    assert len(golden_files) == 10, f"Expected 10 golden cases, found {len(golden_files)}"

    evaluated_count = 0

    for file_path in golden_files:
        case_data = json.loads(file_path.read_text(encoding="utf-8"))

        case_id = case_data["case_id"]
        symbol = case_data.get("symbol", "BTCUSDT")
        quant_payload = case_data["quant_payload"]
        expected = case_data["expected_evaluation"]
        expected_verdict = expected["verdict"]
        fomo_min = expected.get("fomo_index_min", 0.0)

        # Build mock component data from golden case payload
        spot_data = {
            "symbol": symbol,
            "current_price": quant_payload.get("current_price", 50000.0),
            "mvrv_zscore": quant_payload.get("mvrv_zscore", 1.5),
            "cycle_regime": (
                "CYCLE_TOP_EUPHORIA"
                if quant_payload.get("mvrv_zscore", 1.5) >= 4.5
                else "MID_BULL_EXPANSION"
            ),
            "dca_zone_conservative": quant_payload.get("current_price", 50000.0) * 0.92,
            "dca_zone_moderate": quant_payload.get("current_price", 50000.0) * 0.85,
            "dca_zone_aggressive": quant_payload.get("current_price", 50000.0) * 0.70,
            "take_profit_target_1": quant_payload.get("current_price", 50000.0) * 1.35,
            "take_profit_target_2": quant_payload.get("current_price", 50000.0) * 1.75,
            "take_profit_target_3": quant_payload.get("current_price", 50000.0) * 2.50,
        }

        futures_data = {
            "symbol": symbol,
            "current_price": quant_payload.get("current_price", 50000.0),
            "annualized_funding_rate": quant_payload.get("annualized_funding_rate", 10.0),
            "frsi_score": quant_payload.get("frsi_score", 50.0),
            "oi_change_24h_pct": quant_payload.get("oi_change_24h_pct", 5.0),
            "orderbook_imbalance_ratio": quant_payload.get("orderbook_imbalance_ratio", 0.5),
            "liquidation_pocket_above": quant_payload.get("current_price", 50000.0) * 1.03,
            "liquidation_pocket_below": quant_payload.get("current_price", 50000.0) * 0.96,
        }

        whale_data = {
            "symbol": symbol,
            "exchange_netflow_24h_usd": quant_payload.get("netflow_24h_usd", 0.0),
            "cnai_score": quant_payload.get("cnai_score", 50.0),
        }

        vesting_data = {
            "symbol": symbol,
            "unlock_percent_of_circulating": (
                25.0 if "VESTING_CLIFF" in str(quant_payload.get("hard_red_flags", [])) else 0.0
            ),
        }

        # Run multi-agent pipeline
        state = await run_crypto_audit(
            symbol=symbol,
            execution_mode="DUAL_AUDIT",
            spot_valuation_data=spot_data,
            futures_squeeze_data=futures_data,
            whale_flow_data=whale_data,
            token_vesting_data=vesting_data,
            proposed_action="AUDIT_PROPOSAL",
            hard_red_flags=quant_payload.get("hard_red_flags", []),
        )

        # Invariant checks
        assert len(state["fatal_socratic_questions"]) == 3, (
            f"{case_id} failed: expected exactly 3 Socratic questions"
        )
        assert 0.0 <= state["fomo_index"] <= 100.0, (
            f"{case_id} failed: FOMO index {state['fomo_index']} out of [0, 100]"
        )

        # Strictly assert expected verdict and calibrated FOMO minimum
        assert state["anti_fomo_verdict"] == expected_verdict, (
            f"{case_id} expected verdict {expected_verdict}, got {state['anti_fomo_verdict']}"
        )
        if fomo_min > 0.0:
            assert state["fomo_index"] >= fomo_min, (
                f"{case_id} expected FOMO index >= {fomo_min}, got {state['fomo_index']}"
            )

        evaluated_count += 1

    assert evaluated_count == 10, "All 10 Golden Cases must be evaluated"
