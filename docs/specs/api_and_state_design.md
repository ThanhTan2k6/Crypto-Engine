# Specification: API & LangGraph State Machine Architecture

## 1. LangGraph State Machine Specification (`CryptoIntelState`)

```python
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class SpecialistDossier(TypedDict):
    agent_id: str
    verdict: str
    confidence_score: float
    risk_level: str
    key_observations: List[str]
    critical_vulnerabilities: List[str]
    timestamp: datetime

class CryptoIntelState(TypedDict):
    # Immutable Quant Ingestion Contracts
    symbol: str
    timestamp: datetime
    execution_mode: str               # "MODE_SPOT", "MODE_FUTURES", or "DUAL_AUDIT"
    
    # Pre-calculated Quant Schemas (from src/engine/)
    spot_valuation_data: Optional[Dict[str, Any]]    # SpotCycleValuationSchema
    futures_squeeze_data: Optional[Dict[str, Any]]   # FuturesSqueezeSchema
    etf_flow_data: Optional[Dict[str, Any]]          # ETFNetflowSchema
    whale_flow_data: Optional[Dict[str, Any]]        # WhaleFlowSchema
    token_vesting_data: Optional[Dict[str, Any]]     # TokenVestingSchema
    
    # User Trade Context
    proposed_action: Optional[str]                   # e.g., "LONG_BTC_5X", "DCA_BUY_SPOT"
    proposed_entry: Optional[float]
    time_horizon_days: int
    
    # Parallel Specialist Nodes Output
    spot_dossier: Optional[SpecialistDossier]
    futures_dossier: Optional[SpecialistDossier]
    whale_etf_dossier: Optional[SpecialistDossier]
    
    # Socratic Devil's Advocate Inquisitor
    fomo_index: float
    fatal_socratic_questions: List[str]             # Exactly 3 Fatal Questions
    worst_case_invalidation_price: float
    thesis_refutations: List[str]
    anti_fomo_verdict: str
    
    # Delivery Payloads & Metadata
    investment_memo: Optional[Dict[str, Any]]
    telegram_alert_payload: Optional[Dict[str, Any]]
    errors: List[str]
    trace_id: str
```

### Graph Lifecycle & Transitions
1. `node_supervisor`: Ingests and validates inputs $\rightarrow$ Routes in parallel to `[node_spot_specialist, node_futures_specialist, node_whale_specialist]`.
2. `fan_in_barrier`: Waits for all 3 analytical specialist dossiers to complete.
3. `node_socratic`: Synthesizes dossiers + challenges the trade idea $\rightarrow$ Emits 3 Fatal Questions and FOMO index.
4. `node_synthesis`: Final decision formatting, alert persistence $\rightarrow$ `END`.

---

## 2. API Endpoints Specification (FastAPI)

### REST Endpoints:
- `POST /api/v1/analyze`:
  - **Payload**: `{ "symbol": "BTCUSDT", "proposed_action": "LONG", "target_leverage": 3 }`
  - **Response**: Full `CryptoIntelState` with Socratic refutations and 3 Fatal Questions.
- `GET /api/v1/metrics/realtime/{symbol}`:
  - **Response**: Latest validated `DeterministicSignals` (Price, OI, Funding Rate, Netflow Z-score).
- `GET /api/v1/accounting/portfolio/tt200`:
  - **Response**: TT 200 valuation, balance sheet impairment provisions, and realized/unrealized PnL.

### WebSocket Streaming Endpoints:
- `ws://localhost:8000/ws/v1/stream/{symbol}`:
  - Real-time ticker stream broadcasting 1-second price, orderbook pressure, and funding rate anomalies.
