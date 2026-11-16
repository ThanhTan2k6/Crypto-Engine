"""
Unified Deterministic Quantitative Core for CryptoIntel-Engine.
STRICT INVARIANT: PURE PYTHON / NUMPY / PANDAS ONLY. ZERO LLM IMPORTS ALLOWED.
Assembles complete deterministic quantitative intelligence under < 0.5s SLA.
"""

import time
from datetime import UTC, datetime
from typing import Any

from src.engine.futures_engine import FuturesRiskEngine
from src.engine.spot_engine import SpotCycleEngine
from src.engine.whale_engine import WhaleFlowEngine


class CoreQuantEngine:
    """Master Deterministic Quantitative Coordinator."""

    def __init__(self) -> None:
        self.spot_engine = SpotCycleEngine()
        self.futures_engine = FuturesRiskEngine()
        self.whale_engine = WhaleFlowEngine()

    def run_full_quant_audit(
        self,
        symbol: str,
        current_price: float,
        # Spot params
        market_cap: float,
        realized_cap: float,
        std_market_cap: float,
        sma_200d: float,
        sma_200w: float,
        sma_111d: float,
        sma_350d: float,
        # Futures params
        open_interest_usd: float,
        oi_24h_ago: float,
        funding_rate_8h: float,
        long_short_ratio: float,
        bids: list,
        asks: list,
        high_24h: float,
        low_24h: float,
        # Whale params
        inflow_24h_usd: float,
        outflow_24h_usd: float,
        mean_netflow_30d: float,
        std_netflow_30d: float,
        tether_mint_7d_usd: float,
        whale_transfers_count: int,
        # ETF params
        daily_etf_inflow_usd: float,
        ibit_inflow_usd: float,
        fbtc_inflow_usd: float,
        cumulative_5d_etf_usd: float,
        avg_5d_spot_vol_usd: float,
        # Vesting params
        circulating_supply: float,
        total_supply: float,
        fdv_usd: float,
        next_unlock_date: datetime | None = None,
        next_unlock_amount_usd: float = 0.0,
    ) -> dict[str, Any]:
        """
        Execute complete multi-engine quant audit and enforce < 0.5s SLA.
        """
        start_time = time.perf_counter()

        spot_schema = self.spot_engine.evaluate(
            symbol=symbol,
            current_price=current_price,
            market_cap=market_cap,
            realized_cap=realized_cap,
            std_market_cap=std_market_cap,
            sma_200d=sma_200d,
            sma_200w=sma_200w,
            sma_111d=sma_111d,
            sma_350d=sma_350d,
        )

        futures_schema = self.futures_engine.evaluate(
            symbol=symbol,
            current_price=current_price,
            open_interest_usd=open_interest_usd,
            oi_24h_ago=oi_24h_ago,
            funding_rate_8h=funding_rate_8h,
            long_short_ratio=long_short_ratio,
            bids=bids,
            asks=asks,
            high_24h=high_24h,
            low_24h=low_24h,
        )

        whale_schema = self.whale_engine.evaluate_whale_flow(
            symbol=symbol,
            inflow_24h_usd=inflow_24h_usd,
            outflow_24h_usd=outflow_24h_usd,
            mean_30d=mean_netflow_30d,
            std_30d=std_netflow_30d,
            tether_mint_7d_usd=tether_mint_7d_usd,
            whale_transfers_count_1m_plus=whale_transfers_count,
        )

        etf_schema = self.whale_engine.evaluate_etf_flow(
            daily_net_inflow_usd=daily_etf_inflow_usd,
            ibit_inflow_usd=ibit_inflow_usd,
            fbtc_inflow_usd=fbtc_inflow_usd,
            cumulative_5d_netflow_usd=cumulative_5d_etf_usd,
            avg_5d_spot_volume_usd=avg_5d_spot_vol_usd,
        )

        vesting_schema = self.whale_engine.evaluate_token_vesting(
            symbol=symbol,
            circulating_supply=circulating_supply,
            total_supply=total_supply,
            market_cap_usd=market_cap,
            fdv_usd=fdv_usd,
            next_unlock_date=next_unlock_date,
            next_unlock_amount_usd=next_unlock_amount_usd,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.now(UTC),
            "execution_latency_ms": round(elapsed_ms, 2),
            "sla_passed": elapsed_ms < 500.0,
            "spot_valuation": spot_schema,
            "futures_risk": futures_schema,
            "whale_flow": whale_schema,
            "etf_flow": etf_schema,
            "token_vesting": vesting_schema,
        }
