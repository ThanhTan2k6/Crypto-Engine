"""
Deterministic Quant Engine: Mode Futures (Leverage, Squeeze & Liquidation Risk).
STRICT INVARIANT: PURE PYTHON / NUMPY / PANDAS ONLY. ZERO LLM IMPORTS ALLOWED.
Calculates Annualized Funding APR, FRSI, OI Divergence, Orderbook Imbalance (OBIR), Liquidation Pockets.
"""

from datetime import UTC, datetime

from src.ingestion.schemas import FuturesRiskLevel, FuturesSqueezeSchema


def _format_price_val(val: float) -> float:
    """Format price ensuring sub-cent precision (>0) is preserved."""
    if val <= 0.0:
        return 0.0
    if val < 0.01:
        return round(val, 8)
    return round(val, 2)


class FuturesRiskEngine:
    """Deterministic risk engine for perpetual futures leverage crowding and squeeze detection."""

    @staticmethod
    def annualize_funding_rate(funding_rate_8h: float) -> float:
        """
        Convert 8-hour funding rate into Annualized Percentage Rate (APR %).
        Formula: Funding_Rate * 3 * 365 * 100%
        """
        return round(float(funding_rate_8h * 3.0 * 365.0 * 100.0), 2)

    @staticmethod
    def calculate_frsi(annualized_funding_rate: float) -> float:
        """
        Funding Rate Squeeze Index (FRSI) normalized to [0.0, 100.0].
        - Baseline 0% APR -> FRSI 50.0
        - High positive funding (e.g. +100% APR) -> FRSI 100.0 (Extreme Long Squeeze Risk)
        - High negative funding (e.g. -100% APR) -> FRSI 0.0 (Extreme Short Squeeze Risk)
        """
        scaled = (annualized_funding_rate / 100.0) * 50.0 + 50.0
        clipped = max(0.0, min(100.0, scaled))
        return round(float(clipped), 1)

    @staticmethod
    def calculate_oi_change_pct(current_oi: float, oi_24h_ago: float) -> float:
        """Calculate 24h percentage change in Open Interest."""
        if oi_24h_ago <= 0.0:
            return 0.0
        return round(float(((current_oi - oi_24h_ago) / oi_24h_ago) * 100.0), 2)

    @staticmethod
    def calculate_orderbook_imbalance_ratio(
        bids: list[list[float]], asks: list[list[float]], current_price: float | None = None
    ) -> float:
        """
        Calculate Orderbook Imbalance Ratio (OBIR) within ±2% depth:
        OBIR = sum(Bid_Volume) / (sum(Bid_Volume) + sum(Ask_Volume))
        - OBIR < 0.35: Thin bid depth; high vulnerability to downside stop sweeps.
        - OBIR > 0.65: Bid heavy; strong absorption.
        """
        if current_price is not None and current_price > 0.0:
            lower = current_price * 0.98
            upper = current_price * 1.02
            filtered_bids = [q for p, q in bids if p >= lower]
            filtered_asks = [q for p, q in asks if p <= upper]
        else:
            filtered_bids = [q for _, q in bids] if bids else []
            filtered_asks = [q for _, q in asks] if asks else []

        total_bid_vol = sum(filtered_bids)
        total_ask_vol = sum(filtered_asks)
        total_vol = total_bid_vol + total_ask_vol
        if total_vol <= 0.0:
            return 0.5
        return round(float(total_bid_vol / total_vol), 2)

    @staticmethod
    def classify_futures_risk(
        frsi_score: float, oi_change_pct: float, obir: float
    ) -> FuturesRiskLevel:
        """Classify directional leverage risk level."""
        if frsi_score >= 85.0:
            return FuturesRiskLevel.EXTREME_LONG_LIQUIDATION_RISK
        elif frsi_score <= 20.0:
            return FuturesRiskLevel.EXTREME_SHORT_SQUEEZE_RISK
        elif frsi_score >= 70.0 or oi_change_pct >= 20.0 or obir < 0.30:
            return FuturesRiskLevel.ELEVATED
        else:
            return FuturesRiskLevel.LOW

    @staticmethod
    def estimate_liquidation_pockets(
        current_price: float, high_24h: float, low_24h: float
    ) -> tuple[float, float]:
        """
        Identify estimated stop-loss & high-leverage liquidation clusters:
        - Liquidation Pocket Above: 1.5% above 24h High (Short stop hunt zone)
        - Liquidation Pocket Below: 2.0% below 24h Low (Long stop hunt zone)
        """
        above = high_24h * 1.015 if high_24h > current_price else current_price * 1.015
        below = low_24h * 0.98 if low_24h < current_price else current_price * 0.98
        return _format_price_val(above), _format_price_val(below)

    def evaluate(
        self,
        symbol: str,
        current_price: float,
        open_interest_usd: float,
        oi_24h_ago: float,
        funding_rate_8h: float,
        long_short_ratio: float,
        bids: list[list[float]],
        asks: list[list[float]],
        high_24h: float,
        low_24h: float,
        timestamp: datetime | None = None,
    ) -> FuturesSqueezeSchema:
        """Execute full deterministic futures squeeze and liquidation risk evaluation."""
        ts = timestamp or datetime.now(UTC)
        funding_apr = self.annualize_funding_rate(funding_rate_8h)
        frsi = self.calculate_frsi(funding_apr)
        oi_change = self.calculate_oi_change_pct(open_interest_usd, oi_24h_ago)
        obir = self.calculate_orderbook_imbalance_ratio(bids, asks, current_price=current_price)
        risk_level = self.classify_futures_risk(frsi, oi_change, obir)
        liq_above, liq_below = self.estimate_liquidation_pockets(current_price, high_24h, low_24h)

        return FuturesSqueezeSchema(
            symbol=symbol.upper(),
            timestamp=ts,
            current_price=float(current_price),
            open_interest_usd=float(open_interest_usd),
            oi_change_24h_pct=float(oi_change),
            current_funding_rate=float(funding_rate_8h),
            annualized_funding_rate=float(funding_apr),
            frsi_score=float(frsi),
            long_short_ratio=float(round(long_short_ratio, 2)),
            orderbook_imbalance_ratio=float(obir),
            futures_risk_level=risk_level,
            liquidation_pocket_above=float(liq_above),
            liquidation_pocket_below=float(liq_below),
        )
