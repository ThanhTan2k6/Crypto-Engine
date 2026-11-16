"""
Supervisor Node for CryptoIntel-Engine LangGraph.
Reviews input parameters, validates schema contracts, and routes execution.
"""

import logging
from datetime import UTC, datetime

from src.agents.state import CryptoIntelState

logger = logging.getLogger(__name__)


async def supervisor_node(state: CryptoIntelState) -> dict[str, object]:
    """
    Supervisor orchestrates the audit.
    Validates that necessary quant payloads are present based on execution mode.
    """
    symbol = state.get("symbol", "BTCUSDT")
    mode = state.get("execution_mode", "DUAL_AUDIT")
    logger.info("Supervisor Node activating for symbol %s in %s mode.", symbol, mode)

    errors: list[str] = list(state.get("errors", []))

    # Validate contracts based on mode
    if mode in ["MODE_SPOT", "DUAL_AUDIT"] and not state.get("spot_valuation_data"):
        errors.append(f"Missing spot_valuation_data for {symbol}")

    if mode in ["MODE_FUTURES", "DUAL_AUDIT"] and not state.get("futures_squeeze_data"):
        errors.append(f"Missing futures_squeeze_data for {symbol}")

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "errors": errors,
    }
