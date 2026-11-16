# Specification 01: Pydantic v2 Data Contracts

## 1. Overview
All data flowing between the Ingestion Layer, Deterministic Quant Layer, and LangGraph Multi-Agent Layer must strictly adhere to the following Pydantic v2 schemas.

---

## 2. Core Schemas

```python
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class MacroRegime(str, Enum):
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    STAGFLATION_UNCERTAIN = "STAGFLATION_UNCERTAIN"

class WhaleSentiment(str, Enum):
    ACCUMULATION = "ACCUMULATION"
    DISTRIBUTION = "DISTRIBUTION"
    NEUTRAL = "NEUTRAL"

class MarketMetrics(BaseModel):
    model_config = ConfigDict(strict=True)

    symbol: str = Field(..., description="Trading pair, e.g., BTCUSDT")
    timestamp: datetime
    current_price: float = Field(..., gt=0.0)
    volume_24h_usd: float = Field(..., ge=0.0)
    volume_zscore_20d: float = Field(..., description="Z-score vs 20-day moving average volume")
    open_interest_usd: float = Field(..., ge=0.0)
    oi_change_24h_pct: float
    current_funding_rate: float
    annualized_funding_rate: float
    long_short_ratio: float = Field(..., gt=0.0)
    derivatives_risk_level: str = Field(..., description="LOW, ELEVATED, EXTREME_LIQUIDATION_RISK")

class MacroMetrics(BaseModel):
    model_config = ConfigDict(strict=True)

    timestamp: datetime
    fed_funds_rate: float = Field(..., ge=0.0)
    cpi_yoy: float
    dxy_index: float = Field(..., gt=0.0)
    yield_10y: float
    yield_curve_inverted: bool
    next_fomc_rate_cut_prob: float = Field(..., ge=0.0, le=1.0)
    regime: MacroRegime
    macro_score: float = Field(..., ge=-10.0, le=10.0, description="Normalized score: <-3 Risk-off, >+3 Risk-on")

class WhaleFlowMetrics(BaseModel):
    model_config = ConfigDict(strict=True)

    symbol: str
    timestamp: datetime
    exchange_netflow_24h_usd: float = Field(..., description="Positive: Inflow (Dump risk), Negative: Outflow (Accumulation)")
    netflow_zscore_30d: float
    whale_transfers_count_1m_plus: int = Field(..., ge=0)
    exchange_reserve_trend: str = Field(..., description="DEPLETING, STABLE, INFLATING")
    stablecoin_exchange_inflow_24h_usd: float = Field(..., ge=0.0)
    whale_sentiment: WhaleSentiment

class DeterministicSignals(BaseModel):
    model_config = ConfigDict(strict=True)

    symbol: str
    timestamp: datetime
    market: MarketMetrics
    macro: MacroMetrics
    whale: WhaleFlowMetrics
    spot_accumulation_score: float = Field(..., ge=0.0, le=100.0)
    swing_trend_score: float = Field(..., ge=0.0, le=100.0)
    hard_red_flags: List[str] = Field(default_factory=list)

class SocraticEvaluationResult(BaseModel):
    model_config = ConfigDict(strict=True)

    fomo_index: float = Field(..., ge=0.0, le=100.0, description="100 = Peak irrational euphoria")
    fatal_questions: List[str] = Field(..., min_length=3, max_length=3)
    worst_case_invalidation_price: float = Field(..., gt=0.0)
    thesis_flaws: List[str]
    verdict: str = Field(..., description="PROCEED_WITH_CAUTION, SCALE_IN_SPOT, REJECT_SETUP_TOO_RISKY")
    recommended_position_sizing_pct: float = Field(..., ge=0.0, le=100.0)
```
