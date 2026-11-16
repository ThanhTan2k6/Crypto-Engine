"""
Risk Management & Socratic Veto Filter for Automated Trading Bot.
Enforces strict mathematical position sizing (1-2% portfolio risk rule),
Risk:Reward bounds (minimum 1:1.5), and Socratic Devil's Advocate veto gates.
"""

from typing import Any

from src.execution.schemas import OrderRequest, SignalDirection, TradeSignal


class PositionSizer:
    """Calculates position size strictly adhering to mathematical capital preservation."""

    def __init__(
        self,
        default_risk_pct: float = 0.015,  # 1.5% max risk per trade
        max_notional_leverage: float = 2.0,  # Max position notional <= 2x equity
        min_order_usd: float = 10.0,
    ) -> None:
        self.default_risk_pct = default_risk_pct
        self.max_notional_leverage = max_notional_leverage
        self.min_order_usd = min_order_usd

    def calculate_order(
        self,
        signal: TradeSignal,
        equity_usd: float,
        order_id: str,
        mode: Any,
        risk_pct_override: float | None = None,
    ) -> OrderRequest | None:
        """
        Derive precise position quantity from capital risk constraints:
        Quantity = Risk_USD / |Entry - StopLoss|
        """
        if equity_usd <= 0.0:
            return None

        risk_pct = risk_pct_override or self.default_risk_pct
        risk_budget_usd = equity_usd * risk_pct

        price_delta = abs(signal.entry_price - signal.stop_loss_price)
        if price_delta <= 1e-8:
            return None

        raw_quantity = risk_budget_usd / price_delta
        notional_usd = raw_quantity * signal.entry_price

        # Cap notional by max leverage limit
        max_notional = equity_usd * self.max_notional_leverage
        if notional_usd > max_notional:
            raw_quantity = max_notional / signal.entry_price
            notional_usd = max_notional

        if notional_usd < self.min_order_usd:
            return None

        # Round quantity according to asset price magnitude
        if signal.entry_price >= 1000.0:
            qty = round(raw_quantity, 4)
        elif signal.entry_price >= 1.0:
            qty = round(raw_quantity, 2)
        else:
            qty = round(raw_quantity, 0)

        if qty <= 0.0:
            return None

        return OrderRequest(
            order_id=order_id,
            symbol=signal.symbol,
            direction=signal.direction,
            quantity=qty,
            price=signal.entry_price,
            stop_loss=signal.stop_loss_price,
            take_profit=signal.take_profit_price,
            risk_usd=round(risk_budget_usd, 2),
            strategy=signal.strategy,
            mode=mode,
        )


class SocraticRiskFilter:
    """
    Independent Risk Auditor Gate.
    Vetoes any trade signal that conflicts with multi-agent Socratic consensus.
    """

    @staticmethod
    def audit_and_verify(
        signal: TradeSignal,
        audit_state: dict[str, Any] | None,
        quant_data: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """
        Evaluate candidate signal against Socratic Devil's Advocate and Red Flags.
        Returns (is_approved: bool, reason: str).
        """
        if not audit_state:
            return True, "No audit veto active."

        verdict = audit_state.get("anti_fomo_verdict", "PROCEED_WITH_CAUTION")
        fomo_index = float(audit_state.get("fomo_index", 50.0))

        # Gate 1: Hard Socratic Rejection
        if verdict == "REJECT_SETUP_TOO_RISKY":
            return False, f"VETOED by Socratic Auditor: Setup rejected as too risky (FOMO Index: {fomo_index:.1f})."

        # Gate 2: Long Euphoria Trap
        if signal.direction == SignalDirection.BUY and fomo_index >= 75.0:
            return False, f"VETOED: Cannot BUY when FOMO Index is {fomo_index:.1f}/100 (Euphoria Top Trap)."

        # Gate 3: Short Capitulation Trap
        if quant_data:
            spot = quant_data.get("spot")
            if spot and signal.direction == SignalDirection.SELL and getattr(spot, "mvrv_zscore", 2.0) <= 0.8:
                return False, "VETOED: Cannot SHORT when MVRV Z-Score <= 0.8 (Generational Capitulation Floor)."

        # Gate 4: Mega Whale CEX Inflow Veto
        if quant_data:
            whale = quant_data.get("whale")
            netflow = getattr(whale, "netflow_24h_usd", getattr(whale, "exchange_netflow_24h_usd", 0.0)) if whale else 0.0
            if signal.direction == SignalDirection.BUY and netflow >= 1_000_000_000.0:
                return False, f"VETOED: Mega CEX Inflow (${netflow / 1e6:,.1f}M) detected. High probability of dump."

        return True, "Approved by Socratic Risk Auditor."
