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
        symbol: str = "BTCUSDT",
        current_price: float = 95000.0,
        # Spot params
        market_cap: float = 1880000000000.0,
        realized_cap: float = 750000000000.0,
        std_market_cap: float = 300000000000.0,
        sma_200d: float = 68000.0,
        sma_200w: float = 48000.0,
        sma_111d: float = 72000.0,
        sma_350d: float = 65000.0,
        # Futures params
        open_interest_usd: float = 12000000000.0,
        oi_24h_ago: float = 10500000000.0,
        funding_rate_8h: float = 0.0008,
        long_short_ratio: float = 2.85,
        bids: list[list[float]] | None = None,
        asks: list[list[float]] | None = None,
        high_24h: float = 96500.0,
        low_24h: float = 93500.0,
        # Whale params
        inflow_24h_usd: float = 1200000000.0,
        outflow_24h_usd: float = 780000000.0,
        mean_netflow_30d: float = 150000000.0,
        std_netflow_30d: float = 180000000.0,
        tether_mint_7d_usd: float = 1000000000.0,
        whale_transfers_count: int = 142,
        # ETF params
        daily_etf_inflow_usd: float = 450000000.0,
        ibit_inflow_usd: float = 310000000.0,
        fbtc_inflow_usd: float = 140000000.0,
        cumulative_5d_etf_usd: float = 1850000000.0,
        avg_5d_spot_vol_usd: float = 28000000000.0,
        # Vesting params
        circulating_supply: float = 19700000.0,
        total_supply: float = 21000000.0,
        fdv_usd: float = 1995000000000.0,
        next_unlock_date: datetime | None = None,
        next_unlock_amount_usd: float = 0.0,
    ) -> dict[str, Any]:
        """
        Execute complete multi-engine quant audit and enforce < 0.5s SLA.
        """
        start_time = time.perf_counter()

        actual_bids = bids if bids is not None else [[current_price, 15.0]]
        actual_asks = asks if asks is not None else [[current_price * 1.001, 45.0]]

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
            bids=actual_bids,
            asks=actual_asks,
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
            # Convenient aliases
            "spot": spot_schema,
            "futures": futures_schema,
            "whale": whale_schema,
            "etf": etf_schema,
            "vesting": vesting_schema,
        }


def get_symbol_market_profile(symbol: str) -> dict[str, Any]:
    """Retrieve validated market profile for symbol with benchmark calibration fallback."""
    sym = symbol.upper().replace("USDT", "")
    if sym == "ETH":
        return {
            "current_price": 3400.0,
            "market_cap": 410_000_000_000.0,
            "realized_cap": 220_000_000_000.0,
            "std_market_cap": 80_000_000_000.0,
            "sma_200d": 3100.0,
            "sma_200w": 2200.0,
            "sma_111d": 3300.0,
            "sma_350d": 2900.0,
            "open_interest_usd": 4_500_000_000.0,
            "oi_24h_ago": 4_200_000_000.0,
            "circulating_supply": 120_000_000.0,
            "total_supply": 120_000_000.0,
            "fdv_usd": 410_000_000_000.0,
            "is_calibrated": True,
        }
    elif sym == "SOL":
        return {
            "current_price": 185.0,
            "market_cap": 86_000_000_000.0,
            "realized_cap": 45_000_000_000.0,
            "std_market_cap": 18_000_000_000.0,
            "sma_200d": 160.0,
            "sma_200w": 65.0,
            "sma_111d": 175.0,
            "sma_350d": 140.0,
            "open_interest_usd": 2_100_000_000.0,
            "oi_24h_ago": 1_900_000_000.0,
            "circulating_supply": 465_000_000.0,
            "total_supply": 580_000_000.0,
            "fdv_usd": 107_000_000_000.0,
            "is_calibrated": True,
        }
    elif sym == "XRP":
        return {
            "current_price": 0.95,
            "market_cap": 54_000_000_000.0,
            "realized_cap": 28_000_000_000.0,
            "std_market_cap": 12_000_000_000.0,
            "sma_200d": 0.62,
            "sma_200w": 0.52,
            "sma_111d": 0.70,
            "sma_350d": 0.58,
            "open_interest_usd": 600_000_000.0,
            "oi_24h_ago": 580_000_000.0,
            "circulating_supply": 56_800_000_000.0,
            "total_supply": 100_000_000_000.0,
            "fdv_usd": 95_000_000_000.0,
            "is_calibrated": True,
        }
    return {
        "current_price": 95000.0,
        "market_cap": 1880000000000.0,
        "realized_cap": 750000000000.0,
        "std_market_cap": 300000000000.0,
        "sma_200d": 68000.0,
        "sma_200w": 48000.0,
        "sma_111d": 72000.0,
        "sma_350d": 65000.0,
        "open_interest_usd": 12000000000.0,
        "oi_24h_ago": 10500000000.0,
        "circulating_supply": 19700000.0,
        "total_supply": 21000000.0,
        "fdv_usd": 1995000000000.0,
        "is_calibrated": sym == "BTC",
    }
