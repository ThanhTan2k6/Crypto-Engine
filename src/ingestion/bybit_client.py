"""
Bybit Public REST Client for CryptoIntel-Engine.
Fallback data provider requiring NO API keys. Ingests Tickers, Orderbook, and Funding.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BYBIT_BASE_URL = "https://api.bybit.com"


class BybitPublicClient:
    """Public Async Client for Bybit v5 Public Endpoints."""

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout = timeout_seconds

    async def get_linear_ticker(self, symbol: str = "BTCUSDT") -> dict[str, Any]:
        """Fetch linear perpetual ticker data from Bybit v5."""
        url = f"{BYBIT_BASE_URL}/v5/market/tickers"
        params = {"category": "linear", "symbol": symbol.upper()}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            result_list = data.get("result", {}).get("list", [])
            if not result_list:
                raise ValueError(f"No Bybit ticker returned for {symbol}")
            item = result_list[0]
            return {
                "symbol": symbol.upper(),
                "last_price": float(item.get("lastPrice", 0.0)),
                "volume_24h_usd": float(item.get("turnover24h", 0.0)),
                "open_interest_usd": float(item.get("openInterestValue", 0.0)),
                "funding_rate_8h": float(item.get("fundingRate", 0.0)),
                "timestamp": datetime.now(UTC),
            }

    async def get_orderbook(self, symbol: str = "BTCUSDT", limit: int = 50) -> dict[str, Any]:
        """Fetch orderbook depth from Bybit v5."""
        url = f"{BYBIT_BASE_URL}/v5/market/orderbook"
        params: dict[str, str | int] = {"category": "linear", "symbol": symbol.upper(), "limit": limit}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json().get("result", {})
            bids = [[float(p), float(q)] for p, q in data.get("b", [])]
            asks = [[float(p), float(q)] for p, q in data.get("a", [])]
            return {
                "symbol": symbol.upper(),
                "bids": bids,
                "asks": asks,
                "timestamp": datetime.now(UTC),
            }
