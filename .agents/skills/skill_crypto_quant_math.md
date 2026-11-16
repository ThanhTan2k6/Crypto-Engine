# Agent Skill: Crypto Quant Mathematics & Derivatives Formulas

## 1. Description
Provides pure mathematical reference equations used by the Deterministic Quant Engine. LLMs must NOT perform this math; they use this skill to understand the mathematical meaning of pre-computed metrics.

---

## 2. Mathematical Reference

### Annualized Funding Rate
$$\text{APR}_{\text{funding}} = \text{FR}_{8h} \times 3 \times 365 \times 100\%$$
- Standard baseline: $\text{FR}_{8h} = 0.0001$ (0.01%) $\rightarrow \text{APR} = 10.95\%$.
- Euphoric extreme: $\text{FR}_{8h} = 0.0010$ (0.10%) $\rightarrow \text{APR} = 109.50\%$.

### Funding Rate Squeeze Index (FRSI)
$$\text{FRSI} = \text{clip}\left(\frac{\text{APR}_{\text{funding}}}{100.0} \times 50.0 + 50.0, \, 0.0, \, 100.0\right)$$
- $\text{FRSI} \ge 85.0$: Extreme Long Squeeze risk.
- $\text{FRSI} \le 20.0$: Extreme Short Squeeze risk.

### Dynamic Dollar-Cost Averaging (DCA) Level Multiplier
For Spot Accumulation, tranche sizes scale inversely with the Macro Liquidity Score and CNAI:
$$\text{Tranche Multiplier} = 1.0 + \left(\frac{\text{CNAI} - 50.0}{50.0} \times 0.5\right) + \left(\frac{\text{MLS}}{10.0} \times 0.5\right)$$
- When Whales accumulate ($\text{CNAI} = 90$) in Risk-On ($\text{MLS} = +6.0$): Tranche Multiplier $= 1.0 + 0.4 + 0.3 = 1.7\times$.
- When Whales dump ($\text{CNAI} = 20$) in Risk-Off ($\text{MLS} = -6.0$): Tranche Multiplier $= 1.0 - 0.3 - 0.3 = 0.4\times$ (capital preservation).

### Risk-to-Reward Ratio (RRR)
$$\text{RRR} = \frac{|\text{Take Profit Price} - \text{Entry Price}|}{|\text{Entry Price} - \text{Invalidation Stop Price}|}$$
- Minimum acceptable threshold for swing trades: $\text{RRR} \ge 2.5$.
