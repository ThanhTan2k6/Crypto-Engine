"""
FRED (Federal Reserve Economic Data) Client for CryptoIntel-Engine.
Ingests Federal Funds Rate (DFF), CPI (CPIAUCSL), US 10Y Yield (DGS10),
10Y-2Y Spread (T10Y2Y), and DXY Trade-Weighted Dollar Index (DTWEXBGS).
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


class FredMacroClient:
    """Client for querying Federal Reserve Macro Economic Series."""

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 6.0) -> None:
        self.api_key = api_key or os.getenv("FRED_API_KEY", "")
        self.timeout = timeout_seconds

    async def get_latest_observation(self, series_id: str) -> tuple[float, str]:
        """Fetch the most recent valid numeric observation and provenance for a given series."""
        if not self.api_key or self.api_key == "your_fred_api_key_here":
            logger.warning("FRED_API_KEY not configured. Returning offline baseline for %s.", series_id)
            return self._get_offline_fallback(series_id), "OFFLINE_DEMO_BASELINE"

        params: dict[str, str | int] = {
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
                        return float(val), "FRED_API"
                return self._get_offline_fallback(series_id), "OFFLINE_FALLBACK"
            except (httpx.HTTPError, ValueError) as e:
                logger.error("Failed to fetch FRED series %s: %s. Using fallback.", series_id, e)
                return self._get_offline_fallback(series_id), "OFFLINE_FALLBACK"

    async def get_cpi_yoy(self) -> tuple[float, str]:
        """Fetch CPI observations and calculate year-over-year inflation percentage change."""
        if not self.api_key or self.api_key == "your_fred_api_key_here":
            return 3.1, "OFFLINE_DEMO_BASELINE"

        params: dict[str, str | int] = {
            "series_id": "CPIAUCSL",
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 15,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(FRED_BASE_URL, params=params)
                resp.raise_for_status()
                observations = [
                    float(obs["value"])
                    for obs in resp.json().get("observations", [])
                    if obs.get("value") and obs["value"] != "."
                ]
                if len(observations) >= 13:
                    cpi_now = observations[0]
                    cpi_year_ago = observations[12]
                    yoy = ((cpi_now - cpi_year_ago) / cpi_year_ago) * 100.0
                    return round(float(yoy), 2), "FRED_API"
                return 3.1, "OFFLINE_FALLBACK"
            except (httpx.HTTPError, ValueError) as e:
                logger.error("Failed to compute CPI YoY from FRED: %s", e)
                return 3.1, "OFFLINE_FALLBACK"

    async def get_macro_snapshot(self) -> dict[str, Any]:
        """Fetch complete macroeconomic telemetry with explicit data provenance."""
        fed_funds, prov_ff = await self.get_latest_observation("DFF")
        cpi_yoy, prov_cpi = await self.get_cpi_yoy()
        yield_10y, prov_10y = await self.get_latest_observation("DGS10")
        yield_spread, prov_spread = await self.get_latest_observation("T10Y2Y")
        dxy, prov_dxy = await self.get_latest_observation("DTWEXBGS")

        is_offline = any(
            p != "FRED_API" for p in [prov_ff, prov_cpi, prov_10y, prov_spread, prov_dxy]
        )

        return {
            "timestamp": datetime.now(UTC),
            "fed_funds_rate": fed_funds,
            "cpi_yoy": cpi_yoy,
            "dxy_index": dxy,
            "yield_10y": yield_10y,
            "yield_spread_10y_2y": yield_spread,
            "yield_curve_inverted": yield_spread < 0.0,
            "cme_rate_cut_prob_next_fomc": 0.25,
            "is_offline_baseline": is_offline,
            "provenance": {
                "fed_funds": prov_ff,
                "cpi_yoy": prov_cpi,
                "yield_10y": prov_10y,
                "yield_spread": prov_spread,
                "dxy": prov_dxy,
            },
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
