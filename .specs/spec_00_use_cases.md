# Technical Specification 00: Core Use Cases & BDD Acceptance Criteria

## 1. Overview
This specification details the 5 core use cases of `CryptoIntel-Engine` using Behavior-Driven Development (BDD) conventions (Given / When / Then), end-to-end data flows, and exception handling matrices.

---

## 2. Core Use Cases

### UC-01: Real-time Multi-Source Ingestion (Binance WebSocket, FRED, ETF Netflow, Whale Alerts)
- **Primary Actor**: Automated Background Ingestion Service.
- **Goal**: Ingest multi-source market, macro, on-chain, and ETF data into immutable Pydantic v2 schemas within $< 500\text{ms}$.

#### BDD Scenarios:
```gherkin
Scenario: Ingestion of live Binance futures ticker and orderbook depth
  Given a public WebSocket connection to Binance Futures and Spot streams
  When a tick arrives with Mark Price $94,500, 8h Funding Rate 0.0007, and bid/ask depth
  Then the normalizer instantiates an immutable FuturesSqueezeSchema in < 50ms
  And calculates Annualized Funding Rate as 76.65% and OBIR orderbook ratio
  And no API keys are required.

Scenario: Ingestion of Institutional Spot ETF Netflows
  Given a public feed connection to Farside/SoSoValue ETF daily tracker
  When daily net inflow figures for BlackRock IBIT and Fidelity FBTC are published
  Then the normalizer instantiates the ETFNetflowSchema
  And updates the 5-day ETF Institutional Momentum Index (EIMI).
```

---

### UC-02: Spot Cycle Valuation Engine (Cycle Tops/Bottoms, DCA Buy & Target Sell Zones)
- **Primary Actor**: Mode Spot Quant Engine (`src/engine/spot_engine.py`).
- **Goal**: Determine macro cycle position and generate objective Accumulation and Take-Profit zones.

#### BDD Scenarios:
```gherkin
Scenario: Identification of Generational Cycle Bottom and Dynamic DCA calculation
  Given Bitcoin MVRV Z-Score is 0.08 (< 0.10)
  And current price is trading within 3% of the 200-Week Moving Average
  When the Spot Engine computes SpotCycleValuationSchema
  Then cycle_status is flagged as "CYCLE_GENERATIONAL_BOTTOM"
  And calculates 3 DCA Accumulation Zones: Conservative, Moderate, Aggressive
  And sets recommended_spot_allocation_multiplier to 1.8x.

Scenario: Detection of Cycle Top Overheated Phase
  Given Bitcoin MVRV Z-Score exceeds 4.5
  And Mayer Multiple is above 2.4
  When the Spot Engine computes valuation
  Then cycle_status is flagged as "CYCLE_OVERHEATED_DISTRIBUTION"
  And calculates 3 Take-Profit target zones
  And bans new spot allocation.
```

---

### UC-03: Futures Squeeze & Liquidation Risk Audit (Funding, OI Divergence, Orderbook)
- **Primary Actor**: Mode Futures Quant Engine (`src/engine/futures_engine.py`).
- **Goal**: Detect leverage traps, funding bleeds, and stop-loss hunt wicks without LLM involvement.

#### BDD Scenarios:
```gherkin
Scenario: Detection of Extreme Long Liquidation Squeeze
  Given the 8-hour Funding Rate exceeds +0.08% (> 87.6% APR)
  And Open Interest has increased by 16% over the last 4 hours
  And Orderbook Imbalance Ratio (OBIR) is below 0.35 (thin bid support)
  When the Futures Engine evaluates the metrics
  Then FRSI is calculated >= 88.0
  And risk_level is set to "EXTREME_LONG_LIQUIDATION_RISK"
  And liquidation_pocket_below is identified at the primary stop cluster.
```

---

### UC-04: Multi-Agent Socratic Devil's Advocate (Anti-FOMO Interrogation)
- **Primary Actor**: Socratic Devil's Advocate Agent (`src/agents/socratic_agent.py`).
- **Goal**: Interrogate the investor with 3 fatal questions, compute the FOMO Index, and identify the thesis invalidation price.

#### BDD Scenarios:
```gherkin
Scenario: Interrogation of a retail trader FOMO longing into resistance
  Given the user submits a proposed 5x Long trade at $95,000
  And the Quant Engine reports FRSI=91.0, Whale CEX Netflow=+$350M, and Token Vesting cliff in 4 days
  When the LangGraph multi-agent network executes
  Then the Socratic Agent outputs EXACTLY 3 Fatal Socratic Questions
  And computes FOMO Index >= 85.0
  And sets anti_fomo_verdict to "REJECT_SETUP_TOO_RISKY"
  And establishes the Worst-Case Invalidation Price at $90,800.
```

---

### UC-05: Multi-Channel Delivery (Export Memo PDF/Markdown & Telegram Alert Bot)
- **Primary Actor**: Multi-Channel Delivery Nodes (`src/ui/`, `src/bot/`).
- **Goal**: Distribute audited intelligence across Streamlit Web Dashboard, PDF/Markdown Memos, and Telegram Alerts.

#### BDD Scenarios:
```gherkin
Scenario: Telegram Bot on-demand audit request
  Given a user messages the Telegram bot with "/audit BTC"
  When the bot triggers the backend audit pipeline
  Then the bot responds in < 3.0s with the structured audit card
  Including MVRV Z-Score, Funding APR, 3 Fatal Socratic Questions, and Risk Disclaimer.

Scenario: Real-time Telegram alert for Whale CEX Deposit
  Given a whale transfers > $50,000,000 BTC to a Binance spot deposit address
  When the Whale Flow Engine flags a distribution alert
  Then the Telegram bot broadcasts an immediate alert to all subscribed channels.
```

---

## 3. Exception Handling Matrix

| Error Scenario | Root Cause | System Response | Fallback Action |
|---|---|---|---|
| **Binance WebSocket Disconnect** | Network timeout or exchange reset | Auto-reconnect with exponential backoff (1s, 2s, 4s...) | Fallback to public REST polling |
| **ETF Feed Delay / Stale Data** | Farside/SoSoValue update delay | Log notice; set `etf_data_stale=True` | Use previous day's close netflow |
| **Telegram API Rate Limit** | Too many broadcast messages | Queue alerts in Redis buffer; rate limit to 30 msgs/sec | Drop duplicate non-critical alerts |
| **LLM Inference Timeout (>6.0s)** | API latency spike | Abort agent turn; record `llm_timeout` | Return deterministic rule-based audit card |
