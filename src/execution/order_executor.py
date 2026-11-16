"""
Order Execution Engines for CryptoIntel-Engine.
Supports:
1. PaperTradingEngine (High-fidelity simulation with TP/SL auto-triggers & TT200 accounting)
2. BinanceLiveExecutor (HMAC-SHA256 signed REST dispatch for live Binance accounts)
"""

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from src.engine.accounting_tt200 import (
    CryptoTransaction,
    TransactionType,
    TT200AccountCode,
    accounting_ledger,
)
from src.execution.schemas import (
    BotMode,
    BotPerformanceStats,
    OrderRequest,
    SignalDirection,
    TradeRecord,
)

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """
    Zero-Risk Simulated Execution Engine.
    Executes orders in memory, monitors live prices against Take-Profit / Stop-Loss bounds,
    and automatically books transactions into the TT 200 Accounting Ledger.
    """

    def __init__(
        self,
        initial_balance_usd: float = 10_000.0,
        fee_rate: float = 0.0004,
        state_file: str | None = None,
    ) -> None:
        self.initial_balance = float(initial_balance_usd)
        self.balance_usd: float = float(initial_balance_usd)
        self.fee_rate = fee_rate  # 0.04% standard maker/taker fee
        self.state_file: str = str(state_file or os.getenv("BOT_STATE_FILE") or "data/paper_trading_state.json")
        self.active_positions: dict[str, TradeRecord] = {}  # trade_id -> TradeRecord
        self.completed_trades: list[TradeRecord] = []
        self._peak_balance: float = float(initial_balance_usd)
        self._max_drawdown_pct: float = 0.0

        self._load_from_disk()

    def _save_to_disk(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            data = {
                "initial_balance": self.initial_balance,
                "balance_usd": self.balance_usd,
                "peak_balance": self._peak_balance,
                "max_drawdown_pct": self._max_drawdown_pct,
                "active_positions": {k: v.model_dump_json() for k, v in self.active_positions.items()},
                "completed_trades": [t.model_dump_json() for t in self.completed_trades],
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.warning("Failed to persist bot state to %s: %s", self.state_file, e)

    def _load_from_disk(self) -> None:
        if not os.path.exists(self.state_file):
            return
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.initial_balance = float(data.get("initial_balance", self.initial_balance))
            self.balance_usd = float(data.get("balance_usd", self.balance_usd))
            self._peak_balance = float(data.get("peak_balance", self._peak_balance))
            self._max_drawdown_pct = float(data.get("max_drawdown_pct", self._max_drawdown_pct))

            self.active_positions = {
                k: TradeRecord.model_validate_json(v)
                for k, v in data.get("active_positions", {}).items()
            }
            self.completed_trades = [
                TradeRecord.model_validate_json(t)
                for t in data.get("completed_trades", [])
            ]
            logger.info(
                "Loaded %d completed trades and %d open positions from %s",
                len(self.completed_trades),
                len(self.active_positions),
                self.state_file,
            )
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.warning("Could not parse existing bot state from %s: %s", self.state_file, e)

    def reset_account(self, initial_balance: float = 10_000.0) -> None:
        """Reset paper account balance and clear persisted trade history."""
        self.initial_balance = float(initial_balance)
        self.balance_usd = float(initial_balance)
        self.active_positions.clear()
        self.completed_trades.clear()
        self._peak_balance = float(initial_balance)
        self._max_drawdown_pct = 0.0
        self._save_to_disk()

    def execute_order(self, order: OrderRequest) -> TradeRecord:
        """Execute simulated order and register open position."""
        notional = order.quantity * order.price
        fee = notional * self.fee_rate
        self.balance_usd -= fee

        trade = TradeRecord(
            trade_id=order.order_id,
            symbol=order.symbol,
            direction=order.direction,
            strategy=order.strategy,
            entry_price=order.price,
            quantity=order.quantity,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            fee_usd=round(fee, 4),
            entry_time=datetime.now(UTC),
            mode=BotMode.PAPER_TRADING,
        )
        self.active_positions[order.order_id] = trade
        self._save_to_disk()

        # Book into Circular 200 Accounting Ledger
        try:
            acc_type = TT200AccountCode.TK_121  # Trading inventory
            act_type = TransactionType.BUY if order.direction == SignalDirection.BUY else TransactionType.SELL
            accounting_ledger.record_transaction(
                CryptoTransaction(
                    tx_id=f"paper_{order.order_id}",
                    timestamp=datetime.now(UTC),
                    symbol=order.symbol,
                    account=acc_type,
                    action=act_type,
                    quantity=order.quantity,
                    price_usd=order.price,
                    fee_usd=fee,
                    notes=f"Auto-Bot Paper Execution ({order.strategy.value})",
                )
            )
        except (ValueError, KeyError) as e:
            logger.warning("TT200 booking skipped for paper order %s: %s", order.order_id, e)

        return trade

    def update_market_price(self, symbol: str, current_price: float) -> list[TradeRecord]:
        """
        Check all active positions for symbol against Take-Profit and Stop-Loss.
        Automatically closes filled positions and updates PnL.
        """
        closed_this_tick: list[TradeRecord] = []
        trade_ids = list(self.active_positions.keys())

        for tid in trade_ids:
            pos = self.active_positions[tid]
            if pos.symbol != symbol:
                continue

            hit_tp = False
            hit_sl = False

            if pos.direction == SignalDirection.BUY:
                hit_tp = current_price >= pos.take_profit
                hit_sl = current_price <= pos.stop_loss
            elif pos.direction == SignalDirection.SELL:
                hit_tp = current_price <= pos.take_profit
                hit_sl = current_price >= pos.stop_loss

            if hit_tp or hit_sl:
                exit_price = pos.take_profit if hit_tp else pos.stop_loss
                reason = "TAKE_PROFIT" if hit_tp else "STOP_LOSS"

                # Calculate gross & net PnL
                if pos.direction == SignalDirection.BUY:
                    gross_pnl = (exit_price - pos.entry_price) * pos.quantity
                else:
                    gross_pnl = (pos.entry_price - exit_price) * pos.quantity

                exit_fee = (pos.quantity * exit_price) * self.fee_rate
                net_pnl = gross_pnl - pos.fee_usd - exit_fee

                pos.exit_price = round(exit_price, 4)
                pos.exit_time = datetime.now(UTC)
                pos.exit_reason = reason
                pos.realized_pnl_usd = round(net_pnl, 2)
                pos.fee_usd = round(pos.fee_usd + exit_fee, 4)
                pos.is_winner = net_pnl > 0.0

                self.balance_usd += net_pnl
                self._update_drawdown()

                # Book exit in TT200 accounting ledger
                try:
                    exit_action = (
                        TransactionType.SELL if pos.direction == SignalDirection.BUY else TransactionType.BUY
                    )
                    accounting_ledger.record_transaction(
                        CryptoTransaction(
                            tx_id=f"paper_exit_{pos.trade_id}",
                            timestamp=datetime.now(UTC),
                            symbol=pos.symbol,
                            account=TT200AccountCode.TK_121,
                            action=exit_action,
                            quantity=pos.quantity,
                            price_usd=exit_price,
                            fee_usd=exit_fee,
                            notes=f"Auto-Bot Paper Exit ({reason})",
                        )
                    )
                except (ValueError, KeyError) as e:
                    logger.warning("TT200 exit booking skipped for %s: %s", pos.trade_id, e)

                self.completed_trades.append(pos)
                closed_this_tick.append(pos)
                del self.active_positions[tid]

        if closed_this_tick:
            self._save_to_disk()

        return closed_this_tick

    def _update_drawdown(self) -> None:
        if self.balance_usd > self._peak_balance:
            self._peak_balance = self.balance_usd
        elif self._peak_balance > 0.0:
            dd = ((self._peak_balance - self.balance_usd) / self._peak_balance) * 100.0
            self._max_drawdown_pct = max(self._max_drawdown_pct, dd)

    def get_performance_stats(self) -> BotPerformanceStats:
        """Compute statistical win rate, profit factor, and mathematical EV."""
        total = len(self.completed_trades)
        if total == 0:
            return BotPerformanceStats(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                profit_factor=0.0,
                expected_value_r=0.0,
                total_realized_pnl_usd=0.0,
                current_balance_usd=round(self.balance_usd, 2),
                max_drawdown_pct=0.0,
            )

        winners = [t for t in self.completed_trades if (t.is_winner is True)]
        losers = [t for t in self.completed_trades if (t.is_winner is False)]
        n_win = len(winners)
        n_loss = len(losers)

        win_rate = (n_win / total) * 100.0
        gross_profit = sum(t.realized_pnl_usd for t in winners)
        gross_loss = abs(sum(t.realized_pnl_usd for t in losers))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)

        # Expected Value in R-multiples: EV = (win_rate * avg_win) - (loss_rate * avg_loss)
        avg_win_r = (gross_profit / n_win) if n_win > 0 else 0.0
        avg_loss_r = (gross_loss / n_loss) if n_loss > 0 else 1.0
        r_multiple = (avg_win_r / avg_loss_r) if avg_loss_r > 0 else 1.5
        p_win = n_win / total
        p_loss = n_loss / total
        ev_r = (p_win * r_multiple) - (p_loss * 1.0)

        total_pnl = sum(t.realized_pnl_usd for t in self.completed_trades)

        return BotPerformanceStats(
            total_trades=total,
            winning_trades=n_win,
            losing_trades=n_loss,
            win_rate_pct=round(win_rate, 2),
            profit_factor=round(profit_factor, 2),
            expected_value_r=round(ev_r, 3),
            total_realized_pnl_usd=round(total_pnl, 2),
            current_balance_usd=round(self.balance_usd, 2),
            max_drawdown_pct=round(self._max_drawdown_pct, 2),
        )


class BinanceLiveExecutor:
    """
    Live HMAC-SHA256 Signed Order Dispatcher for Binance Futures / Spot.
    Operates strictly when user provides explicit API credentials.
    """

    def __init__(self, api_key: str | None = None, api_secret: str | None = None) -> None:
        self.api_key: str = api_key or os.getenv("BINANCE_API_KEY") or ""
        self.api_secret: str = api_secret or os.getenv("BINANCE_SECRET_KEY") or ""
        self.base_url = "https://fapi.binance.com"

    def is_configured(self) -> bool:
        """Check if live trading credentials are provided."""
        return bool(self.api_key and self.api_secret)

    def _generate_signature(self, params: dict[str, Any]) -> str:
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def place_order(self, order: OrderRequest) -> dict[str, Any]:
        """Dispatch live signed order to Binance Futures."""
        if not self.is_configured():
            raise RuntimeError("Binance API credentials missing. Cannot dispatch live order.")

        endpoint = f"{self.base_url}/fapi/v1/order"
        timestamp = int(time.time() * 1000)
        side = "BUY" if order.direction == SignalDirection.BUY else "SELL"

        params: dict[str, Any] = {
            "symbol": order.symbol.upper(),
            "side": side,
            "type": "LIMIT",
            "quantity": order.quantity,
            "price": order.price,
            "timeInForce": "GTC",
            "timestamp": timestamp,
        }
        params["signature"] = self._generate_signature(params)
        headers = {"X-MBX-APIKEY": self.api_key}

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(endpoint, params=params, headers=headers)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data
