"""
Historical Backtesting Engine for CryptoIntel-Engine.
Simulates quant execution strategies on historical Binance candles.
Strict Zero LLM Arithmetic: 100% deterministic pure math.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.execution.schemas import SignalDirection
from src.ingestion.binance_client import BinancePublicClient

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    trade_id: int
    symbol: str
    direction: SignalDirection
    strategy: str
    entry_time_ms: int
    entry_price: float
    exit_time_ms: int
    exit_price: float
    stop_loss: float
    take_profit: float
    quantity: float
    pnl_usd: float
    is_winner: bool
    exit_reason: str


@dataclass
class BacktestResult:
    symbol: str
    interval: str
    total_candles: int
    initial_balance: float
    final_balance: float
    total_pnl_usd: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    profit_factor: float
    expected_value_r: float
    max_drawdown_pct: float
    trades: list[BacktestTrade]


class HistoricalBacktester:
    """Runs deterministic backtesting on Binance klines."""

    def __init__(
        self,
        initial_balance_usd: float = 10_000.0,
        risk_per_trade_pct: float = 0.015,
        fee_rate: float = 0.0004,
    ) -> None:
        self.initial_balance = initial_balance_usd
        self.risk_pct = risk_per_trade_pct
        self.fee_rate = fee_rate
        self.binance_client = BinancePublicClient()

    async def run_backtest(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        candle_count: int = 500,
        strategy_mode: str = "COMBINED_QUANT",
    ) -> BacktestResult:
        """Fetch historical klines and simulate trading strategies."""
        klines = await self.binance_client.get_historical_klines(
            symbol=symbol, interval=interval, limit=candle_count
        )
        return self.simulate(klines, symbol=symbol, interval=interval, strategy_mode=strategy_mode)

    def simulate(
        self,
        klines: list[dict[str, Any]],
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        strategy_mode: str = "COMBINED_QUANT",
    ) -> BacktestResult:
        """Simulate trades across kline series deterministically."""
        if len(klines) < 30:
            return BacktestResult(
                symbol=symbol,
                interval=interval,
                total_candles=len(klines),
                initial_balance=self.initial_balance,
                final_balance=self.initial_balance,
                total_pnl_usd=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                profit_factor=0.0,
                expected_value_r=0.0,
                max_drawdown_pct=0.0,
                trades=[],
            )

        balance = self.initial_balance
        peak_balance = self.initial_balance
        max_drawdown = 0.0
        trades: list[BacktestTrade] = []
        trade_id_counter = 1

        closes = [k["close"] for k in klines]

        # Calculate EMA 50 trend indicator
        ema50 = [closes[0]]
        alpha = 2.0 / (50 + 1)
        for c in closes[1:]:
            ema50.append(alpha * c + (1 - alpha) * ema50[-1])

        # Scan candle by candle
        i = 30
        while i < len(klines) - 1:
            current = klines[i]
            c_price = current["close"]
            c_high = current["high"]
            c_low = current["low"]
            c_open = current["open"]
            c_ema = ema50[i]

            # 20-period volatility bands
            window = closes[i - 20 : i]
            ma20 = sum(window) / 20.0
            variance = sum((x - ma20) ** 2 for x in window) / 20.0
            std20 = variance**0.5
            upper_band = ma20 + (2.0 * std20)
            lower_band = ma20 - (2.0 * std20)

            signal_direction: SignalDirection | None = None
            strat_label = ""
            entry_price = c_price
            stop_loss = 0.0
            take_profit = 0.0

            wick_top = c_high - max(c_open, c_price)
            wick_bottom = min(c_open, c_price) - c_low
            body = abs(c_price - c_open)

            # Strategy 1: Trend Pullback (High probability trend following)
            if strategy_mode in ("COMBINED_QUANT", "TREND_PULLBACK"):
                # Uptrend pullback to EMA50 and bounce
                if c_price > c_ema and c_low <= (c_ema * 1.003) and c_price >= c_open:
                    signal_direction = SignalDirection.BUY
                    strat_label = "TREND_PULLBACK_LONG"
                    stop_loss = round(c_low * 0.995, 2)
                    risk_dist = entry_price - stop_loss
                    if risk_dist > 0:
                        take_profit = round(entry_price + (risk_dist * 2.0), 2)  # 1:2.0 R:R
                    else:
                        signal_direction = None

                # Downtrend rally to EMA50 and rejection
                elif c_price < c_ema and c_high >= (c_ema * 0.997) and c_price <= c_open:
                    signal_direction = SignalDirection.SELL
                    strat_label = "TREND_PULLBACK_SHORT"
                    stop_loss = round(c_high * 1.005, 2)
                    risk_dist = stop_loss - entry_price
                    if risk_dist > 0:
                        take_profit = round(entry_price - (risk_dist * 2.0), 2)  # 1:2.0 R:R
                    else:
                        signal_direction = None

            # Strategy 2: Liquidation Sweep Reversal (Mean reversion at volatility extremes)
            # Enforce Trend Filter: Do NOT catch falling knives if price is breaking down sharply under EMA50 (>2%)
            if not signal_direction and strategy_mode in ("COMBINED_QUANT", "LIQUIDATION_SWEEP"):
                if c_low < lower_band and wick_bottom > body and c_price > c_low and c_price >= (c_ema * 0.98):
                    signal_direction = SignalDirection.BUY
                    strat_label = "LIQUIDATION_SWEEP_LONG"
                    stop_loss = round(c_low * 0.995, 2)
                    risk_dist = entry_price - stop_loss
                    if risk_dist > 0:
                        take_profit = round(entry_price + (risk_dist * 1.8), 2)  # 1:1.8 R:R
                    else:
                        signal_direction = None

                elif c_high > upper_band and wick_top > body and c_price < c_high and c_price <= (c_ema * 1.02):
                    signal_direction = SignalDirection.SELL
                    strat_label = "LIQUIDATION_SWEEP_SHORT"
                    stop_loss = round(c_high * 1.005, 2)
                    risk_dist = stop_loss - entry_price
                    if risk_dist > 0:
                        take_profit = round(entry_price - (risk_dist * 1.8), 2)  # 1:1.8 R:R
                    else:
                        signal_direction = None

            if signal_direction and stop_loss > 0 and take_profit > 0:
                # Sizing: strictly 1.5% fixed risk
                risk_usd = balance * self.risk_pct
                sl_distance = abs(entry_price - stop_loss)
                qty = risk_usd / sl_distance if sl_distance > 0 else 0.0

                # Simulate forward until exit
                exit_price = 0.0
                exit_time = current["close_time"]
                exit_reason = "TIMEOUT"
                j = i + 1

                while j < len(klines):
                    next_k = klines[j]
                    n_high = next_k["high"]
                    n_low = next_k["low"]

                    if signal_direction == SignalDirection.BUY:
                        if n_low <= stop_loss:  # Worst-case: SL checked first
                            exit_price = stop_loss
                            exit_time = next_k["close_time"]
                            exit_reason = "STOP_LOSS"
                            break
                        elif n_high >= take_profit:
                            exit_price = take_profit
                            exit_time = next_k["close_time"]
                            exit_reason = "TAKE_PROFIT"
                            break
                    else:  # SELL
                        if n_high >= stop_loss:
                            exit_price = stop_loss
                            exit_time = next_k["close_time"]
                            exit_reason = "STOP_LOSS"
                            break
                        elif n_low <= take_profit:
                            exit_price = take_profit
                            exit_time = next_k["close_time"]
                            exit_reason = "TAKE_PROFIT"
                            break
                    j += 1

                if exit_price == 0.0:
                    exit_price = klines[-1]["close"]
                    exit_time = klines[-1]["close_time"]
                    exit_reason = "PERIOD_END"

                if signal_direction == SignalDirection.BUY:
                    gross_pnl = (exit_price - entry_price) * qty
                else:
                    gross_pnl = (entry_price - exit_price) * qty

                total_fees = (entry_price * qty * self.fee_rate) + (exit_price * qty * self.fee_rate)
                net_pnl = gross_pnl - total_fees
                is_win = net_pnl > 0.0

                balance += net_pnl
                if balance > peak_balance:
                    peak_balance = balance
                elif peak_balance > 0.0:
                    dd = ((peak_balance - balance) / peak_balance) * 100.0
                    max_drawdown = max(max_drawdown, dd)

                trades.append(
                    BacktestTrade(
                        trade_id=trade_id_counter,
                        symbol=symbol,
                        direction=signal_direction,
                        strategy=strat_label,
                        entry_time_ms=current["open_time"],
                        entry_price=round(entry_price, 2),
                        exit_time_ms=exit_time,
                        exit_price=round(exit_price, 2),
                        stop_loss=round(stop_loss, 2),
                        take_profit=round(take_profit, 2),
                        quantity=round(qty, 4),
                        pnl_usd=round(net_pnl, 2),
                        is_winner=is_win,
                        exit_reason=exit_reason,
                    )
                )
                trade_id_counter += 1
                i = max(i + 1, j)
                continue

            i += 1

        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.is_winner)
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

        gross_profits = sum(t.pnl_usd for t in trades if t.is_winner)
        gross_losses = abs(sum(t.pnl_usd for t in trades if not t.is_winner))
        pf = (gross_profits / gross_losses) if gross_losses > 0 else (99.0 if gross_profits > 0 else 0.0)

        if total_trades > 0:
            avg_win = (gross_profits / winning_trades) if winning_trades > 0 else 0.0
            avg_loss = (gross_losses / losing_trades) if losing_trades > 0 else 1.0
            r_ratio = avg_win / avg_loss if avg_loss > 0 else 2.0
            win_p = winning_trades / total_trades
            loss_p = losing_trades / total_trades
            ev_r = (win_p * r_ratio) - (loss_p * 1.0)
        else:
            ev_r = 0.0

        return BacktestResult(
            symbol=symbol,
            interval=interval,
            total_candles=len(klines),
            initial_balance=self.initial_balance,
            final_balance=round(balance, 2),
            total_pnl_usd=round(balance - self.initial_balance, 2),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=round(win_rate, 2),
            profit_factor=round(pf, 2),
            expected_value_r=round(ev_r, 2),
            max_drawdown_pct=round(max_drawdown, 2),
            trades=trades,
        )
