"""
Unit tests for Deterministic Quant Engine: Mode Spot.
Verifies MVRV Z-Score, Mayer Multiple, 200W-MA, Pi Cycle, Algorithmic DCA & Take-Profit Zones.
"""

import pytest
from src.engine.spot_engine import SpotCycleEngine
from src.ingestion.schemas import CycleRegime


def test_mvrv_zscore_calculation():
    engine = SpotCycleEngine()
    # Market Cap: $1.8T, Realized Cap: $600B, Std: $300B -> (1800 - 600) / 300 = 4.0
    z = engine.calculate_mvrv_zscore(1800.0, 600.0, 300.0)
    assert z == 4.0

    # Generational bottom test: Market Cap $300B, Realized Cap $320B, Std $200B -> -0.1
    z_bot = engine.calculate_mvrv_zscore(300.0, 320.0, 200.0)
    assert z_bot == -0.1


def test_mayer_multiple():
    engine = SpotCycleEngine()
    # Price $60k, 200d SMA $50k -> 1.2
    mayer = engine.calculate_mayer_multiple(60000.0, 50000.0)
    assert mayer == 1.2


def test_pi_cycle_top_indicator():
    engine = SpotCycleEngine()
    # 111d SMA: 35k (*2 = 70k), 350d SMA: 68k -> 70k >= 68k (Triggered)
    assert engine.evaluate_pi_cycle_top(35000.0, 68000.0) is True

    # 111d SMA: 25k (*2 = 50k), 350d SMA: 68k -> 50k < 68k (Not triggered)
    assert engine.evaluate_pi_cycle_top(25000.0, 68000.0) is False


def test_cycle_regime_classification():
    engine = SpotCycleEngine()
    assert engine.classify_cycle_regime(0.05, 0.6) == CycleRegime.CYCLE_BOTTOM_CAPITULATION
    assert engine.classify_cycle_regime(1.2, 1.1) == CycleRegime.EARLY_ACCUMULATION
    assert engine.classify_cycle_regime(2.5, 1.4) == CycleRegime.MID_BULL_EXPANSION
    assert engine.classify_cycle_regime(4.2, 2.0) == CycleRegime.LATE_BULL_OVERHEATED
    assert engine.classify_cycle_regime(5.5, 2.7) == CycleRegime.CYCLE_TOP_EUPHORIA


def test_algorithmic_dca_and_tp_zones():
    engine = SpotCycleEngine()
    price = 100000.0
    realized_price = 45000.0
    sma_200w = 52000.0

    dca1, dca2, dca3 = engine.calculate_dca_zones(price, realized_price, sma_200w)
    assert dca1 == 92000.0   # 100k * 0.92
    assert dca2 == 85000.0   # max(45k, 85k)
    assert dca3 == 52000.0   # min(52k, 70k)

    tp1, tp2, tp3 = engine.calculate_take_profit_zones(price)
    assert tp1 == 135000.0   # 100k * 1.35
    assert tp2 == 175000.0   # 100k * 1.75
    assert tp3 == 250000.0   # 100k * 2.50


def test_full_spot_cycle_evaluation():
    engine = SpotCycleEngine()
    schema = engine.evaluate(
        symbol="BTCUSDT",
        current_price=95000.0,
        market_cap=1880000000000.0,
        realized_cap=750000000000.0,
        std_market_cap=300000000000.0,
        sma_200d=68000.0,
        sma_200w=48000.0,
        sma_111d=72000.0,
        sma_350d=65000.0,
    )
    assert schema.symbol == "BTCUSDT"
    assert schema.current_price == 95000.0
    assert schema.mvrv_zscore > 3.5
    assert schema.cycle_regime == CycleRegime.LATE_BULL_OVERHEATED
    assert schema.dca_zone_conservative < schema.current_price
    assert schema.take_profit_target_1 > schema.current_price
