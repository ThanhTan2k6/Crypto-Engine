"""
Unit tests for Deterministic Quant Engine: Mode Futures.
Verifies Annualized Funding Rate, FRSI, OI Change %, Orderbook Imbalance (OBIR), Liquidation Pockets.
"""

import pytest
from src.engine.futures_engine import FuturesRiskEngine
from src.ingestion.schemas import FuturesRiskLevel


def test_annualized_funding_rate():
    engine = FuturesRiskEngine()
    # 0.01% (0.0001) per 8h -> 0.0001 * 3 * 365 * 100 = 10.95%
    apr_baseline = engine.annualize_funding_rate(0.0001)
    assert apr_baseline == 10.95

    # 0.08% (0.0008) per 8h -> 0.0008 * 3 * 365 * 100 = 87.6%
    apr_hot = engine.annualize_funding_rate(0.0008)
    assert apr_hot == 87.6

    # Negative funding -0.1% (-0.0010) per 8h -> -109.5%
    apr_neg = engine.annualize_funding_rate(-0.0010)
    assert apr_neg == -109.5


def test_frsi_score():
    engine = FuturesRiskEngine()
    # 0% APR -> 50.0
    assert engine.calculate_frsi(0.0) == 50.0

    # 100% APR -> 100.0
    assert engine.calculate_frsi(100.0) == 100.0

    # -100% APR -> 0.0
    assert engine.calculate_frsi(-100.0) == 0.0

    # +87.6% APR -> (87.6 / 100) * 50 + 50 = 93.8
    assert engine.calculate_frsi(87.6) == 93.8


def test_orderbook_imbalance_ratio():
    engine = FuturesRiskEngine()
    # Heavy bids (bids total 80, asks total 20) -> 80 / 100 = 0.8
    bids = [[95000.0, 50.0], [94900.0, 30.0]]
    asks = [[95100.0, 10.0], [95200.0, 10.0]]
    obir = engine.calculate_orderbook_imbalance_ratio(bids, asks)
    assert obir == 0.8

    # Heavy asks (bids total 20, asks total 80) -> 20 / 100 = 0.2
    bids_thin = [[95000.0, 10.0], [94900.0, 10.0]]
    asks_heavy = [[95100.0, 50.0], [95200.0, 30.0]]
    obir_thin = engine.calculate_orderbook_imbalance_ratio(bids_thin, asks_heavy)
    assert obir_thin == 0.2


def test_liquidation_pockets():
    engine = FuturesRiskEngine()
    price = 95000.0
    high_24h = 96000.0
    low_24h = 93000.0

    pocket_above, pocket_below = engine.estimate_liquidation_pockets(price, high_24h, low_24h)
    assert pocket_above > price
    assert pocket_below < price
    assert pocket_above == 97440.0  # 96000 * 1.015
    assert pocket_below == 91140.0  # 93000 * 0.98


def test_full_futures_risk_evaluation():
    engine = FuturesRiskEngine()
    schema = engine.evaluate(
        symbol="BTCUSDT",
        current_price=95000.0,
        open_interest_usd=12000000000.0,
        oi_24h_ago=10500000000.0,
        funding_rate_8h=0.0008,
        long_short_ratio=2.85,
        bids=[[95000.0, 15.0]],
        asks=[[95100.0, 45.0]],
        high_24h=96500.0,
        low_24h=93500.0,
    )
    assert schema.symbol == "BTCUSDT"
    assert schema.annualized_funding_rate == 87.6
    assert schema.frsi_score > 90.0
    assert schema.futures_risk_level == FuturesRiskLevel.EXTREME_LONG_LIQUIDATION_RISK
    assert schema.orderbook_imbalance_ratio == 0.25
