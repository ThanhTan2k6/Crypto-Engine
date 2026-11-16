# ADR 001: Architectural Separation of Deterministic Quant Engine and Socratic Multi-Agent Network

- **Status**: ACCEPTED
- **Date**: 2026-11-16
- **Authors**: CryptoIntel Architecture Team
- **Context**: Trading & Spot Accumulation Engine for Cryptocurrency Markets

---

## 1. Context & Problem Statement
Cryptocurrency trading systems incorporating Large Language Models (LLMs) commonly fail due to:
1. **Mathematical Hallucinations**: LLMs miscalculating percentages, Z-scores, funding rate annualization, and liquidation thresholds.
2. **Sycophancy & Confirmation Bias (Cheerleading)**: LLMs tending to agree with user prompts (e.g., if the user asks "Should I long BTC now? It looks bullish!", LLMs find superficial bullish arguments).
3. **Black-box Decision Making**: Lack of verifiable audit trails and failure to comply with structured financial and accounting standards (e.g., Vietnam Circular 200/2014/TT-BTC).

We need an architecture that guarantees **100% mathematical precision** while leveraging AI strictly for **contextual synthesis, intention decoding, and counter-bias interrogation**.

---

## 2. Decision
We separate the system into two strictly bounded layers:

### Layer A: Deterministic Quant Layer (Zero-Hallucination)
- **Implementation**: Pure Python (NumPy, Polars/Pandas).
- **Responsibilities**:
  - Ingestion from Binance/Bybit public WebSockets/REST and FRED.
  - Calculation of indicators: 20-day Volume Z-score, Open Interest (OI) Delta, Annualized Funding Rates, Exchange Netflow Z-scores.
  - TT 200/2014/TT-BTC currency valuation, realized/unrealized PnL, risk provision calculation.
  - Emitting immutable **Pydantic v2 Contract Objects**.
- **Rule**: LLMs are strictly forbidden from participating in Layer A calculations.

### Layer B: Multi-Agent Socratic Reasoning Layer (LangGraph)
- **Implementation**: LangGraph StateGraph with typed `CryptoIntelState`.
- **Agents**:
  1. `Supervisor Agent`: Validates contracts, routes execution.
  2. `Macro Strategist Agent`: Evaluates FED interest rates, DXY, and global liquidity regime.
  3. `Whale Flow Analyst Agent`: Decodes accumulation vs. CEX distribution motives.
  4. `Derivatives & Sentiment Agent`: Detects funding traps, leverage imbalances, and squeeze setups.
  5. `Socratic Devil's Advocate Agent`: Formulates **3 Fatal Socratic Questions**, establishes worst-case invalidation levels, and computes a FOMO penalty score.
- **Rule**: Agents only receive validated JSON payloads from Layer A. Their output is qualitative reasoning, risk refutation, and thesis stress-testing.

---

## 3. Consequences

### Positive:
- **Zero Math Errors**: High-frequency numbers and accounting equations are immune to prompt degradation or model drift.
- **Anti-FOMO Psychological Safety**: The Socratic Agent forces the user to confront falsification points before entering trades.
- **Automated Verification**: The separation allows independent testing: Unit tests for Layer A math, and DeepEval CI/CD evaluations (Faithfulness $\ge 0.95$) for Layer B prompts.

### Negative / Trade-offs:
- Slightly increased boilerplate due to strict Pydantic v2 schemas.
- Latency overhead introduced by multi-agent reasoning steps (~1-3 seconds), acceptable for Spot Accumulation and Swing Trading, though not intended for sub-second High-Frequency Trading (HFT).
