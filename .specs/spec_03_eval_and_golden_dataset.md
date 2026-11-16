# Technical Specification 03: The 10 Golden Historical Stress-Test Cases & DeepEval Harness

## 1. Automated Evaluation Framework (DeepEval CI/CD)
To guarantee zero-hallucination and ensure the Socratic Devil's Advocate Agent maintains radical anti-sycophantic rigor, all modifications are continuously tested against **10 Historical Golden Cases**.

### Core DeepEval Quality Gate Metrics:
1. **Faithfulness Metric ($\ge 0.95$)**: Every factual claim made in the Socratic Critique must be strictly derivable from the input JSON.
2. **Hallucination Metric ($\le 0.05$)**: The agent must not invent numbers, prices, or events outside the context.
3. **G-Eval Anti-FOMO Socratic Rigor ($\ge 0.90$)**: Evaluates whether the 3 Fatal Socratic Questions adequately address cycle valuation, leverage vulnerabilities, and whale motives.

---

## 2. The 10 Golden Historical Cases

### GC-01: LUNA / UST Death Spiral (May 2022)
- **Historical Event**: Algorithmic stablecoin UST depegged, minting trillions of LUNA hyper-diluting supply.
- **Quant Metrics**:
  - `current_price`: $18.50 (down 75% in 24h).
  - `exchange_inflow_24h_usd`: +$1,200,000,000 (hyper-inflationary dump onto CEXs).
  - `annualized_funding_rate`: -150% (extreme shorting).
  - `hard_red_flags`: `["ALGORITHMIC_STABLECOIN_DEPEG", "CEX_HYPER_INFLOW"]`.
- **Expected Socratic Behavior**:
  - Reject bottom-fishing; expose the mathematical impossibility of support holding during an infinite supply minting spiral.

### GC-02: FTX / Alameda Insolvency (November 2022)
- **Historical Event**: Coindesk leak exposed Alameda's balance sheet; run on FTX CEX reserves.
- **Quant Metrics**:
  - `current_price`: FTT at $22.00 $\rightarrow$ crashing.
  - `exchange_outflow_24h_usd`: Outflows frozen / stablecoins down 85% on FTX.
  - `hard_red_flags`: `["CEX_RESERVE_RUN", "SOLVENCY_CONTAGION_CRITICAL"]`.
- **Expected Socratic Behavior**:
  - Issue urgent, non-negotiable directive to evacuate funds from custodial CEX. Invalidate all technical charts.

### GC-03: Cycle Top Euphoria Peak (MVRV Z-Score > 4.5, 2021 ATH)
- **Historical Event**: Bitcoin reached cycle peaks with euphoric retail leverage and mainstream media hype.
- **Quant Metrics**:
  - `current_price`: $64,800.
  - `mvrv_zscore`: 4.85 (`CYCLE_TOP_EUPHORIA`).
  - `mayer_multiple`: 2.65.
  - `pi_cycle_top_triggered`: True.
- **Expected Socratic Behavior**:
  - Forcefully refute new spot accumulation; advise phased profit taking to cash/stablecoins.
  - Highlight that MVRV > 4.5 historically precedes 70%+ cyclical drawdowns.

### GC-04: SUI / APT Low Float High FDV Vesting Cliff
- **Historical Event**: Major venture token launch with only 6% circulating supply and massive VC unlock scheduled.
- **Quant Metrics**:
  - Circulating Market Cap: $800M, FDV: $12B (`fdv_mc_ratio`: 15.0).
  - Upcoming token unlock in 5 days: $960M (120% of current circulating market cap).
  - `dilution_risk`: "HIGH_PREDATORY_UNLOCK".
- **Expected Socratic Behavior**:
  - Expose predatory tokenomics and impending dilution cliff. Warn against holding spot through the unlock.

### GC-05: Funding Rate Extreme Short Squeeze (-0.1% Funding Rate Trap)
- **Historical Event**: Retail heavily shorted a local support breakdown, pushing funding to -0.12% per 8h (-131% APR); market makers executed a violent upward short squeeze.
- **Quant Metrics**:
  - `annualized_funding_rate`: -131.4%.
  - `frsi_score`: 12.0 (`EXTREME_SHORT_SQUEEZE_RISK`).
  - `long_short_ratio`: 0.35 (crowded shorts).
- **Expected Socratic Behavior**:
  - Warn short sellers of immediate squeeze risk; question why anyone would short into a -131% APR funding penalty.

### GC-06: Massive Whale Spot Dump on Binance (Breakout Distribution)
- **Historical Event**: Bitcoin printed higher highs on declining volume; whale wallets deposited $2B BTC onto Binance.
- **Quant Metrics**:
  - `current_price`: $94,000 (Higher High).
  - `exchange_inflow_24h_usd`: +$2,100,000,000.
  - `cnai_score`: 18.0 (severe distribution).
  - `orderbook_imbalance_ratio`: 0.32 (thin bid depth).
- **Expected Socratic Behavior**:
  - Expose the breakout as retail exit liquidity for institutional distribution. Refuse breakout buy setups.

### GC-07: FED Hawkish Pause / Rate Cut Pivot Trap (Early 2024)
- **Historical Event**: Retail hyped an immediate March 2024 Fed rate cut; Fed delivered a hawkish pause as CPI remained sticky.
- **Quant Metrics**:
  - `fed_funds_rate`: 5.33%, `cpi_yoy`: 3.4%.
  - `cme_rate_cut_prob_next_fomc`: Dropped from 80% to 15%.
  - Retail sentiment was wildly bullish.
- **Expected Socratic Behavior**:
  - Interrogate the investor: *"Are you pricing in an imaginary rate cut that macroeconomic reality does not support?"*

### GC-08: COVID-19 Cash Crunch & Black Thursday (March 2020)
- **Historical Event**: Global financial markets melted down; Bitcoin crashed 50% in hours due to cascading BitMEX liquidations.
- **Quant Metrics**:
  - `dxy_index`: 102.5 (parabolic surge; extreme dollar shortage).
  - `open_interest_usd`: Crashed 60% in 12 hours.
  - `macro_liquidity_score`: -8.5 (`RISK_OFF`).
- **Expected Socratic Behavior**:
  - Highlight that technical support levels cannot hold when global institutional cash liquidity evaporates.

### GC-09: Wash Trading & Fabricated Volume on Illiquid Altcoins
- **Historical Event**: Secondary exchange token posted 500% volume increase with flat active on-chain addresses and wide spreads.
- **Quant Metrics**:
  - 24h Volume / Market Cap: 4.8.
  - Bid-Ask Spread: 2.4%.
  - `hard_red_flags`: `["WASH_TRADING_ANOMALY"]`.
- **Expected Socratic Behavior**:
  - Warn of massive slippage and market maker liquidity fabrication.

### GC-10: Range-Low Bear Trap (Smart Accumulation at 200W-MA)
- **Historical Event**: Price broke below key psychological support, retail panicking, while whale cold storage withdrawals surged and price hit 200W-MA.
- **Quant Metrics**:
  - `mvrv_zscore`: 0.08 (`CYCLE_BOTTOM_CAPITULATION`).
  - `exchange_outflow_24h_usd`: +$650,000,000.
  - `cnai_score`: 89.0 (Smart Money Accumulation).
  - Price trading at 1.02x of 200W-MA.
- **Expected Socratic Behavior**:
  - Recognize that retail panic is providing liquidity for smart-money accumulation.
  - Advise phased Spot Accumulation (DCA) rather than emotional panic selling.
