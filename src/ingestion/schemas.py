"""
Data Contracts & Pydantic v2 Schema Definitions for CryptoIntel-Engine.
Implements spec_01_data_contracts.md with immutable frozen strict configurations.
Supports Dual-Engine (Mode Spot & Mode Futures), Whale Tracking, Spot ETF & Telegram alerts.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CycleRegime(str, Enum):
    CYCLE_BOTTOM_CAPITULATION = "CYCLE_BOTTOM_CAPITULATION"
    EARLY_ACCUMULATION = "EARLY_ACCUMULATION"
    MID_BULL_EXPANSION = "MID_BULL_EXPANSION"
    LATE_BULL_OVERHEATED = "LATE_BULL_OVERHEATED"
    CYCLE_TOP_EUPHORIA = "CYCLE_TOP_EUPHORIA"


class FuturesRiskLevel(str, Enum):
    LOW = "LOW"
    ELEVATED = "ELEVATED"
    EXTREME_LONG_LIQUIDATION_RISK = "EXTREME_LONG_LIQUIDATION_RISK"
    EXTREME_SHORT_SQUEEZE_RISK = "EXTREME_SHORT_SQUEEZE_RISK"


class AntiFomoVerdict(str, Enum):
    SCALE_IN_SPOT = "SCALE_IN_SPOT"
    PROCEED_WITH_CAUTION = "PROCEED_WITH_CAUTION"
    REJECT_SETUP_TOO_RISKY = "REJECT_SETUP_TOO_RISKY"


class SpotCycleValuationSchema(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str
    timestamp: datetime
    current_price: float = Field(..., gt=0.0)
    mvrv_zscore: float = Field(..., description="MVRV Z-Score indicator")
    realized_price: float = Field(..., gt=0.0)
    sma_200w: float = Field(..., gt=0.0, description="200-Week Simple Moving Average")
    mayer_multiple: float = Field(..., description="Current Price / 200-Day SMA")
    pi_cycle_top_triggered: bool
    cycle_regime: CycleRegime
    dca_zone_conservative: float = Field(..., gt=0.0)
    dca_zone_moderate: float = Field(..., gt=0.0)
    dca_zone_aggressive: float = Field(..., gt=0.0)
    take_profit_target_1: float = Field(..., gt=0.0)
    take_profit_target_2: float = Field(..., gt=0.0)
    take_profit_target_3: float = Field(..., gt=0.0)
    recommended_spot_multiplier: float = Field(..., ge=0.0, le=2.5)


class FuturesSqueezeSchema(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str
    timestamp: datetime
    current_price: float = Field(..., gt=0.0)
    open_interest_usd: float = Field(..., ge=0.0)
    oi_change_24h_pct: float
    current_funding_rate: float
    annualized_funding_rate: float
    frsi_score: float = Field(..., ge=0.0, le=100.0, description="Funding Rate Squeeze Index (0-100)")
    long_short_ratio: float = Field(..., gt=0.0)
    orderbook_imbalance_ratio: float = Field(..., ge=0.0, le=1.0, description="OBIR: Bid depth / (Bid + Ask)")
    futures_risk_level: FuturesRiskLevel
    liquidation_pocket_above: float = Field(..., gt=0.0)
    liquidation_pocket_below: float = Field(..., gt=0.0)


class ETFNetflowSchema(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    timestamp: datetime
    daily_net_inflow_usd: float = Field(..., description="Total Daily US Spot ETF Netflow")
    ibit_inflow_usd: float = Field(default=0.0, description="BlackRock IBIT Netflow")
    fbtc_inflow_usd: float = Field(default=0.0, description="Fidelity FBTC Netflow")
    cumulative_5d_netflow_usd: float
    etf_momentum_index: float = Field(..., description="EIMI indicator")
    institutional_bias: str = Field(..., description="ACCUMULATION, NEUTRAL, DISTRIBUTION")


class WhaleFlowSchema(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str
    timestamp: datetime
    exchange_inflow_24h_usd: float = Field(..., ge=0.0)
    exchange_outflow_24h_usd: float = Field(..., ge=0.0)
    netflow_24h_usd: float = Field(..., description="Inflow - Outflow")
    cnai_score: float = Field(..., ge=0.0, le=100.0, description="CEX Netflow Accumulation Index")
    tether_mint_7d_usd: float = Field(..., ge=0.0, description="USDT Treasury Minting in 7 days")
    whale_transfers_count_1m_plus: int = Field(..., ge=0)
    whale_sentiment: str = Field(..., description="ACCUMULATION, DISTRIBUTION, NEUTRAL")
    hard_red_flags: list[str] = Field(default_factory=list)


class TokenVestingSchema(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str
    circulating_supply: float = Field(..., gt=0.0)
    total_supply: float = Field(..., gt=0.0)
    circulating_pct: float = Field(..., ge=0.0, le=100.0)
    fdv_usd: float = Field(..., gt=0.0)
    market_cap_usd: float = Field(..., gt=0.0)
    fdv_mc_ratio: float = Field(..., gt=0.0)
    next_unlock_date: datetime | None = None
    next_unlock_amount_usd: float = Field(default=0.0)
    next_unlock_pct_of_circulating: float = Field(default=0.0)
    dilution_risk: str = Field(..., description="LOW, MODERATE, HIGH_PREDATORY_UNLOCK")


class SocraticCritiqueSchema(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    symbol: str
    timestamp: datetime
    fomo_index: float = Field(..., ge=0.0, le=100.0, description="100 = Peak Irrational Euphoria")
    fatal_socratic_questions: list[str] = Field(..., min_length=3, max_length=3)
    worst_case_invalidation_price: float = Field(..., gt=0.0)
    core_thesis_flaws: list[str] = Field(..., min_length=1)
    anti_fomo_verdict: AntiFomoVerdict
    max_recommended_allocation_pct: float = Field(..., ge=0.0, le=100.0)


class TelegramAlertPayload(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    alert_id: str
    timestamp: datetime
    symbol: str
    alert_type: str = Field(..., description="WHALE_DUMP, SQUEEZE_WARNING, TETHER_MINT, AUDIT_RESPONSE")
    urgency_level: str = Field(..., description="INFO, WARNING, CRITICAL_EMERGENCY")
    markdown_message: str
    action_url: str | None = None
