"""
Unit tests for Deterministic Quant Engine: Whale Netflows, Tether Minting, Spot ETF & Token Vesting.
"""

from datetime import datetime, timezone, timedelta
import pytest
from src.engine.whale_engine import WhaleFlowEngine


def test_netflow_zscore_and_cnai():
    engine = WhaleFlowEngine()
    # High Inflow: Netflow +$600M, Mean $0, Std $200M -> Z = +3.0 -> CNAI = 50 - (3.0 * 15) = 5.0
    z_inflow = engine.calculate_netflow_zscore(600.0, 0.0, 200.0)
    assert z_inflow == 3.0
    cnai_dump = engine.calculate_cnai(z_inflow)
    assert cnai_dump == 5.0
    assert engine.classify_whale_sentiment(cnai_dump) == "DISTRIBUTION"

    # High Outflow (Accumulation): Netflow -$600M -> Z = -3.0 -> CNAI = 50 - (-3.0 * 15) = 95.0
    z_outflow = engine.calculate_netflow_zscore(-600.0, 0.0, 200.0)
    assert z_outflow == -3.0
    cnai_accum = engine.calculate_cnai(z_outflow)
    assert cnai_accum == 95.0
    assert engine.classify_whale_sentiment(cnai_accum) == "ACCUMULATION"


def test_etf_momentum_index():
    engine = WhaleFlowEngine()
    # 5d Net Inflow: $1B, 5d Avg Spot Vol: $20B -> 5.0%
    eimi = engine.calculate_etf_momentum_index(1000000000.0, 20000000000.0)
    assert eimi == 5.0


def test_token_vesting_dilution():
    engine = WhaleFlowEngine()
    # BTC (Low Dilution): 94% circulating, FDV/MC 1.06, 0% unlock
    btc_vesting = engine.evaluate_token_vesting(
        symbol="BTC",
        circulating_supply=19800000.0,
        total_supply=21000000.0,
        market_cap_usd=1880000000000.0,
        fdv_usd=1995000000000.0,
    )
    assert btc_vesting.dilution_risk == "LOW"
    assert btc_vesting.fdv_mc_ratio == 1.06

    # Predatory Low Float Token: 8% circulating, FDV/MC 12.5, 25% unlock cliff
    unlock_dt = datetime.now(timezone.utc) + timedelta(days=5)
    predatory_vesting = engine.evaluate_token_vesting(
        symbol="SUI",
        circulating_supply=80000000.0,
        total_supply=1000000000.0,
        market_cap_usd=960000000.0,
        fdv_usd=12000000000.0,
        next_unlock_date=unlock_dt,
        next_unlock_amount_usd=240000000.0,
    )
    assert predatory_vesting.dilution_risk == "HIGH_PREDATORY_UNLOCK"
    assert predatory_vesting.next_unlock_pct_of_circulating == 25.0
