"""
Unit and Integration Tests for Automated Quantitative Execution & Trading Bot.
Verifies Strategy Engine, Position Sizing (1.5% Risk Rule), Socratic Veto Filter,
Paper Trading Execution, and Mathematical EV Telemetry.
"""

import pytest

from src.execution import (
    BotMode,
    BotStatus,
    OrderRequest,
    PaperTradingEngine,
    PositionSizer,
    QuantitativeStrategyEngine,
    SignalDirection,
    SocraticRiskFilter,
    StrategyType,
    TradeSignal,
    TradingBotCoordinator,
)


def test_strategy_engine_liquidation_sweep_short():
    """Verify liquidation sweep generates sell signal on extreme long overheating."""
    engine = QuantitativeStrategyEngine()
    sig = engine.evaluate_liquidation_sweep(
        symbol="BTCUSDT",
        current_price=66000.0,
        frsi_score=82.0,
        annualized_funding=45.0,
        liquidation_pocket_above=66500.0,
        liquidation_pocket_below=63500.0,
        orderbook_imbalance=0.35,
    )

    assert sig is not None
    assert sig.direction == SignalDirection.SELL
    assert sig.strategy == StrategyType.LIQUIDATION_SWEEP_REVERSAL
    assert sig.stop_loss_price > sig.entry_price
    assert sig.take_profit_price < sig.entry_price
    assert sig.risk_reward_ratio >= 1.9


def test_strategy_engine_liquidation_sweep_long():
    """Verify liquidation sweep generates buy signal on extreme short crowding."""
    engine = QuantitativeStrategyEngine()
    sig = engine.evaluate_liquidation_sweep(
        symbol="BTCUSDT",
        current_price=63600.0,
        frsi_score=22.0,
        annualized_funding=-15.0,
        liquidation_pocket_above=67000.0,
        liquidation_pocket_below=63500.0,
        orderbook_imbalance=0.65,
    )

    assert sig is not None
    assert sig.direction == SignalDirection.BUY
    assert sig.stop_loss_price < sig.entry_price
    assert sig.take_profit_price > sig.entry_price
    assert sig.risk_reward_ratio >= 1.9


def test_position_sizer_risk_equation():
    """Verify PositionSizer enforces Quantity = Risk_USD / |Entry - StopLoss|."""
    sizer = PositionSizer(default_risk_pct=0.015)  # 1.5%
    equity = 10_000.0  # Risk budget = $150
    signal = TradeSignal(
        symbol="BTCUSDT",
        direction=SignalDirection.BUY,
        strategy=StrategyType.LIQUIDATION_SWEEP_REVERSAL,
        entry_price=60000.0,
        stop_loss_price=57000.0,  # Delta = $3,000
        take_profit_price=66000.0,
        risk_reward_ratio=2.0,
        rationale="Test",
    )

    order = sizer.calculate_order(signal=signal, equity_usd=equity, order_id="ord_1", mode=BotMode.PAPER_TRADING)
    assert order is not None
    # Expected quantity = 150 / 3000 = 0.05 BTC
    assert order.quantity == 0.05
    assert order.risk_usd == 150.0


def test_socratic_risk_filter_veto_logic():
    """Verify Socratic Risk Filter vetoes trades on high FOMO or red flag consensus."""
    filt = SocraticRiskFilter()
    signal = TradeSignal(
        symbol="BTCUSDT",
        direction=SignalDirection.BUY,
        strategy=StrategyType.SPOT_DCA_GRID,
        entry_price=65000.0,
        stop_loss_price=62000.0,
        take_profit_price=80000.0,
        risk_reward_ratio=5.0,
        rationale="Test",
    )

    # 1. Hard Rejection Veto
    approved, reason = filt.audit_and_verify(
        signal=signal,
        audit_state={"anti_fomo_verdict": "REJECT_SETUP_TOO_RISKY", "fomo_index": 85.0},
    )
    assert not approved
    assert "VETOED" in reason

    # 2. Approved on normal caution
    approved, _ = filt.audit_and_verify(
        signal=signal,
        audit_state={"anti_fomo_verdict": "PROCEED_WITH_CAUTION", "fomo_index": 35.0},
    )
    assert approved


def test_paper_trading_execution_and_tp_sl_triggers(tmp_path):
    """Verify PaperTradingEngine executes simulated orders and auto-triggers TP & SL."""
    state_file = str(tmp_path / "test_paper_triggers.json")
    paper = PaperTradingEngine(initial_balance_usd=10_000.0, state_file=state_file)

    order = OrderRequest(
        order_id="trade_test_1",
        symbol="BTCUSDT",
        direction=SignalDirection.BUY,
        quantity=0.1,
        price=60000.0,
        stop_loss=58000.0,
        take_profit=64000.0,
        risk_usd=200.0,
        strategy=StrategyType.LIQUIDATION_SWEEP_REVERSAL,
        mode=BotMode.PAPER_TRADING,
    )

    trade = paper.execute_order(order)
    assert trade.trade_id == "trade_test_1"
    assert "trade_test_1" in paper.active_positions

    # Price moves to $62,000 (Neither TP nor SL hit)
    closed = paper.update_market_price("BTCUSDT", 62000.0)
    assert len(closed) == 0
    assert len(paper.active_positions) == 1

    # Price hits Take-Profit $64,100
    closed = paper.update_market_price("BTCUSDT", 64100.0)
    assert len(closed) == 1
    assert closed[0].exit_reason == "TAKE_PROFIT"
    assert closed[0].is_winner is True
    # PnL = (64000 - 60000) * 0.1 = +$400 gross minus fee
    assert closed[0].realized_pnl_usd > 390.0
    assert len(paper.active_positions) == 0

    stats = paper.get_performance_stats()
    assert stats.total_trades == 1
    assert stats.winning_trades == 1
    assert stats.win_rate_pct == 100.0
    assert stats.expected_value_r > 0.0


@pytest.mark.asyncio
async def test_bot_coordinator_lifecycle_and_tick():
    """Verify master coordinator lifecycle and tick evaluation."""
    coordinator = TradingBotCoordinator(default_mode=BotMode.PAPER_TRADING)
    assert coordinator.status == BotStatus.STOPPED

    coordinator.start(mode=BotMode.PAPER_TRADING)
    assert coordinator.status == BotStatus.RUNNING

    dummy_quant = {
        "spot": type("MockSpot", (), {"mvrv_zscore": 1.5, "dca_zone_conservative": 65000.0, "dca_zone_aggressive": 48000.0, "take_profit_target_1": 85000.0})(),
        "futures": type("MockFutures", (), {"frsi_score": 50.0, "annualized_funding_rate": 5.0, "liquidation_pocket_above": 68000.0, "liquidation_pocket_below": 62000.0, "orderbook_imbalance_ratio": 0.50})(),
        "whale": type("MockWhale", (), {"netflow_24h_usd": -50_000_000.0})(),
    }

    tick_res = await coordinator.evaluate_tick(
        symbol="BTCUSDT",
        current_price=64000.0,
        quant_audit=dummy_quant,
        audit_state={"anti_fomo_verdict": "SCALE_IN_SPOT", "fomo_index": 20.0},
    )

    assert tick_res["bot_status"] == "RUNNING"
    coordinator.stop()
    assert coordinator.status == BotStatus.STOPPED


def test_paper_trading_disk_persistence(tmp_path):
    """Verify state persists to disk and reloads accurately on engine restart."""
    state_file = str(tmp_path / "paper_state.json")
    paper1 = PaperTradingEngine(initial_balance_usd=10_000.0, state_file=state_file)

    order = OrderRequest(
        order_id="persist_test_1",
        symbol="BTCUSDT",
        direction=SignalDirection.BUY,
        quantity=0.1,
        price=60000.0,
        stop_loss=59000.0,
        take_profit=63000.0,
        risk_usd=100.0,
        strategy=StrategyType.LIQUIDATION_SWEEP_REVERSAL,
        mode=BotMode.PAPER_TRADING,
    )
    paper1.execute_order(order)
    paper1.update_market_price("BTCUSDT", 63500.0)  # TP hit

    assert len(paper1.completed_trades) == 1
    assert paper1.completed_trades[0].realized_pnl_usd > 0

    # Simulate process termination and reinitialization
    paper2 = PaperTradingEngine(initial_balance_usd=10_000.0, state_file=state_file)
    assert len(paper2.completed_trades) == 1
    assert paper2.completed_trades[0].trade_id == "persist_test_1"
    assert paper2.balance_usd == paper1.balance_usd

    # Test reset
    paper2.reset_account(initial_balance=10_000.0)
    assert len(paper2.completed_trades) == 0
    assert paper2.balance_usd == 10_000.0


def test_historical_backtester_simulation():
    """Verify HistoricalBacktester runs deterministic math on synthetic klines."""
    from src.execution.backtest_engine import HistoricalBacktester

    tester = HistoricalBacktester(initial_balance_usd=10_000.0)

    # Generate 100 synthetic candles with an oscillating bounce
    synthetic_klines = []
    base_price = 60000.0
    for idx in range(100):
        # Create a dip and bounce
        price = base_price - (idx * 50.0) if idx < 50 else base_price - 2500.0 + ((idx - 50) * 80.0)
        synthetic_klines.append({
            "open_time": idx * 3600000,
            "open": price,
            "high": price + 200.0,
            "low": price - 200.0,
            "close": price + 50.0,
            "volume": 100.0,
            "close_time": (idx + 1) * 3600000 - 1,
        })

    result = tester.simulate(synthetic_klines, symbol="BTCUSDT", interval="1h")
    assert result.total_candles == 100
    assert result.initial_balance == 10_000.0
    assert isinstance(result.win_rate_pct, float)
    assert isinstance(result.profit_factor, float)
    assert isinstance(result.expected_value_r, float)

