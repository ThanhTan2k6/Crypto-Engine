"""
Deterministic Quant Engine: Mode Futures (Leverage, Squeeze & Liquidation Risk).
STRICT INVARIANT: PURE PYTHON / NUMPY / PANDAS ONLY. ZERO LLM IMPORTS ALLOWED.
Calculates Annualized Funding APR, FRSI, OI Divergence, Orderbook Imbalance (OBIR), Liquidation Pockets.
"""

from typing import Tuple, List, Dict, Any
from datetime import datetime, timezone
import numpy as np

from src.ingestion.schemas import FuturesSqueezeSchema, FuturesRiskLevel


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
        bids: List[List[float]], asks: List[List[float]]
    ) -> float:
        """
        Calculate Orderbook Imbalance Ratio (OBIR) within depth:
        OBIR = sum(Bid_Volume) / (sum(Bid_Volume) + sum(Ask_Volume))
        - OBIR < 0.35: Thin bid depth; high vulnerability to downside stop sweeps.
        - OBIR > 0.65: Bid heavy; strong absorption.
        """
        total_bid_vol = sum(q for _, q in bids) if bids else 0.0
        total_ask_vol = sum(q for _, q in asks) if asks else 0.0
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
    ) -> Tuple[float, float]:
        """
        Identify estimated stop-loss & high-leverage liquidation clusters:
        - Liquidation Pocket Above: 1.5% above 24h High (Short stop hunt zone)
        - Liquidation Pocket Below: 2.0% below 24h Low (Long stop hunt zone)
        """
        pocket_above = round(high_24h * 1.015 if high_24h > current_price else current_price * 1.015, 2)
        pocket_below = round(low_24h * 0.98 if low_24h < current_price else current_price * 0.98, 2)
        return pocket_above, pocket_below

    def evaluate(
        self,
        symbol: str,
        current_price: float,
        open_interest_usd: float,
        oi_24h_ago: float,
        funding_rate_8h: float,
        long_short_ratio: float,
        bids: List[List[float]],
        asks: List[List[float]],
        high_24h: float,
        low_24h: float,
        timestamp: datetime | None = None,
    ) -> FuturesSqueezeSchema:
        """Execute full deterministic futures squeeze and liquidation risk evaluation."""
        ts = timestamp or datetime.now(timezone.utc)
        funding_apr = self.annualize_funding_rate(funding_rate_8h)
        frsi = self.calculate_frsi(funding_apr)
        oi_change = self.calculate_oi_change_pct(open_interest_usd, oi_24h_ago)
        obir = self.calculate_orderbook_imbalance_ratio(bids, asks)
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
