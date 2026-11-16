# CLAUDE.md - Developer & Agent Operating Manual for CryptoIntel-Engine

## 1. Project Overview & Dual-Engine Architecture
**CryptoIntel-Engine** is an institutional-grade, anti-FOMO decision support platform operating under a **Dual-Engine Architecture**:
- **MODE SPOT**: On-Chain Cycle Valuation (MVRV Z-Score, Realized Price, 200W-MA, Mayer Multiple), Algorithmic DCA/Take-Profit zones, Spot ETF Flows, and Token Vesting cliffs.
- **MODE FUTURES**: High-frequency leverage monitoring (Funding Rate APR, OI Divergence, Liquidation Squeeze Heatmaps, Orderbook Imbalance, Tether Minting velocity).
- **SOCRATIC DEVIL'S ADVOCATE**: Anti-FOMO multi-agent inquisitor requiring 3 fatal questions before placing capital at risk.
- **MULTI-CHANNEL INTERFACE**: FastAPI Backend + Streamlit Web Dashboard + Telegram Risk Alert Bot (`/audit <symbol>`).

### Strict Decoupled Boundary
- `src/engine/`: Pure Python (NumPy, Pandas, Polars). **ZERO LLM IMPORTS ALLOWED**.
- `src/agents/`: LangGraph StateGraph running on frozen Pydantic v2 JSON contracts (`src/ingestion/schemas.py`).
- `src/bot/`: Telegram bot service communicating via webhooks or polling.
- `src/llmops/`: Redis Semantic Caching (<200ms) + Langfuse Tracing + DeepEval CI/CD.

---

## 2. Essential CLI Commands

```bash
# Setup & Environments
make install              # Install poetry dependencies
make env                  # Copy .env.example to .env

# Quality & Verification
make lint                 # Run ruff check and mypy --strict
make format               # Run ruff format and black
make test                 # Run deterministic quant tests (<0.5s SLA)
make eval                 # Run DeepEval 10 Golden Cases benchmark
make check                # Full check: lint + test + eval

# Execution & Services
make run-api              # Launch FastAPI backend (port 8000)
make run-ui               # Launch Streamlit Dashboard (port 8501)
make run-bot              # Launch Telegram Risk Alert Bot
make docker-up            # Boot complete system with Redis, API, Dashboard & Bot
```

---

## 3. Directory Layout
```
CryptoIntel-Engine/
├── .cursorrules                  # IDE governance & anti-hallucination rules
├── CLAUDE.md                     # This operational manual
├── README.md                     # Platform architecture & setup guide
├── Makefile                      # Standard build & run automation
├── pyproject.toml                # Dependencies & tool configs
├── requirements.txt              # Pinned requirements
├── Dockerfile                    # Containerization definition
├── docker-compose.yml            # Multi-service compose (App, Redis, Bot)
├── .github/workflows/ci.yml      # CI pipeline (MyPy, Ruff, PyTest, DeepEval)
├── docs/                         # ADRs & Indicator mapping
│   ├── adr/
│   │   └── 001_decoupled_architecture_and_realtime_llmops.md
│   ├── crypto_metrics_and_indicators_mapping.md
│   └── api_and_state_design.md
├── .specs/                       # Formal Technical Specifications
│   ├── spec_00_use_cases.md
│   ├── spec_01_data_contracts.md
│   ├── spec_02_agent_prompts.md
│   └── spec_03_eval_and_golden_dataset.md
├── .agents/skills/               # Agent Skill Reference Documents
│   ├── skill_spot_cycle_math.md
│   ├── skill_futures_squeeze_math.md
│   ├── skill_whale_and_etf_tracking.md
│   ├── skill_multi_agent_langgraph.md
│   └── skill_llmops_evals.md
├── src/
│   ├── ingestion/                # WebSocket & REST data connectors
│   │   └── schemas.py            # Immutable Pydantic v2 data contracts
│   ├── engine/                   # Pure Deterministic Quant Engine (NO LLMs)
│   ├── agents/                   # LangGraph StateGraph multi-agent network
│   ├── llmops/                   # Redis Cache, Langfuse Tracing, DeepEval evaluators
│   ├── bot/                      # Telegram Risk Alert Bot (/audit <symbol>)
│   └── ui/                       # Streamlit Real-Time Dashboard
├── tests/                        # Unit tests for quant math & ingestion
└── data/golden_eval/             # 10 Golden Historical Stress-Test Cases (JSON)
```
