"""Ingestion module for CryptoIntel-Engine."""

from src.ingestion.schemas import (
    SpotCycleValuationSchema,
    FuturesSqueezeSchema,
    ETFNetflowSchema,
    WhaleFlowSchema,
    TokenVestingSchema,
    SocraticCritiqueSchema,
    TelegramAlertPayload,
    CycleRegime,
    FuturesRiskLevel,
    AntiFomoVerdict,
)
from src.ingestion.binance_client import BinancePublicClient
from src.ingestion.bybit_client import BybitPublicClient
from src.ingestion.fred_client import FredMacroClient
from src.ingestion.onchain_client import OnChainPublicClient

__all__ = [
    "SpotCycleValuationSchema",
    "FuturesSqueezeSchema",
    "ETFNetflowSchema",
    "WhaleFlowSchema",
    "TokenVestingSchema",
    "SocraticCritiqueSchema",
    "TelegramAlertPayload",
    "CycleRegime",
    "FuturesRiskLevel",
    "AntiFomoVerdict",
    "BinancePublicClient",
    "BybitPublicClient",
    "FredMacroClient",
    "OnChainPublicClient",
]
