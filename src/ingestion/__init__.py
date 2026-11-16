"""Ingestion module for CryptoIntel-Engine."""

from src.ingestion.binance_client import BinancePublicClient
from src.ingestion.bybit_client import BybitPublicClient
from src.ingestion.fred_client import FredMacroClient
from src.ingestion.onchain_client import OnChainPublicClient
from src.ingestion.schemas import (
    AntiFomoVerdict,
    CycleRegime,
    ETFNetflowSchema,
    FuturesRiskLevel,
    FuturesSqueezeSchema,
    SocraticCritiqueSchema,
    SpotCycleValuationSchema,
    TelegramAlertPayload,
    TokenVestingSchema,
    WhaleFlowSchema,
)

__all__ = [
    "AntiFomoVerdict",
    "BinancePublicClient",
    "BybitPublicClient",
    "CycleRegime",
    "ETFNetflowSchema",
    "FredMacroClient",
    "FuturesRiskLevel",
    "FuturesSqueezeSchema",
    "OnChainPublicClient",
    "SocraticCritiqueSchema",
    "SpotCycleValuationSchema",
    "TelegramAlertPayload",
    "TokenVestingSchema",
    "WhaleFlowSchema",
]
