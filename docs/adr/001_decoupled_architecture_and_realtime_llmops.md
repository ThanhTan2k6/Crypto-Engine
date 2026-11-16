# ADR 001: Decoupled Dual-Engine Architecture, LangGraph StateGraph, Redis Caching, and Multi-Channel Delivery

- **Status**: ACCEPTED
- **Date**: 2026-11-16
- **Authors**: Principal AI Systems Architect & Quantitative Web3 FinTech Tech Lead
- **Scope**: Core System Architecture of CryptoIntel-Engine

---

## 1. Context & Business Drivers
Cryptocurrency investors face fundamentally different risk regimes depending on their horizon:
1. **Spot Accumulation Investors (Multi-Year Horizon)**: Suffer from buying cycle tops (e.g., MVRV Z-Score > 4.0) due to media hype and failing to accumulate at cycle bottoms (e.g., price below 200W-MA or Realized Price) due to panic. Furthermore, they are blind to massive dilution from token vesting cliffs and institutional ETF flow rebalancing.
2. **Futures & Swing Traders (Hours-to-Weeks Horizon)**: Suffer from leverage wipes, long/short squeeze cascades triggered by extreme funding rates, orderbook stop hunts, and rapid whale CEX inflows.

Conventional AI financial assistants fail by asking LLMs to compute these metrics, resulting in arithmetic hallucinations and sycophantic cheerleading.

---

## 2. Architectural Decisions

### 2.1. Dual-Engine Decoupled Architecture
We divide quantitative analysis into two specialized deterministic domains within `src/engine/`:
- **Mode Spot Engine**:
  - Implements on-chain valuation math: MVRV Z-Score, Realized Price, 200-Week Moving Average, Mayer Multiple, and Pi Cycle.
  - Programmatically defines 4 Accumulation DCA tranches and 3 Take-Profit target zones.
  - Tracks Institutional Spot ETF Netflows (BlackRock, Fidelity) and Token Unlock Vesting cliffs.
- **Mode Futures Engine**:
  - Computes high-frequency derivatives metrics: Funding Rate Squeeze Index (FRSI), Open Interest (OI) Divergence, Liquidation Heatmap clusters, and Orderbook Bid/Ask Imbalance.
  - Monitors high-velocity liquidity: CEX Netflows, Tether Treasury Minting alerts, and large whale transactions ($>\$1\text{M}$).
- **Zero LLM Invariant**: `src/engine/` is 100% Python (NumPy, Pandas, Polars) and contains **ZERO LLM IMPORTS**.

### 2.2. Multi-Agent Socratic Debate Network (LangGraph)
- Ingests frozen Pydantic v2 JSON contracts from the Dual-Engine Quant Layer.
- Runs parallel specialist nodes: `Spot Cycle Strategist`, `Futures & Liquidation Hunter`, and `Whale & Institutional Flow Agent`.
- Converges into the `Socratic Devil's Advocate Agent` to output **3 Fatal Socratic Questions**, the **FOMO Index**, and the **Worst-Case Invalidation Price**.

### 2.3. Multi-Channel Interface Architecture
To maximize accessibility, the platform exports its intelligence across three tiers:
1. **FastAPI Core Engine**: High-performance REST and WebSocket telemetry API.
2. **Streamlit Web Dashboard**: Interactive charts, metric gauges, and Socratic chat pane.
3. **Telegram Risk Alert Bot**: Mobile on-demand audit (`/audit <symbol>`) and real-time push alerts for whale dumps, Tether minting, and extreme funding squeezes.

### 2.4. Low-Latency Redis Semantic Caching & DeepEval Benchmark
- Market queries within a stable regime are cached in Redis for $< 200\text{ms}$ response times.
- Quality is strictly governed by automated **DeepEval** CI/CD benchmarks maintaining Faithfulness $\ge 0.95$ across 10 Historical Golden Cases.
