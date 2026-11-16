# Agent Skill: Whale Netflows, Tether Minting & Spot ETF Tracking

## 1. Description
Analytical guidelines for interpreting centralized exchange (CEX) net transfers, Tether Treasury minting velocity, and institutional Spot Bitcoin/ETH ETF net flows.

---

## 2. Institutional Indicators & Formulations

### CEX Netflow Accumulation Index (CNAI)
$$Z_{\text{netflow}} = \frac{\text{Netflow}_{24h} - \mu_{30d}}{\sigma_{30d}}$$
$$\text{CNAI} = \text{clip}\left(50.0 - (Z_{\text{netflow}} \times 15.0), \, 0.0, \, 100.0\right)$$
- $\text{CNAI} \ge 75.0$: Smart Money Cold Storage Withdrawal.
- $\text{CNAI} \le 35.0$: Whale Inflow Dump Preparation.

### Tether Treasury Minting Velocity (TTMV)
$$\text{TTMV}_{7d} = \frac{\sum \text{USDT Minted}_{7d} - \sum \text{USDT Burned}_{7d}}{\text{Total USDT Supply}} \times 100\%$$
- $\text{TTMV}_{7d} > +1.5\%$: "Fresh Cash" injection; historically leads to spot price appreciation within 72-96 hours.

### ETF Institutional Momentum Index (EIMI)
$$\text{EIMI} = \frac{\sum \text{Net ETF Inflow}_{5d} (\text{USD})}{\text{Average 5-day Spot Volume}} \times 100$$
- $\text{EIMI} > +5.0$: Strong institutional absorption by BlackRock (IBIT), Fidelity (FBTC).
- $\text{EIMI} < -5.0$: Institutional de-risking and outflow pressure.
