"""
Unit Tests for Deterministic Circular 200 Accounting & Impairment Engine.
Verifies FIFO, Moving Average, TK 2291 Impairment Provisions, and PnL separation.
"""

from datetime import UTC, datetime

import pytest

from src.engine.accounting_tt200 import (
    CryptoTransaction,
    InventoryCostMethod,
    TransactionType,
    TT200AccountCode,
    TT200AccountingEngine,
)


def test_tt200_fifo_costing_and_realized_pnl():
    """Verify First-In-First-Out depletion and realized PnL calculation."""
    engine = TT200AccountingEngine(
        costing_method=InventoryCostMethod.FIFO,
        initial_cash_usd=500_000.0,
    )

    # Buy Lot 1: 2 BTC @ $50,000 = $100,000
    engine.record_transaction(
        CryptoTransaction(
            tx_id="tx_1",
            timestamp=datetime.now(UTC),
            symbol="BTCUSDT",
            account=TT200AccountCode.TK_121,
            action=TransactionType.BUY,
            quantity=2.0,
            price_usd=50000.0,
            fee_usd=0.0,
        )
    )

    # Buy Lot 2: 3 BTC @ $60,000 = $180,000
    engine.record_transaction(
        CryptoTransaction(
            tx_id="tx_2",
            timestamp=datetime.now(UTC),
            symbol="BTCUSDT",
            account=TT200AccountCode.TK_121,
            action=TransactionType.BUY,
            quantity=3.0,
            price_usd=60000.0,
            fee_usd=0.0,
        )
    )

    # Sell 2.5 BTC @ $70,000
    # FIFO should deplete:
    # 2.0 BTC from Lot 1 @ $50,000 = $100,000
    # 0.5 BTC from Lot 2 @ $60,000 = $30,000
    # Total COGS = $130,000
    # Proceeds = 2.5 * $70,000 = $175,000
    # Realized Gain = $175,000 - $130,000 = $45,000
    sell_res = engine.record_transaction(
        CryptoTransaction(
            tx_id="tx_3",
            timestamp=datetime.now(UTC),
            symbol="BTCUSDT",
            account=TT200AccountCode.TK_121,
            action=TransactionType.SELL,
            quantity=2.5,
            price_usd=70000.0,
            fee_usd=0.0,
        )
    )

    assert sell_res["cost_basis_usd"] == 130000.0
    assert sell_res["proceeds_usd"] == 175000.0
    assert sell_res["realized_pnl_usd"] == 45000.0
    assert engine.cumulative_realized_pnl == 45000.0

    # Remaining in inventory: 2.5 BTC from Lot 2 @ $60,000 = $150,000
    sheet = engine.evaluate_portfolio({"BTCUSDT": 70000.0})
    pos = sheet.positions[0]
    assert pos.total_quantity == 2.5
    assert pos.total_book_value_usd == 150000.0
    assert pos.average_unit_cost_usd == 60000.0
    assert pos.market_value_usd == 175000.0
    assert pos.unrealized_pnl_usd == 25000.0
    assert pos.impairment_provision_required_usd == 0.0
    assert not pos.is_impaired


def test_tt200_moving_average_costing():
    """Verify Moving Weighted Average cost calculation."""
    engine = TT200AccountingEngine(
        costing_method=InventoryCostMethod.MOVING_AVERAGE,
        initial_cash_usd=500_000.0,
    )

    # Buy 2 BTC @ $40,000 = $80,000
    engine.record_transaction(
        CryptoTransaction(
            tx_id="ma_1",
            timestamp=datetime.now(UTC),
            symbol="BTCUSDT",
            account=TT200AccountCode.TK_121,
            action=TransactionType.BUY,
            quantity=2.0,
            price_usd=40000.0,
        )
    )

    # Buy 2 BTC @ $60,000 = $120,000
    # Total: 4 BTC, Book Value = $200,000 -> Unit Average = $50,000
    engine.record_transaction(
        CryptoTransaction(
            tx_id="ma_2",
            timestamp=datetime.now(UTC),
            symbol="BTCUSDT",
            account=TT200AccountCode.TK_121,
            action=TransactionType.BUY,
            quantity=2.0,
            price_usd=60000.0,
        )
    )

    # Sell 1 BTC @ $65,000
    # COGS should be 1.0 * $50,000 = $50,000
    # Realized Gain = $15,000
    sell_res = engine.record_transaction(
        CryptoTransaction(
            tx_id="ma_3",
            timestamp=datetime.now(UTC),
            symbol="BTCUSDT",
            account=TT200AccountCode.TK_121,
            action=TransactionType.SELL,
            quantity=1.0,
            price_usd=65000.0,
        )
    )

    assert sell_res["cost_basis_usd"] == 50000.0
    assert sell_res["realized_pnl_usd"] == 15000.0


def test_tt200_impairment_provision_tk2291():
    """
    Verify Circular 200 Impairment Rule:
    Target Provision = max(0, Book Value - Market Value).
    """
    engine = TT200AccountingEngine(costing_method=InventoryCostMethod.FIFO)

    # Buy 10 ETH @ $4,000 = $40,000
    engine.record_transaction(
        CryptoTransaction(
            tx_id="eth_1",
            timestamp=datetime.now(UTC),
            symbol="ETHUSDT",
            account=TT200AccountCode.TK_121,
            action=TransactionType.BUY,
            quantity=10.0,
            price_usd=4000.0,
        )
    )

    # Market price crashes to $3,200 (Market Value = $32,000)
    # Impairment target = $40,000 - $32,000 = $8,000
    sheet = engine.evaluate_portfolio({"ETHUSDT": 3200.0})
    pos = sheet.positions[0]

    assert pos.is_impaired
    assert pos.impairment_provision_required_usd == 8000.0
    assert sheet.total_impairment_provision_usd == 8000.0
    assert sheet.net_carrying_value_usd == 32000.0


def test_tt200_insufficient_inventory_raises_error():
    """Verify that attempting to sell more than available inventory raises ValueError."""
    engine = TT200AccountingEngine()

    engine.record_transaction(
        CryptoTransaction(
            tx_id="sol_1",
            timestamp=datetime.now(UTC),
            symbol="SOLUSDT",
            account=TT200AccountCode.TK_121,
            action=TransactionType.BUY,
            quantity=5.0,
            price_usd=150.0,
        )
    )

    with pytest.raises(ValueError, match="Insufficient inventory"):
        engine.record_transaction(
            CryptoTransaction(
                tx_id="sol_sell_excess",
                timestamp=datetime.now(UTC),
                symbol="SOLUSDT",
                account=TT200AccountCode.TK_121,
                action=TransactionType.SELL,
                quantity=10.0,
                price_usd=160.0,
            )
        )
