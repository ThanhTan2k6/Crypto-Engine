# Specification 00: Use Cases & Investor Journeys

## 1. Overview
CryptoIntel-Engine is specifically designed to service two trading methodologies while mitigating cognitive biases (Greed, Euphoria, FOMO, Panic Selling):
1. **Spot Accumulation (Smart DCA)**: Long-term wealth building by acquiring blue-chip crypto assets (BTC, ETH) during macro depression and smart-money accumulation phases.
2. **Swing / Position Trading**: Multi-day to multi-week trend exploitation while avoiding leverage squeeze cascades.

---

## 2. Core Use Cases

### UC-01: Smart Spot Accumulation (DCA Optimizer)
- **Target Persona**: Long-term investor with a 1-4 year horizon.
- **Trigger**: Periodic DCA date or price reaching macro support zones.
- **System Workflow**:
  1. Quant Engine retrieves Macro Metrics from FRED and 24h Exchange Netflow.
  2. If Macro is `RISK_OFF` and Exchange Netflow indicates massive CEX Inflows (Whale dump preparation), Quant Engine generates a low `spot_accumulation_score`.
  3. Socratic Agent warns: *"Why buy today when macro liquidity is contracting and whales deposited $1.2B BTC on exchanges in the last 12 hours? Waiting for absorption saves capital."*
  4. System recommends allocating to cash/stablecoins or adjusting DCA tranches dynamically.

### UC-02: Swing Position Entry Verification (FOMO Killer)
- **Target Persona**: Swing trader looking to enter a 4-hour/Daily breakout setup.
- **Trigger**: User inputs a proposed trade idea (e.g., "Long BTC at $94,500 breakout with 5x leverage").
- **System Workflow**:
  1. Derivatives Quant calculates Funding Rate APR (> 85%), OI Delta (+18% in 4h), and Volume Z-Score.
  2. Derivatives Agent identifies a high probability of a Long Squeeze.
  3. Socratic Agent fires the **3 Fatal Questions**:
     - *Question 1*: "You are longing into an 85% annualized funding rate. Are you prepared to bleed daily carry cost if price chops for 5 days?"
     - *Question 2*: "Open Interest surged 18% without spot volume expansion. What evidence proves this is organic spot buying rather than a synthetic leveraged trap?"
     - *Question 3*: "If price drops 3.5% to sweep the $91,200 liquidity pool before moving up, will your stop-loss survive?"
  4. User is presented with an objective Risk/Reward matrix and falsification price before confirming the order.

### UC-03: Portfolio Rebalancing & TT 200 Accounting Audit
- **Target Persona**: Fund manager, corporate treasury, or compliance-conscious investor.
- **Trigger**: End-of-month or quarterly accounting valuation cycle.
- **System Workflow**:
  1. Quant Engine pulls mark prices for all crypto assets.
  2. Evaluates impairment provisions under Circular 200/2014/TT-BTC guidelines.
  3. Separates realized profits from unrealized gains to prevent premature taxation or distributions.
