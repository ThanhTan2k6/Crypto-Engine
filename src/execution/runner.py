"""
Standalone Headless Runner for CryptoIntel-Engine Trading Bot.
Can run 24/7 on any Cloud Server, VPS, Docker container, or Scheduled Task.
Continuously monitors 1 to N symbols (e.g., BTC, ETH, SOL), executes paper/live orders,
triggers TP/SL, and persists state to disk.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import UTC, datetime
from typing import Any

import httpx

from src.engine.core_quant import CoreQuantEngine, get_symbol_market_profile
from src.execution.bot_coordinator import trading_bot_coordinator
from src.execution.schemas import BotMode
from src.ingestion.binance_client import BinancePublicClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("HeadlessBotRunner")


async def run_single_tick_for_symbols(
    symbols: list[str],
    quant_engine: CoreQuantEngine,
    client: BinancePublicClient,
) -> dict[str, Any]:
    """Execute evaluation tick across all target symbols."""
    results: dict[str, Any] = {}

    for symbol in symbols:
        try:
            sym_upper = symbol.upper().strip()
            ticker = await client.get_futures_ticker_24h(sym_upper)
            funding = await client.get_funding_rate(sym_upper)
            depth = await client.get_orderbook_depth(sym_upper, limit=20)

            current_price = float(ticker["last_price"])
            profile = get_symbol_market_profile(sym_upper)

            # Build quant audit payload
            quant_audit = quant_engine.run_full_quant_audit(
                symbol=sym_upper,
                current_price=current_price,
                market_cap=profile.get("market_cap", 1_000_000_000.0),
                realized_cap=profile.get("realized_cap", 500_000_000.0),
                std_market_cap=profile.get("std_market_cap", 200_000_000.0),
                sma_200d=profile.get("sma_200d", current_price * 0.95),
                sma_200w=profile.get("sma_200w", current_price * 0.70),
                sma_111d=profile.get("sma_111d", current_price * 0.98),
                sma_350d=profile.get("sma_350d", current_price * 0.90),
                open_interest_usd=profile.get("open_interest_usd", 1_000_000_000.0),
                oi_24h_ago=profile.get("oi_24h_ago", 950_000_000.0),
                funding_rate_8h=funding.get("funding_rate_8h", 0.0001),
                bids=depth.get("bids", []),
                asks=depth.get("asks", []),
                high_24h=ticker.get("high_price_24h", current_price * 1.02),
                low_24h=ticker.get("low_price_24h", current_price * 0.98),
            )

            # Audit state check for Anti-FOMO traffic light
            audit_state = {
                "anti_fomo_verdict": "SCALE_IN_SPOT" if current_price < profile.get("sma_200d", current_price) else "PROCEED_WITH_CAUTION",
                "fomo_index": 35.0,
            }

            tick_res = await trading_bot_coordinator.evaluate_tick(
                symbol=sym_upper,
                current_price=current_price,
                quant_audit=quant_audit,
                audit_state=audit_state,
            )
            results[sym_upper] = {
                "price": current_price,
                "action": tick_res.get("action"),
                "new_orders": len(tick_res.get("executed_orders", [])),
                "closed": tick_res.get("closed_trades_count", 0),
            }

        except (httpx.HTTPError, ValueError, KeyError, OSError) as e:
            logger.error("Error evaluating symbol %s: %s", symbol, e)
            results[symbol] = {"error": str(e)}

    return results


async def main_loop(
    symbols: list[str],
    interval_seconds: int = 60,
    max_ticks: int | None = None,
    mode: str = "PAPER_TRADING",
) -> None:
    """Run headless async trading loop."""
    logger.info("Initializing Headless Bot Runner...")
    logger.info("Tracking Symbols: %s | Poll Interval: %ds | Mode: %s", symbols, interval_seconds, mode)

    quant_engine = CoreQuantEngine()
    binance_client = BinancePublicClient()

    bot_mode = BotMode.LIVE_BINANCE if mode == "LIVE_BINANCE" else BotMode.PAPER_TRADING
    trading_bot_coordinator.start(mode=bot_mode)

    tick_count = 0
    try:
        while True:
            tick_count += 1
            now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

            results = await run_single_tick_for_symbols(
                symbols=symbols,
                quant_engine=quant_engine,
                client=binance_client,
            )

            stats = trading_bot_coordinator.get_stats()
            active_pos = len(trading_bot_coordinator.get_active_positions())

            summary_tokens = [f"{sym}: ${data.get('price', 0):,.2f}" for sym, data in results.items() if "price" in data]
            price_summary = " | ".join(summary_tokens)

            logger.info(
                "[%s] Tick #%d | %s | Active: %d | Closed: %d | WR: %.1f%% | PF: %.2f | Balance: $%.2f",
                now_str,
                tick_count,
                price_summary,
                active_pos,
                stats.total_trades,
                stats.win_rate_pct,
                stats.profit_factor,
                stats.current_balance_usd,
            )

            if max_ticks and tick_count >= max_ticks:
                logger.info("Reached maximum requested ticks (%d). Terminating runner cleanly.", max_ticks)
                break

            await asyncio.sleep(interval_seconds)

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Termination signal received. Stopping trading bot coordinator...")
        trading_bot_coordinator.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Headless 24/7 Trading Bot Runner")
    parser.add_argument(
        "--symbols",
        type=str,
        default="BTCUSDT,ETHUSDT,SOLUSDT",
        help="Comma-separated symbols to trade (e.g. BTCUSDT,ETHUSDT,SOLUSDT)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling and tick evaluation interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=None,
        help="Maximum ticks to run before exiting (default: infinite)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="PAPER_TRADING",
        choices=["PAPER_TRADING", "LIVE_BINANCE"],
        help="Execution mode (PAPER_TRADING or LIVE_BINANCE)",
    )

    args = parser.parse_args()
    symbol_list = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    asyncio.run(
        main_loop(
            symbols=symbol_list,
            interval_seconds=args.interval,
            max_ticks=args.ticks,
            mode=args.mode,
        )
    )
