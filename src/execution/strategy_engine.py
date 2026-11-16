"""
Quantitative Strategy Engine for CryptoIntel-Engine.
Implements 100% deterministic, rule-based signal generation with ZERO LLM Arithmetic.
Strategies:
1. Liquidation Sweep Reversal (Mean reversion from stop-hunt pockets)
2. Spot DCA Accumulation Grid (Cycle floor accumulation with +35% TP)
3. Orderbook Imbalance Flow (OBIR + Whale CEX netflow divergence)
"""

from typing import Any

from src.execution.schemas import SignalDirection, StrategyType, TradeSignal


class QuantitativeStrategyEngine:
    """Master Deterministic Strategy Generator."""

    @staticmethod
    def evaluate_liquidation_sweep(
        symbol: str,
        current_price: float,
        frsi_score: float,
        annualized_funding: float,
        liquidation_pocket_above: float,
        liquidation_pocket_below: float,
        orderbook_imbalance: float,
    ) -> TradeSignal | None:
        """
        Evaluate Liquidation Sweep Reversal Strategy.
        Exploits over-leveraged stop-runs and funding rate squeezes.
        """
        # Condition A: Extreme Long Crowding (FRSI > 75, High positive funding, or test of pocket above)
        if (frsi_score >= 70.0 or annualized_funding >= 30.0) and current_price >= (liquidation_pocket_above * 0.985):
            sl = liquidation_pocket_above * 1.012
            risk = abs(sl - current_price)
            if risk <= 0:
                return None
            tp = current_price - (risk * 2.0)  # Enforce 1:2 R:R
            if tp <= 0:
                return None
            rr = round(abs(current_price - tp) / risk, 2)
            return TradeSignal(
                symbol=symbol,
                direction=SignalDirection.SELL,
                strategy=StrategyType.LIQUIDATION_SWEEP_REVERSAL,
                entry_price=round(current_price, 4),
                stop_loss_price=round(sl, 4),
                take_profit_price=round(tp, 4),
                risk_reward_ratio=rr,
                rationale=(
                    f"FRSI {frsi_score:.1f} and funding {annualized_funding:.1f}% indicate over-leveraged longs. "
                    f"Anticipating short squeeze rejection near liquidation pocket ${liquidation_pocket_above:,.2f}."
                ),
            )

        # Condition B: Extreme Short Crowding (FRSI < 30, Negative funding, or test of pocket below)
        if (frsi_score <= 30.0 or annualized_funding <= -10.0) and current_price <= (liquidation_pocket_below * 1.015):
            sl = liquidation_pocket_below * 0.988
            risk = abs(current_price - sl)
            if risk <= 0:
                return None
            tp = current_price + (risk * 2.0)  # Enforce 1:2 R:R
            rr = round(abs(tp - current_price) / risk, 2)
            return TradeSignal(
                symbol=symbol,
                direction=SignalDirection.BUY,
                strategy=StrategyType.LIQUIDATION_SWEEP_REVERSAL,
                entry_price=round(current_price, 4),
                stop_loss_price=round(sl, 4),
                take_profit_price=round(tp, 4),
                risk_reward_ratio=rr,
                rationale=(
                    f"FRSI {frsi_score:.1f} indicates extreme short crowding. "
                    f"Anticipating long reversal bounce from stop-sweep pocket ${liquidation_pocket_below:,.2f}."
                ),
            )

        return None

    @staticmethod
    def evaluate_spot_dca_grid(
        symbol: str,
        current_price: float,
        mvrv_zscore: float,
        dca_conservative: float,
        dca_aggressive: float,
        tp_target_1: float,
    ) -> TradeSignal | None:
        """
        Evaluate Spot DCA Accumulation Strategy.
        Buys when price enters conservative or moderate DCA zones with MVRV < 2.5.
        """
        if mvrv_zscore <= 2.5 and current_price <= (dca_conservative * 1.02):
            sl = dca_aggressive * 0.90
            risk = abs(current_price - sl)
            if risk <= 0:
                return None
            tp = max(tp_target_1, current_price * 1.25)
            rr = round(abs(tp - current_price) / risk, 2)
            if rr < 1.2:
                return None
            return TradeSignal(
                symbol=symbol,
                direction=SignalDirection.BUY,
                strategy=StrategyType.SPOT_DCA_GRID,
                entry_price=round(current_price, 4),
                stop_loss_price=round(sl, 4),
                take_profit_price=round(tp, 4),
                risk_reward_ratio=rr,
                rationale=(
                    f"MVRV Z-Score {mvrv_zscore:.2f} confirms fair/undervalued cycle regime. "
                    f"Price tested algorithmic accumulation zone ${dca_conservative:,.2f}."
                ),
            )
        return None

    @staticmethod
    def evaluate_orderbook_flow(
        symbol: str,
        current_price: float,
        obir: float,
        netflow_24h_usd: float,
        frsi_score: float,
    ) -> TradeSignal | None:
        """
        Evaluate Orderbook Imbalance Flow Strategy.
        Follows smart-money depth and whale exchange outflows.
        """
        # Long Flow: Heavy Bid Depth (OBIR >= 0.65) + Whale CEX Outflow (Netflow <= 0)
        if obir >= 0.65 and netflow_24h_usd <= 0 and 35.0 <= frsi_score <= 65.0:
            sl = current_price * 0.985  # 1.5% SL
            tp = current_price * 1.030  # 3.0% TP -> 1:2 R:R
            return TradeSignal(
                symbol=symbol,
                direction=SignalDirection.BUY,
                strategy=StrategyType.ORDERBOOK_IMBALANCE_FLOW,
                entry_price=round(current_price, 4),
                stop_loss_price=round(sl, 4),
                take_profit_price=round(tp, 4),
                risk_reward_ratio=2.0,
                rationale=(
                    f"OBIR {obir:.2f} shows strong buyer bid depth. "
                    f"Whale CEX netflow is negative (${netflow_24h_usd / 1e6:,.1f}M) indicating cold storage accumulation."
                ),
            )

        # Short Flow: Heavy Ask Depth (OBIR <= 0.35) + Whale CEX Inflow (> $100M)
        if obir <= 0.35 and netflow_24h_usd >= 100_000_000.0 and frsi_score >= 55.0:
            sl = current_price * 1.015  # 1.5% SL
            tp = current_price * 0.970  # 3.0% TP -> 1:2 R:R
            return TradeSignal(
                symbol=symbol,
                direction=SignalDirection.SELL,
                strategy=StrategyType.ORDERBOOK_IMBALANCE_FLOW,
                entry_price=round(current_price, 4),
                stop_loss_price=round(sl, 4),
                take_profit_price=round(tp, 4),
                risk_reward_ratio=2.0,
                rationale=(
                    f"OBIR {obir:.2f} reveals heavy seller ask pressure. "
                    f"Whales deposited ${netflow_24h_usd / 1e6:,.1f}M onto CEX, increasing dump probability."
                ),
            )

        return None

    def scan_for_signals(
        self,
        symbol: str,
        current_price: float,
        quant_data: dict[str, Any],
    ) -> list[TradeSignal]:
        """Scan all quantitative strategies and return valid actionable signals."""
        spot = quant_data.get("spot")
        futures = quant_data.get("futures")
        whale = quant_data.get("whale")

        if not spot or not futures or not whale:
            return []

        signals: list[TradeSignal] = []

        # 1. Check Liquidation Sweep
        sig_sweep = self.evaluate_liquidation_sweep(
            symbol=symbol,
            current_price=current_price,
            frsi_score=futures.frsi_score,
            annualized_funding=futures.annualized_funding_rate,
            liquidation_pocket_above=futures.liquidation_pocket_above,
            liquidation_pocket_below=futures.liquidation_pocket_below,
            orderbook_imbalance=futures.orderbook_imbalance_ratio,
        )
        if sig_sweep:
            signals.append(sig_sweep)

        # 2. Check Spot DCA Grid
        sig_dca = self.evaluate_spot_dca_grid(
            symbol=symbol,
            current_price=current_price,
            mvrv_zscore=spot.mvrv_zscore,
            dca_conservative=spot.dca_zone_conservative,
            dca_aggressive=spot.dca_zone_aggressive,
            tp_target_1=spot.take_profit_target_1,
        )
        if sig_dca:
            signals.append(sig_dca)

        # 3. Check Orderbook Flow
        netflow = getattr(whale, "netflow_24h_usd", getattr(whale, "exchange_netflow_24h_usd", 0.0))
        sig_flow = self.evaluate_orderbook_flow(
            symbol=symbol,
            current_price=current_price,
            obir=futures.orderbook_imbalance_ratio,
            netflow_24h_usd=netflow,
            frsi_score=futures.frsi_score,
        )
        if sig_flow:
            signals.append(sig_flow)

        return signals
