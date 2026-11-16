"""
Streamlit Web Dashboard for CryptoIntel-Engine.
Visualizes Mode Spot (Cycle Valuation & DCA Targets), Mode Futures (Leverage Squeeze),
Whale & Macro telemetry, and Multi-Agent Socratic Audit findings.
"""

import asyncio

import streamlit as st

from src.agents.graph import run_crypto_audit
from src.engine.core_quant import CoreQuantEngine

st.set_page_config(
    page_title="CryptoIntel-Engine | Decision Support Copilot",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ CryptoIntel-Engine: Market Intelligence & Socratic Risk Audit")
st.caption(
    "Dual-Engine Spot Cycle Valuation, Real-time Futures Leverage Squeeze & Socratic Devil's Advocate Copilot"
)

# Sidebar controls
st.sidebar.header("🎯 Target Asset & Mode Selection")
symbol_input = st.sidebar.text_input("Asset Symbol", value="BTC").upper()
symbol = symbol_input.replace("USDT", "") + "USDT"

analysis_mode = st.sidebar.radio(
    "Execution Mode",
    options=["DUAL_AUDIT", "MODE_SPOT", "MODE_FUTURES"],
)

proposed_trade = st.sidebar.text_input("Proposed Trade Setup (Optional)", value="BUY_SPOT_DCA")

run_audit_btn = st.sidebar.button("🚀 Chạy Thẩm định Rủi ro", type="primary")

# Run quant audit and LangGraph workflow
engine = CoreQuantEngine()
quant_audit = engine.run_full_quant_audit(symbol=symbol)

spot_data = quant_audit["spot"]
futures_data = quant_audit["futures"]
whale_data = quant_audit["whale"]

with st.spinner(f"Hội đồng AI đang thẩm định {symbol}..."):
    audit_state = asyncio.run(
        run_crypto_audit(
            symbol=symbol,
            execution_mode=analysis_mode,
            spot_valuation_data=spot_data.model_dump(),
            futures_squeeze_data=futures_data.model_dump(),
            whale_flow_data=whale_data.model_dump(),
            etf_flow_data=quant_audit["etf"].model_dump(),
            token_vesting_data=quant_audit["vesting"].model_dump(),
            proposed_action=proposed_trade,
        )
    )

tab_overview, tab_spot, tab_futures = st.tabs([
    "🏛️ Socratic Audit & Verdict",
    "📈 Mode Spot (Cycle DCA)",
    "⚡ Mode Futures (Leverage Risk)",
])

with tab_overview:
    st.subheader(f"🔍 Multi-Agent Audit Summary for {symbol}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Price (USD)", f"${spot_data.current_price:,.2f}")
    with col2:
        st.metric("Cycle Regime", spot_data.cycle_regime.value)
    with col3:
        st.metric("Futures Risk", futures_data.futures_risk_level.value, f"APR {futures_data.annualized_funding_rate:.1f}%")
    with col4:
        st.metric("Anti-FOMO Verdict", audit_state["anti_fomo_verdict"], f"FOMO {audit_state['fomo_index']}/100")

    st.markdown("---")
    st.markdown("### 🗣️ Socratic Devil's Advocate - 3 Fatal Cross-Examinations")
    for idx, q in enumerate(audit_state.get("fatal_socratic_questions", []), 1):
        st.warning(f"⚠️ **Câu hỏi {idx}:** {q}")

    st.markdown(f"🛑 **Mức giá Vô hiệu hóa Tồi tệ nhất (Worst-Case Invalidation):** `${audit_state['worst_case_invalidation_price']:,.2f}`")

with tab_spot:
    st.subheader(f"📊 Spot Accumulation & Cycle Valuation ({symbol})")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.metric("MVRV Z-Score", f"{spot_data.mvrv_zscore:.2f}", "Fair Value [0.1 - 5.0]")
    with sc2:
        st.metric("Mayer Multiple", f"{spot_data.mayer_multiple:.2f}", "200-Day SMA Benchmark")
    with sc3:
        st.metric("Pi Cycle Top Alert", "TRIGGERED" if spot_data.pi_cycle_top_triggered else "NORMAL")

    st.markdown("#### 🎯 Algorithmic DCA Accumulation Zones")
    st.info(f"🔹 **Zone 1 (Conservative -8%):** ${spot_data.dca_zone_conservative:,.2f}")
    st.info(f"🔹 **Zone 2 (Moderate / Realized Floor):** ${spot_data.dca_zone_moderate:,.2f}")
    st.info(f"🔹 **Zone 3 (Aggressive / 200W-MA Floor):** ${spot_data.dca_zone_aggressive:,.2f}")

    st.markdown("#### 💰 Algorithmic Take-Profit Targets")
    st.success(f"🟢 **TP 1 (+35% Initial De-risk):** ${spot_data.take_profit_target_1:,.2f}")
    st.success(f"🟢 **TP 2 (+75% Mid-Cycle Expansion):** ${spot_data.take_profit_target_2:,.2f}")
    st.success(f"🟢 **TP 3 (+150% Cycle Top Euphoria):** ${spot_data.take_profit_target_3:,.2f}")

with tab_futures:
    st.subheader(f"⚡ Derivatives Leverage & Liquidation Risk ({symbol})")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.metric("Funding Rate (8h)", f"{futures_data.funding_rate_8h * 100:.3f}%", f"APR: {futures_data.annualized_funding_rate:.1f}%")
    with fc2:
        st.metric("FRSI Score (0-100)", f"{futures_data.frsi_score:.1f}")
    with fc3:
        st.metric("Orderbook Imbalance (±2%)", f"{futures_data.orderbook_imbalance_ratio:.2f}")

    st.markdown("#### 🎯 Estimated High-Leverage Liquidation Clusters")
    st.error(f"🔴 **Short Liquidation Pocket Above (+1.5% 24h High):** ${futures_data.liquidation_pocket_above:,.2f}")
    st.error(f"🟢 **Long Stop Sweep Pocket Below (-2.0% 24h Low):** ${futures_data.liquidation_pocket_below:,.2f}")

st.markdown("---")
st.caption(
    "⚠️ **Digital Asset Risk Disclaimer**: This platform is an educational decision-support tool. "
    "Digital assets involve extreme volatility and structural risk. Never allocate capital you cannot afford to lose."
)
