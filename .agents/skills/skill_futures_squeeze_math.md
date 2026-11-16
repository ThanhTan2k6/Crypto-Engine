# Agent Skill: Futures Squeeze & Derivatives Microstructure Math

## 1. Description
Provides mathematical equations for calculating perpetual funding rate APRs, Funding Rate Squeeze Index (FRSI), Open Interest Divergence, and Orderbook Imbalance.

---

## 2. Mathematical Formulations

### Annualized Funding Rate
$$\text{APR}_{\text{funding}} = \text{FR}_{8h} \times 3 \times 365 \times 100\%$$
- Standard baseline: $\text{FR}_{8h} = 0.0001$ (0.01%) $\rightarrow \text{APR} = 10.95\%$.
- Euphoric extreme: $\text{FR}_{8h} = 0.0010$ (0.10%) $\rightarrow \text{APR} = 109.50\%$.

### Funding Rate Squeeze Index (FRSI)
$$\text{FRSI} = \text{clip}\left(\frac{\text{APR}_{\text{funding}}}{100.0} \times 50.0 + 50.0, \, 0.0, \, 100.0\right)$$
- $\text{FRSI} \ge 85.0$: Extreme Long Squeeze risk (longs bleeding financing costs).
- $\text{FRSI} \le 20.0$: Extreme Short Squeeze risk (shorts crowded, explosive upside risk).

### Orderbook Imbalance Ratio (OBIR)
$$\text{OBIR} = \frac{\sum \text{Bid Depth}_{\pm 2\%}}{\sum \text{Bid Depth}_{\pm 2\%} + \sum \text{Ask Depth}_{\pm 2\%}}$$
- $\text{OBIR} < 0.35$: Bid liquidity deficit; vulnerable to downside wick sweeps.
- $\text{OBIR} > 0.65$: Bid liquidity support; strong absorption.

### Open Interest Divergence
$$\Delta \text{OI}_{24h} = \frac{\text{OI}_{t} - \text{OI}_{t - 24h}}{\text{OI}_{t - 24h}} \times 100\%$$
- If Price rises $> 2\%$ while OI rises $> 15\%$ with flat spot volume: Synthetic leverage debt pump.
