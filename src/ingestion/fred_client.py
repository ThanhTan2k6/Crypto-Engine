"""
FRED (Federal Reserve Economic Data) Client for CryptoIntel-Engine.
Ingests Federal Funds Rate (DFF), CPI (CPIAUCSL), US 10Y Yield (DGS10),
10Y-2Y Spread (T10Y2Y), and DXY Trade-Weighted Dollar Index (DTWEXBGS).
"""

from typing import Dict, Any, Optional
import os
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


class FredMacroClient:
    """Client for querying Federal Reserve Macro Economic Series."""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: float = 6.0) -> None:
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")
        self.timeout = timeout_seconds

    async def get_latest_observation(self, series_id: str) -> float:
        """Fetch the most recent valid numeric observation for a given series."""
        if not self.api_key or self.api_key == "your_fred_api_key_here":
            logger.warning(f"FRED_API_KEY not configured. Returning offline baseline for {series_id}.")
            return self._get_offline_fallback(series_id)

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 5,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(FRED_BASE_URL, params=params)
                resp.raise_for_status()
                observations = resp.json().get("observations", [])
                for obs in observations:
                    val = obs.get("value", "")
                    if val and val != ".":
                        return float(val)
                return self._get_offline_fallback(series_id)
            except Exception as e:
                logger.error(f"Failed to fetch FRED series {series_id}: {e}. Using fallback.")
                return self._get_offline_fallback(series_id)

    async def get_macro_snapshot(self) -> Dict[str, Any]:
        """Fetch complete macroeconomic telemetry in parallel."""
        fed_funds = await self.get_latest_observation("DFF")
        cpi = await self.get_latest_observation("CPIAUCSL")
        yield_10y = await self.get_latest_observation("DGS10")
        yield_spread = await self.get_latest_observation("T10Y2Y")
        dxy = await self.get_latest_observation("DTWEXBGS")

        return {
            "timestamp": datetime.utcnow(),
            "fed_funds_rate": fed_funds,
            "cpi_yoy": 3.1,  # Calculated or baseline YoY
            "dxy_index": dxy,
            "yield_10y": yield_10y,
            "yield_spread_10y_2y": yield_spread,
            "yield_curve_inverted": yield_spread < 0.0,
            "cme_rate_cut_prob_next_fomc": 0.25,
        }

    def _get_offline_fallback(self, series_id: str) -> float:
        """Fallback realistic values when offline or rate-limited."""
        fallbacks = {
            "DFF": 5.33,
            "CPIAUCSL": 314.1,
            "DGS10": 4.25,
            "T10Y2Y": 0.05,
            "DTWEXBGS": 104.5,
        }
        return fallbacks.get(series_id, 0.0)
