---
name: skill_quant_math
description: Strict mathematical formulations and indicator calculations for cryptocurrency derivatives and volume analytics.
---

# Skill: Deterministic Quant Mathematics

## 1. Scope & Objective
This skill defines the pure Python equations used across the Deterministic Quant Engine. LLMs must NOT modify these formulas.

## 2. Mathematical Formulations

### Volume Z-Score (20-day Lookback)
$$Z_{\text{vol}} = \frac{V_{\text{current}} - \mu_{20}}{\sigma_{20}}$$
Where:
- $\mu_{20}$: 20-period moving average of trading volume.
- $\sigma_{20}$: Standard deviation of volume over 20 periods.
- Alert threshold: $|Z_{\text{vol}}| > 2.5$ represents statistically anomalous volume.

### Annualized Funding Rate
$$\text{APR}_{\text{funding}} = \text{Funding Rate (8h)} \times 3 \times 365 \times 100\%$$
- If $\text{APR}_{\text{funding}} > 75\%$: Extreme Long Crowding (Squeeze danger).
- If $\text{APR}_{\text{funding}} < -30\%$: Aggressive Short Crowding (Short squeeze setup).

### Open Interest (OI) Delta (%)
$$\Delta \text{OI}_{24h} = \frac{\text{OI}_{t} - \text{OI}_{t - 24h}}{\text{OI}_{t - 24h}} \times 100\%$$
- If $\text{Price} \uparrow$ and $\Delta \text{OI} \uparrow$: New aggressive long leverage entering.
- If $\text{Price} \uparrow$ and $\Delta \text{OI} \downarrow$: Short covering (exhaustion rally).
