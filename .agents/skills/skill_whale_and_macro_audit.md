# Agent Skill: Whale Tracking & Macro Liquidity Auditing

## 1. Description
Analytical guidelines for interpreting centralized exchange (CEX) net transfers, whale transaction clustering, Federal Reserve interest rate cycles, and Dollar Index (DXY) sensitivity.

---

## 2. Whale Netflow Behavioral Patterns

### Pattern A: Smart Money Cold Storage Drainage (Bullish Accumulation)
- **Signal**: Sustained negative netflow ($\text{Netflow}_{24h} < -\$200\text{M}$ USD) spanning $\ge 7$ days.
- **Microstructure**: Coins move from Binance/Coinbase hot wallets to unlabelled multi-sig custody addresses.
- **Implication**: Liquid float on exchanges decreases; supply shock potential increases.

### Pattern B: Pre-Dump Exchange Staging (Bearish Distribution)
- **Signal**: Massive positive netflow ($\text{Netflow}_{24h} > +\$300\text{M}$ USD) occurring while price tests local resistance.
- **Microstructure**: Whale addresses deposit to exchange deposit addresses; taker buy volume does not increase.
- **Implication**: Whales are preparing to sell into retail limit bids; high risk of a bull trap.

---

## 3. Macro Liquidity Sensitivity Matrix

| Macro Factor | High / Rising Trend | Low / Falling Trend | Impact on Crypto Beta |
|---|---|---|---|
| **Fed Funds Rate** | Restrictive credit; high risk-free hurdle rate (>5%) | Accommodative; low cash yield (<2%) | Higher rates compress speculative asset multiples |
| **US Dollar Index (DXY)** | Strong USD; liquidity drained from emerging/risk assets | Weak USD; global capital seeks yield | Crypto has a strong inverse correlation ($-0.7$) to DXY |
| **10Y-2Y Yield Curve** | Steepening / normalizing after inversion | Inversion (recession signal) | Un-inversion often coincides with equity/risk market selloffs |
