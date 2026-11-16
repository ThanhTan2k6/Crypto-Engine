"""
Deterministic Quant Engine: Whale Netflows, Tether Minting, Spot ETF & Token Vesting.
STRICT INVARIANT: PURE PYTHON / NUMPY / PANDAS ONLY. ZERO LLM IMPORTS ALLOWED.
Calculates CNAI, Netflow Z-score, Tether Velocity (TTMV), ETF Momentum (EIMI), and Vesting Cliff Risk.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np

from src.ingestion.schemas import (
    WhaleFlowSchema,
    ETFNetflowSchema,
    TokenVestingSchema,
)


class WhaleFlowEngine:
    """Deterministic engine for institutional flows, whale accumulation/distribution, and vesting dilution."""

    @staticmethod
    def calculate_netflow_zscore(
        netflow_24h_usd: float, mean_netflow_30d: float, std_netflow_30d: float
    ) -> float:
        """Calculate 30-day lookback Z-score for exchange netflows."""
        if std_netflow_30d <= 0.0:
            return 0.0
        return round(float((netflow_24h_usd - mean_netflow_30d) / std_netflow_30d), 2)

    @staticmethod
    def calculate_cnai(netflow_zscore: float) -> float:
        """
        CEX Netflow Accumulation Index (CNAI) normalized to [0.0, 100.0].
        Inverted logic: High negative netflow (outflow to cold wallet) yields high CNAI (Accumulation).
        Formula: clip(50.0 - (Z * 15.0), 0.0, 100.0)
        """
        scaled = 50.0 - (netflow_zscore * 15.0)
        clipped = max(0.0, min(100.0, scaled))
        return round(float(clipped), 1)

    @staticmethod
    def classify_whale_sentiment(cnai_score: float) -> str:
        """Classify whale behavior from CNAI score."""
        if cnai_score >= 70.0:
            return "ACCUMULATION"
        elif cnai_score <= 35.0:
            return "DISTRIBUTION"
        else:
            return "NEUTRAL"

    @staticmethod
    def calculate_etf_momentum_index(
        net_inflows_5d_usd: float, avg_5d_spot_volume_usd: float
    ) -> float:
        """
        ETF Institutional Momentum Index (EIMI):
        Ratio of 5-day net ETF inflows relative to global spot volume.
        """
        if avg_5d_spot_volume_usd <= 0.0:
            return 0.0
        return round(float((net_inflows_5d_usd / avg_5d_spot_volume_usd) * 100.0), 2)

    def evaluate_whale_flow(
        self,
        symbol: str,
        inflow_24h_usd: float,
        outflow_24h_usd: float,
        mean_30d: float,
        std_30d: float,
        tether_mint_7d_usd: float,
        whale_transfers_count_1m_plus: int,
        timestamp: datetime | None = None,
    ) -> WhaleFlowSchema:
        """Evaluate whale exchange netflows and stablecoin velocity."""
        ts = timestamp or datetime.now(timezone.utc)
        netflow = float(inflow_24h_usd - outflow_24h_usd)
        zscore = self.calculate_netflow_zscore(netflow, mean_30d, std_30d)
        cnai = self.calculate_cnai(zscore)
        sentiment = self.classify_whale_sentiment(cnai)

        red_flags: List[str] = []
        if zscore >= 2.0:
            red_flags.append("MASSIVE_CEX_INFLOW_ALERT")
        if whale_transfers_count_1m_plus >= 10 and netflow > 0:
            red_flags.append("ELEVATED_WHALE_DISTRIBUTION_FREQUENCY")

        return WhaleFlowSchema(
            symbol=symbol.upper(),
            timestamp=ts,
            exchange_inflow_24h_usd=float(inflow_24h_usd),
            exchange_outflow_24h_usd=float(outflow_24h_usd),
            netflow_24h_usd=float(netflow),
            cnai_score=float(cnai),
            tether_mint_7d_usd=float(tether_mint_7d_usd),
            whale_transfers_count_1m_plus=int(whale_transfers_count_1m_plus),
            whale_sentiment=sentiment,
            hard_red_flags=red_flags,
        )

    def evaluate_etf_flow(
        self,
        daily_net_inflow_usd: float,
        ibit_inflow_usd: float,
        fbtc_inflow_usd: float,
        cumulative_5d_netflow_usd: float,
        avg_5d_spot_volume_usd: float,
        timestamp: datetime | None = None,
    ) -> ETFNetflowSchema:
        """Evaluate institutional ETF accumulation or distribution."""
        ts = timestamp or datetime.now(timezone.utc)
        eimi = self.calculate_etf_momentum_index(cumulative_5d_netflow_usd, avg_5d_spot_volume_usd)
        bias = "ACCUMULATION" if cumulative_5d_netflow_usd > 50000000.0 else ("DISTRIBUTION" if cumulative_5d_netflow_usd < -50000000.0 else "NEUTRAL")

        return ETFNetflowSchema(
            timestamp=ts,
            daily_net_inflow_usd=float(daily_net_inflow_usd),
            ibit_inflow_usd=float(ibit_inflow_usd),
            fbtc_inflow_usd=float(fbtc_inflow_usd),
            cumulative_5d_netflow_usd=float(cumulative_5d_netflow_usd),
            etf_momentum_index=float(eimi),
            institutional_bias=bias,
        )

    def evaluate_token_vesting(
        self,
        symbol: str,
        circulating_supply: float,
        total_supply: float,
        market_cap_usd: float,
        fdv_usd: float,
        next_unlock_date: Optional[datetime] = None,
        next_unlock_amount_usd: float = 0.0,
    ) -> TokenVestingSchema:
        """Evaluate token dilution risk from vesting cliffs and low float."""
        circ_pct = (circulating_supply / total_supply * 100.0) if total_supply > 0 else 100.0
        fdv_mc = (fdv_usd / market_cap_usd) if market_cap_usd > 0 else 1.0
        unlock_pct = (next_unlock_amount_usd / market_cap_usd * 100.0) if market_cap_usd > 0 else 0.0

        if circ_pct < 15.0 or fdv_mc > 5.0 or unlock_pct >= 5.0:
            dilution_risk = "HIGH_PREDATORY_UNLOCK"
        elif circ_pct < 40.0 or fdv_mc > 2.5:
            dilution_risk = "MODERATE"
        else:
            dilution_risk = "LOW"

        return TokenVestingSchema(
            symbol=symbol.upper(),
            circulating_supply=float(circulating_supply),
            total_supply=float(total_supply),
            circulating_pct=round(float(circ_pct), 2),
            fdv_usd=float(fdv_usd),
            market_cap_usd=float(market_cap_usd),
            fdv_mc_ratio=round(float(fdv_mc), 2),
            next_unlock_date=next_unlock_date,
            next_unlock_amount_usd=float(next_unlock_amount_usd),
            next_unlock_pct_of_circulating=round(float(unlock_pct), 2),
            dilution_risk=dilution_risk,
        )
