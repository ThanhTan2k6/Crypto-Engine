# Agent Skill: Spot Cycle Valuation Mathematics

## 1. Description
Provides mathematical formulas for long-term on-chain cycle valuation: MVRV Z-Score, Realized Price, 200W-MA, Mayer Multiple, Pi Cycle, and Algorithmic DCA/Take-Profit zones.

---

## 2. Core Mathematical Formulations

### MVRV Z-Score
$$\text{MVRV} = \frac{\text{Market Cap}}{\text{Realized Cap}}$$
$$\text{MVRV Z-Score} = \frac{\text{Market Cap} - \text{Realized Cap}}{\sigma_{\text{Market Cap}}}$$
- $Z < 0.1$: Generational bottom (Historical Capitulation). Maximum Spot DCA tranche.
- $Z > 3.5$: Overheated market. Phase 1 & 2 Profit Taking.
- $Z \ge 5.0$: Cycle Top Euphoria. Complete capital de-risking.

### Mayer Multiple
$$\text{Mayer Multiple} = \frac{P_{\text{current}}}{\text{SMA}_{200d}(P)}$$
- $< 0.8$: Historically undervalued accumulation zone.
- $> 2.4$: Severe over-extension.

### 200-Week Simple Moving Average (200W-MA)
$$\text{SMA}_{200W} = \frac{1}{200} \sum_{i=0}^{199} P_{\text{weekly}, i}$$
- Serves as the ultimate baseline floor in Bitcoin's historical market cycles.

### Dynamic DCA & Take-Profit Targets
$$\text{DCA Zone 1 (Conservative)} = P_{\text{current}} \times 0.92$$
$$\text{DCA Zone 2 (Moderate)} = \max(P_{\text{Realized}}, \, P_{\text{current}} \times 0.85)$$
$$\text{DCA Zone 3 (Aggressive/Capitulation)} = \text{SMA}_{200W}$$

$$\text{TP Target 1 (De-risk)} = P_{\text{current}} \times 1.35$$
$$\text{TP Target 2 (Mid-Cycle)} = P_{\text{current}} \times 1.75$$
$$\text{TP Target 3 (Cycle Peak)} = P_{\text{current}} \times 2.50$$
