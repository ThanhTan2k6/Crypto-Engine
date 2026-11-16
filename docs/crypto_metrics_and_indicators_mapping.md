# Crypto Metrics, Indicators & Mathematical Mapping Specification

## 1. Scope & Standards
This document details all mathematical formulations implemented by the **Deterministic Quant Engine (`src/engine/`)** across both **Mode Spot** and **Mode Futures**. LLMs must never perform this math; they consume the pre-calculated metrics verbatim.

---

## 2. Mode Spot: Cycle Valuation & Accumulation Indicators

### 2.1. MVRV Z-Score
Measures whether an asset is overvalued or undervalued relative to its "fair value" (Realized Value):
$$\text{MVRV} = \frac{\text{Market Capitalization}}{\text{Realized Capitalization}}$$
$$\text{MVRV Z-Score} = \frac{\text{Market Cap} - \text{Realized Cap}}{\sigma_{\text{Market Cap}}}$$

#### Valuation Regime Lookup:
| MVRV Z-Score | Cycle Status | Recommended Action | Allocation Bias |
|---|---|---|---|
| **$Z < 0.1$** | **Cycle Generational Bottom** (Historical Capitulation) | Maximum Spot Accumulation (Aggressive DCA) | $150\% - 200\%$ tranche |
| **$0.1 \le Z < 1.5$** | **Early Bull / Accumulation** | Standard Systematic DCA | $100\%$ base tranche |
| **$1.5 \le Z < 3.5$** | **Mid-Bull / Healthy Expansion** | Hold & Maintain Positions | $50\%$ tranche (selective) |
| **$3.5 \le Z < 5.0$** | **Late Bull / Overheated** | Begin Phased Profit Taking (TP1, TP2) | $0\%$ buying (Distribution) |
| **$Z \ge 5.0$** | **Cycle Top Euphoria Peak** | Aggressive Liquidation to Cash/Stablecoins | Total capital defense |

---

### 2.2. Mayer Multiple & 200-Week Moving Average
Measures price extension relative to long-term baseline trends:
$$\text{Mayer Multiple} = \frac{\text{Current Price}}{\text{200-Day SMA}}$$
$$\text{200W-MA Ratio} = \frac{\text{Current Price}}{\text{200-Week SMA}}$$
- **Mayer Multiple $< 0.8$ or 200W-MA Ratio $\le 1.05$**: Structural bottom support; historical maximum risk-adjusted accumulation zone.
- **Mayer Multiple $> 2.4$**: Historical cyclical over-extension.

---

### 2.3. Pi Cycle Top Indicator
$$\text{Pi High SMA} = \text{SMA}_{350}(P) \times 2.0, \quad \text{Pi Low SMA} = \text{SMA}_{111}(P)$$
- **Cycle Top Alert**: Triggered when $\text{SMA}_{111}$ crosses above $\text{SMA}_{350} \times 2.0$.

---

### 2.4. Algorithmic DCA Accumulation & Take-Profit Zones
Zones are dynamically computed based on Fibonacci retracements combined with Realized Price and Volume Profile Value Area:
$$\text{DCA Zone 1 (Conservative)} = P_{\text{current}} \times 0.92$$
$$\text{DCA Zone 2 (Moderate)} = \max(P_{\text{Realized}}, \, P_{\text{current}} \times 0.85)$$
$$\text{DCA Zone 3 (Aggressive/Capitulation)} = \text{SMA}_{200W}$$

$$\text{Take-Profit 1 (De-risk)} = P_{\text{current}} \times 1.35$$
$$\text{Take-Profit 2 (Mid-Cycle)} = P_{\text{current}} \times 1.75$$
$$\text{Take-Profit 3 (Cycle Peak)} = P_{\text{current}} \times 2.50$$

---

## 3. Mode Futures: Real-Time Leverage & Microstructure Indicators

### 3.1. Funding Rate Squeeze Index (FRSI)
$$\text{APR}_{\text{funding}} = \text{FR}_{8h} \times 3 \times 365 \times 100\%$$
$$\text{FRSI} = \text{clip}\left(\frac{\text{APR}_{\text{funding}}}{100.0} \times 50.0 + 50.0, \, 0.0, \, 100.0\right)$$
- **$\text{FRSI} \ge 85.0$ ($\text{APR} \ge +70\%$)**: Extreme Long Squeeze hazard. Leveraged longs pay excessive carry bleed.
- **$\text{FRSI} \le 20.0$ ($\text{APR} \le -60\%$)**: Extreme Short Squeeze hazard. Short seller crowding.

---

### 3.2. Orderbook Imbalance Ratio (OBIR)
Measures bid vs ask liquidity depth within $\pm 2.0\%$ of the mid-price:
$$\text{OBIR} = \frac{\sum \text{Bid Depth}_{2\%}}{\sum \text{Bid Depth}_{2\%} + \sum \text{Ask Depth}_{2\%}}$$
- **$\text{OBIR} < 0.35$**: Thin bid depth; vulnerability to downward stop-loss hunting wicks.
- **$\text{OBIR} > 0.65$**: Strong bid support; high absorption capacity.

---

## 4. Institutional & Whale Flow Indicators

### 4.1. CEX Netflow Accumulation Index (CNAI)
$$Z_{\text{netflow}} = \frac{\text{Netflow}_{24h} - \mu_{30d}}{\sigma_{30d}}$$
$$\text{CNAI} = \text{clip}\left(50.0 - (Z_{\text{netflow}} \times 15.0), \, 0.0, \, 100.0\right)$$
- $\text{CNAI} \ge 75.0$: Smart Money Cold Storage Withdrawal.
- $\text{CNAI} \le 35.0$: Whale Inflow Dump Preparation.

### 4.2. Tether Treasury Minting Velocity (TTMV)
$$\text{TTMV}_{7d} = \frac{\sum \text{USDT Minted}_{7d} - \sum \text{USDT Burned}_{7d}}{\text{Total USDT Supply}} \times 100\%$$
- **$\text{TTMV}_{7d} > +1.5\%$**: "Fresh Cash" injection; historically leads to positive spot crypto price appreciation within 72-96 hours.

### 4.3. ETF Institutional Momentum Index (EIMI)
$$\text{EIMI} = \frac{\sum \text{Net ETF Inflow}_{5d} (\text{USD})}{\text{Average 5-day Spot Volume}} \times 100$$
- **$\text{EIMI} > +5.0$**: Strong institutional absorption by BlackRock (IBIT), Fidelity (FBTC).
- **$\text{EIMI} < -5.0$**: Institutional institutional de-risking and outflow pressure.
