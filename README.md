# CryptoIntel-Engine

> **Dual-Engine Crypto Intelligence: Spot Cycle Valuation, Real-time Futures Risk & Multi-Agent Socratic Auditing Platform**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-red.svg)](https://streamlit.io/)
[![Telegram](https://img.shields.io/badge/bot-Telegram-blue.svg)](https://core.telegram.org/bots)
[![DeepEval](https://img.shields.io/badge/evals-DeepEval-purple.svg)](https://github.com/confident-ai/deepeval)

---

## 1. Executive Summary & Dual-Engine Product Vision

**CryptoIntel-Engine** is an institutional-grade, anti-FOMO decision support platform designed to prevent crypto investors from buying cycle tops and panic-selling bottoms. Operating as an **Independent Investment Committee** and **Socratic Devil's Advocate**, the platform features two distinct specialized operational modes:

### 🌟 Mode Spot (Long-Term Investment & Smart Accumulation)
- **Cycle Top & Bottom Identification**: Leverages quantitative on-chain metrics: MVRV Z-Score, Realized Price, 200-Week Moving Average, Mayer Multiple, and Pi Cycle.
- **Algorithmic Accumulation & Take-Profit Zones**: Programmatically derives mathematically grounded DCA Buy Zones and Take-Profit Tariffs instead of emotional guessing.
- **Supply Dilution & Institutional Flows**: Real-time tracking of Token Unlock Vesting cliffs (DeFiLlama/TokenUnlocks) and Spot Bitcoin/ETH ETF net flows (BlackRock, Fidelity).

### ⚡ Mode Futures (Short-Term Leverage & Squeeze Defense)
- **Real-Time Derivatives Health**: Tracks 8h Funding Rate APR, Open Interest (OI) Divergence, and Liquidation Squeeze Heatmaps.
- **High-Velocity Liquidity Tracing**: Alerts on CEX Inflow/Outflow spikes, Tether Treasury "Fresh Cash" Minting, and Orderbook Depth Imbalances to prevent stop-loss hunting.

### 🛡️ Socratic Devil's Advocate (Anti-FOMO Inquisitor)
- Before entering any spot accumulation tranche or leveraged swing position, an automated multi-agent council interrogates the investor with **3 Fatal Socratic Questions**, calculates the **FOMO Index**, and identifies the **Worst-Case Invalidation Price**.

---

## 2. System Architecture & Multi-Channel Delivery

```mermaid
flowchart TD
    subgraph Data_Stack["Zero-Cost Real-Time Data Stack"]
        D1["Binance / Bybit Public WebSocket & REST\n(Spot/Futures Ticker, OI, Funding, Depth)"]
        D2["FRED API + CME FedWatch\n(Fed Funds, CPI, DXY, US 10Y)"]
        D3["On-Chain & Institutional Feeds\n(ETF Netflows, CEX Flows, Tether Minting, Vesting)"]
    end

    subgraph Quant_Engine["Deterministic Quant Engine (src/engine/) - Pure Python"]
        Q_Spot["Mode Spot Engine\n(MVRV Z-Score, 200W-MA, Mayer, DCA Zones)"]
        Q_Futures["Mode Futures Engine\n(FRSI, OI Divergence, Squeeze Heatmaps)"]
        Q_Whale["Flow & Dilution Engine\n(CNAI, Tether Velocity, Token Unlocks)"]
        Q_Contract["Frozen Pydantic v2 Contracts\n(strict=True, frozen=True)"]
        
        Q_Spot & Q_Futures & Q_Whale --> Q_Contract
    end

    subgraph Caching_Observability["Caching & Observability (src/llmops/)"]
        RC["Redis Semantic Cache\n(<200ms Response)"]
        LF["Langfuse Tracing"]
    end

    subgraph Multi_Agent["LangGraph Socratic Network (src/agents/)"]
        SV["Supervisor Agent\n(Fund Coordinator)"]
        S_Spot["Spot Cycle Strategist"]
        S_Fut["Futures & Liquidation Hunter"]
        S_Whale["Whale & Institutional Flow Agent"]
        SD["Socratic Devil's Advocate Agent\n(3 Fatal Anti-FOMO Questions)"]
        
        SV --> S_Spot & S_Fut & S_Whale
        S_Spot & S_Fut & S_Whale --> SD
    end

    subgraph Multi_Channel["Multi-Channel Interfaces"]
        API["FastAPI Core Service (Port 8000)\nREST & WebSocket Telemetry"]
        DASH["Streamlit Dashboard (Port 8501)\nVisual Candles, Indicator Gauges, Chat"]
        BOT["Telegram Risk Alert Bot\n/audit <symbol> & Volatility Alerts"]
    end

    D1 & D2 & D3 --> Q_Spot & Q_Futures & Q_Whale
    Q_Contract --> RC
    RC -- Cache Miss --> SV
    RC -- Cache Hit (<0.2s) --> Multi_Channel
    SD --> API & DASH & BOT
    SV -. Traced by .-> LF
```

---

## 3. Feature Comparison

| Capability | Generic AI Bot | Typical Chart Indicators | CryptoIntel-Engine |
|---|---|---|---|
| **Mathematical Precision** | Low (Frequent Hallucinations) | High | **Exact (Deterministic Quant Engine)** |
| **Spot Cycle Valuation** | Guesswork based on training text | Static moving averages | **MVRV Z-Score, 200W-MA, Realized Price, Mayer** |
| **DCA & Take Profit Zones** | Vague advice | Manual Fibonacci drawing | **Algorithmic Valuation Zones** |
| **Futures Squeeze Defense** | None | Raw funding numbers | **FRSI Index, Squeeze Heatmaps, OI Divergence** |
| **Token Unlock Dilution** | Not accounted for | Manual schedule checking | **Automated Vesting Cliff Alerts** |
| **Anti-FOMO Psychological Gate** | Sycophantic ("Great buy!") | Ignorant of psychology | **Socratic Devil's Advocate (3 Fatal Questions)** |
| **Delivery Interfaces** | Web chat only | TradingView | **FastAPI + Streamlit Dashboard + Telegram Bot** |

---

## 4. Performance Targets & SLAs

- **Deterministic Quant Engine**: Latency $< \mathbf{500\text{ms}}$ (0.5s).
- **Multi-Agent LangGraph Workflow**:
  - Cold Request: $< \mathbf{6.0\text{s}}$ for complete multi-agent committee critique.
  - Cached Request (Redis Semantic Cache): $< \mathbf{200\text{ms}}$ (0.2s).
- **DeepEval Faithfulness Benchmark**: $\ge \mathbf{0.95}$ (automated CI/CD regression testing across 10 historical Golden Cases).

---

## 5. Installation & Quickstart

```bash
# 1. Clone repository
git clone https://github.com/CryptoIntel/CryptoIntel-Engine.git
cd CryptoIntel-Engine

# 2. Configure Environment
cp .env.example .env
# Fill in GEMINI_API_KEY, FRED_API_KEY, TELEGRAM_BOT_TOKEN

# 3. Install dependencies via Makefile
make install

# 4. Run tests and linting
make check

# 5. Launch complete stack via Docker Compose (App + Redis + Bot)
make docker-up
```

Access the Streamlit Dashboard at `http://localhost:8501`, FastAPI Docs at `http://localhost:8000/docs`, and message your Telegram Bot with `/audit BTC`.
