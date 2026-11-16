"""
Binance Public WebSocket & REST Client for CryptoIntel-Engine.
Requires NO API keys. Ingests Real-Time Spot & Perpetual Futures Ticker, Depth, OI, and Funding.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BINANCE_FUTURES_BASE_URL = "https://fapi.binance.com"
BINANCE_SPOT_BASE_URL = "https://api.binance.com"


class BinancePublicClient:
    """Public Async Client for Binance REST API without credentials."""

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout = timeout_seconds

    async def get_futures_ticker_24h(self, symbol: str = "BTCUSDT") -> dict[str, Any]:
        """Fetch 24h ticker price, volume, high, low from Binance Futures."""
        url = f"{BINANCE_FUTURES_BASE_URL}/fapi/v1/ticker/24hr"
        params = {"symbol": symbol.upper()}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return {
                "symbol": symbol.upper(),
                "last_price": float(data.get("lastPrice", 0.0)),
                "volume_24h_usd": float(data.get("quoteVolume", 0.0)),
                "price_change_pct_24h": float(data.get("priceChangePercent", 0.0)),
                "high_price_24h": float(data.get("highPrice", 0.0)),
                "low_price_24h": float(data.get("lowPrice", 0.0)),
                "timestamp": datetime.now(UTC),
            }

    async def get_open_interest(self, symbol: str = "BTCUSDT") -> dict[str, Any]:
        """Fetch current open interest in USD and contracts."""
        url = f"{BINANCE_FUTURES_BASE_URL}/fapi/v1/openInterest"
        params = {"symbol": symbol.upper()}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return {
                "symbol": symbol.upper(),
                "open_interest_contracts": float(data.get("openInterest", 0.0)),
                "timestamp": datetime.now(UTC),
            }

    async def get_funding_rate(self, symbol: str = "BTCUSDT") -> dict[str, Any]:
        """Fetch latest funding rate normalized to 8h equivalent and funding interval."""
        url = f"{BINANCE_FUTURES_BASE_URL}/fapi/v1/premiumIndex"
        params: dict[str, str | int] = {"symbol": symbol.upper()}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            raw_rate = float(data.get("lastFundingRate", 0.0))
            interval_hours = int(data.get("fundingIntervalHours", 8))
            rate_8h = raw_rate * (8.0 / interval_hours) if interval_hours > 0 else raw_rate
            next_funding_time = datetime.fromtimestamp(data.get("nextFundingTime", 0) / 1000.0, tz=UTC)
            return {
                "symbol": symbol.upper(),
                "funding_rate_8h": rate_8h,
                "funding_interval_hours": interval_hours,
                "funding_time": next_funding_time,
                "timestamp": datetime.now(UTC),
            }

    async def get_orderbook_depth(self, symbol: str = "BTCUSDT", limit: int = 50) -> dict[str, Any]:
        """Fetch orderbook top bids and asks to calculate orderbook depth and imbalance."""
        url = f"{BINANCE_FUTURES_BASE_URL}/fapi/v1/depth"
        params: dict[str, str | int] = {"symbol": symbol.upper(), "limit": limit}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            bids = [[float(p), float(q)] for p, q in data.get("bids", [])]
            asks = [[float(p), float(q)] for p, q in data.get("asks", [])]
            return {
                "symbol": symbol.upper(),
                "bids": bids,
                "asks": asks,
                "timestamp": datetime.now(UTC),
            }
