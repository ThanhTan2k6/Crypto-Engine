---
name: skill_forensic_redflags
description: On-chain forensic heuristics to detect whale dumps, exchange insolvencies, low-float dilution, and wash trading.
---

# Skill: Forensic On-Chain Red Flags & Anomaly Detection

## 1. Scope & Objective
Provides behavioral patterns and heuristic rules to identify predatory practices in crypto markets before entering positions.

## 2. Red Flag Heuristics

### 1. Exchange Reserve Depletion (Insolvency Alert)
- **Condition**: CEX stablecoin reserves fall $> 25\%$ within 48 hours while Bitcoin outflow accelerates without matching price expansion.
- **Action**: Immediate red alert; advise withdrawing capital from the exchange. (Reference: FTX / Alameda Nov 2022).

### 2. Whale Distribution Divergence
- **Condition**: Price reaches higher resistance while Netflow shows $> \$500\text{M}$ transferred onto spot exchanges with flat or negative taker buy volume.
- **Action**: Invalidate breakout setups; flag as Smart Money distributing into retail liquidity.

### 3. Low Float / Predatory FDV Trap
- **Condition**: $\frac{\text{Circulating Market Cap}}{\text{Fully Diluted Valuation (FDV)}} < 0.15$ with $> 5\%$ token unlock within 14 days.
- **Action**: Ban spot accumulation; token supply hyper-dilution imminent.

### 4. Wash Trading & Volume Fabrication
- **Condition**: 24h Volume / Market Cap $> 3.0$ on non-major altcoins accompanied by bid-ask spreads $> 1.5\%$ and flat active on-chain wallets.
- **Action**: Flag artificial wash trading; prevent market orders due to severe slippage risk.
