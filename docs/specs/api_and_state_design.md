# Specification: API & LangGraph State Machine Architecture

## 1. LangGraph State Machine Specification (`CryptoIntelState`)

```python
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class AgentDossier(TypedDict):
    agent_name: str
    assessment: str
    risk_score: float
    key_findings: List[str]
    timestamp: datetime

class CryptoIntelState(TypedDict):
    # Ingestion & Deterministic Inputs
    symbol: str
    timestamp: datetime
    raw_quant_signals: Dict[str, Any]       # Validated DeterministicSignals dict
    
    # User Context (Optional trade proposal)
    proposed_action: Optional[str]          # e.g., "LONG_BTC_5X", "DCA_BUY_SPOT"
    proposed_entry_price: Optional[float]
    
    # Multi-Agent Outputs
    macro_dossier: Optional[AgentDossier]
    whale_dossier: Optional[AgentDossier]
    derivatives_dossier: Optional[AgentDossier]
    
    # Socratic Refutation & Verdict
    socratic_verdict: Optional[Dict[str, Any]] # Validated SocraticEvaluationResult dict
    fatal_questions: List[str]
    worst_case_invalidation: float
    fomo_index: float
    
    # Execution Metadata
    errors: List[str]
    trace_id: str
```

### Graph Lifecycle & Transitions
1. `node_supervisor`: Ingests and validates inputs $\rightarrow$ Routes in parallel to `[node_macro, node_whale, node_derivatives]`.
2. `fan_in_barrier`: Waits for all 3 analytical dossiers to complete.
3. `node_socratic`: Synthesizes dossiers + challenges the trade idea $\rightarrow$ Emits 3 Fatal Questions and FOMO index.
4. `node_synthesis`: Final decision formatting and persistence $\rightarrow$ `END`.

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
