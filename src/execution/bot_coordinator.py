"""
Trading Bot Master Coordinator for CryptoIntel-Engine.
Orchestrates Strategy Engine, Socratic Veto Filter, Risk Manager, and Order Execution.
Maintains stateful telemetry and paper-trading balances.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from src.execution.order_executor import BinanceLiveExecutor, PaperTradingEngine
from src.execution.risk_manager import PositionSizer, SocraticRiskFilter
from src.execution.schemas import (
    BotMode,
    BotPerformanceStats,
    BotStatus,
    OrderRequest,
    StrategyType,
    TradeRecord,
)
from src.execution.strategy_engine import QuantitativeStrategyEngine

logger = logging.getLogger(__name__)


class TradingBotCoordinator:
    """
    Central Controller for Automated Quantitative Trading Bot.
    Guarantees deterministic execution, anti-FOMO veto checks, and strict 1.5% capital risk sizing.
    """

    def __init__(self, default_mode: BotMode = BotMode.PAPER_TRADING) -> None:
        self.status: BotStatus = BotStatus.STOPPED
        self.mode: BotMode = default_mode
        self.enabled_strategies: list[StrategyType] = [
            StrategyType.LIQUIDATION_SWEEP_REVERSAL,
            StrategyType.SPOT_DCA_GRID,
            StrategyType.ORDERBOOK_IMBALANCE_FLOW,
        ]
        self.strategy_engine = QuantitativeStrategyEngine()
        self.risk_sizer = PositionSizer(default_risk_pct=0.015)
        self.risk_filter = SocraticRiskFilter()
        self.paper_engine = PaperTradingEngine(initial_balance_usd=10_000.0)
        self.live_executor = BinanceLiveExecutor()

        self.last_tick_time: datetime | None = None
        self.activity_logs: list[dict[str, Any]] = []

    def start(self, mode: BotMode = BotMode.PAPER_TRADING) -> None:
        """Start or resume automated trading bot."""
        self.status = BotStatus.RUNNING
        self.mode = mode
        self._log_event("BOT_START", f"Bot started in {mode.value} mode.")

    def stop(self) -> None:
        """Stop automated trading bot."""
        self.status = BotStatus.STOPPED
        self._log_event("BOT_STOP", "Bot execution stopped.")

    def pause(self) -> None:
        """Pause automated trade generation."""
        self.status = BotStatus.PAUSED
        self._log_event("BOT_PAUSE", "Bot execution paused.")

    def set_enabled_strategies(self, strategies: list[StrategyType]) -> None:
        """Update allowed strategy types."""
        self.enabled_strategies = list(strategies)
        self._log_event("STRATEGY_UPDATE", f"Active strategies: {[s.value for s in strategies]}")

    def _log_event(self, event_type: str, message: str, data: dict[str, Any] | None = None) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event_type,
            "message": message,
            "data": data or {},
        }
        self.activity_logs.append(entry)
        if len(self.activity_logs) > 300:
            self.activity_logs = self.activity_logs[-300:]

    async def evaluate_tick(
        self,
        symbol: str,
        current_price: float,
        quant_audit: dict[str, Any],
        audit_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a single evaluation cycle:
        1. Check active positions against current price (auto-close TP/SL).
        2. If RUNNING, scan for new signals and execute through risk filter.
        """
        self.last_tick_time = datetime.now(UTC)

        # 1. Update active paper positions
        closed_trades = self.paper_engine.update_market_price(symbol, current_price)
        for closed in closed_trades:
            self._log_event(
                "TRADE_CLOSED",
                f"Closed {closed.direction.value} {closed.quantity} {closed.symbol} via {closed.exit_reason}: PnL ${closed.realized_pnl_usd:+,.2f}",
                closed.model_dump(),
            )

        if self.status != BotStatus.RUNNING:
            return {
                "bot_status": self.status.value,
                "mode": self.mode.value,
                "closed_trades_count": len(closed_trades),
                "active_positions_count": len(self.paper_engine.active_positions),
                "action": "SKIPPED_NOT_RUNNING",
            }

        # Don't open more than 3 simultaneous positions on the same symbol
        active_on_symbol = [t for t in self.paper_engine.active_positions.values() if t.symbol == symbol]
        if len(active_on_symbol) >= 3:
            return {
                "bot_status": self.status.value,
                "mode": self.mode.value,
                "action": "SKIPPED_MAX_EXPOSURE_REACHED",
                "active_positions_count": len(self.paper_engine.active_positions),
            }

        # 2. Scan quantitative signals
        all_signals = self.strategy_engine.scan_for_signals(
            symbol=symbol,
            current_price=current_price,
            quant_data=quant_audit,
        )

        candidate_signals = [s for s in all_signals if s.strategy in self.enabled_strategies]
        if not candidate_signals:
            return {
                "bot_status": self.status.value,
                "mode": self.mode.value,
                "action": "NO_SIGNALS",
                "active_positions_count": len(self.paper_engine.active_positions),
            }

        executed_orders: list[OrderRequest] = []
        vetoed_signals: list[dict[str, str]] = []

        # 3. Process candidate signals through Socratic Risk Gate
        for sig in candidate_signals:
            # Check Socratic Veto
            approved, reason = self.risk_filter.audit_and_verify(
                signal=sig,
                audit_state=audit_state,
                quant_data=quant_audit,
            )

            if not approved:
                vetoed_signals.append({"signal": sig.direction.value, "strategy": sig.strategy.value, "reason": reason})
                self._log_event("SIGNAL_VETOED", f"Vetoed {sig.strategy.value} signal: {reason}")
                continue

            # Calculate mathematical position size
            order_id = f"ord_{int(datetime.now(UTC).timestamp())}_{sig.direction.value.lower()}"
            equity = self.paper_engine.balance_usd
            order = self.risk_sizer.calculate_order(
                signal=sig,
                equity_usd=equity,
                order_id=order_id,
                mode=self.mode,
            )

            if not order:
                self._log_event("ORDER_SIZING_SKIPPED", "Position sizing resulted in sub-minimum order.")
                continue

            # Execute order
            if self.mode == BotMode.PAPER_TRADING:
                trade_rec = self.paper_engine.execute_order(order)
                executed_orders.append(order)
                self._log_event(
                    "ORDER_EXECUTED_PAPER",
                    f"Opened {trade_rec.direction.value} {trade_rec.quantity} {trade_rec.symbol} @ ${trade_rec.entry_price:,.2f} "
                    f"(SL: ${trade_rec.stop_loss:,.2f}, TP: ${trade_rec.take_profit:,.2f})",
                    trade_rec.model_dump(),
                )
            elif self.mode == BotMode.LIVE_BINANCE:
                if self.live_executor.is_configured():
                    try:
                        live_res = await self.live_executor.place_order(order)
                        executed_orders.append(order)
                        self._log_event("ORDER_EXECUTED_LIVE", f"Live order placed: {live_res}")
                    except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                        self._log_event("LIVE_ORDER_FAILED", f"Live dispatch failed: {e}")
                else:
                    self._log_event("LIVE_ORDER_BLOCKED", "Binance API keys not configured. Trade blocked.")

        return {
            "bot_status": self.status.value,
            "mode": self.mode.value,
            "executed_orders": [o.model_dump() for o in executed_orders],
            "vetoed_signals": vetoed_signals,
            "active_positions_count": len(self.paper_engine.active_positions),
            "performance": self.paper_engine.get_performance_stats().model_dump(),
        }

    def get_stats(self) -> BotPerformanceStats:
        """Return quantitative performance telemetry."""
        return self.paper_engine.get_performance_stats()

    def get_active_positions(self) -> list[TradeRecord]:
        """Return list of currently active open positions."""
        return list(self.paper_engine.active_positions.values())

    def get_trade_history(self) -> list[TradeRecord]:
        """Return list of closed trades."""
        return list(self.paper_engine.completed_trades)


# Global Bot Coordinator instance
trading_bot_coordinator = TradingBotCoordinator()
