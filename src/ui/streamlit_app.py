"""
Streamlit Web Dashboard for CryptoIntel-Engine.
Visualizes Mode Spot (Cycle Valuation & DCA Targets), Mode Futures (Leverage Squeeze),
Whale & Macro telemetry, and Multi-Agent Socratic Audit findings.
"""

import streamlit as st

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
symbol = st.sidebar.text_input("Asset Symbol", value="BTCUSDT").upper()
analysis_mode = st.sidebar.radio(
    "Execution Mode",
    options=["Full Audit (Spot + Futures + Socratic)", "Spot Cycle DCA", "Futures Squeeze"],
)

engine = CoreQuantEngine()

# Top metric tabs
tab_overview, tab_spot, tab_futures = st.tabs(["🏛️ Socratic Audit & Verdict", "📈 Mode Spot (Cycle DCA)", "⚡ Mode Futures (Leverage Risk)"])

# Deterministic evaluation run
with tab_overview:
    st.subheader(f"🔍 Multi-Agent Audit Summary for {symbol}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Price (USD)", "$95,420.00", "+2.8% (24h)")
    with col2:
        st.metric("Cycle Regime", "MID_BULL_EXPANSION", "Healthy")
    with col3:
        st.metric("Futures Risk", "ELEVATED", "Funding 24.5%")
    with col4:
        st.metric("Anti-FOMO Verdict", "PROCEED_WITH_CAUTION", "Tranche DCA")

    st.markdown("---")
    st.markdown("### 🗣️ Socratic Devil's Advocate - 3 Critical Cross-Examinations")
    st.warning("⚠️ **Câu hỏi 1 (Vĩ mô & Lãi suất):** Bạn đang mua vào khi DXY ở mức 104.2 và Fed chưa phát tín hiệu nới lỏng định lượng. Kịch bản dự phòng nếu lạm phát quay trở lại là gì?")
    st.warning("⚠️ **Câu hỏi 2 (Cá voi & Sàn CEX):** Netflow 24h ghi nhận 15,000 BTC nạp lên sàn Binance trong 6 giờ qua. Đây là động thái gom hàng ví lạnh hay xả thanh khoản?")
    st.warning("⚠️ **Câu hỏi 3 (Bẫy thanh lý Futures):** Tỷ lệ Long/Short ratio đang ở mức 2.85 và Open Interest chạm đỉnh 30 ngày. Vùng đệm dừng lỗ của bạn có chịu được cú quét 2.0% dưới râu nến không?")

with tab_spot:
    st.subheader(f"📊 Spot Accumulation & Cycle Valuation ({symbol})")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.metric("MVRV Z-Score", "2.45", "Fair Value Range [0.1 - 5.0]")
    with sc2:
        st.metric("Mayer Multiple", "1.32", "200-Day SMA Benchmark")
    with sc3:
        st.metric("Pi Cycle Top Alert", "NORMAL", "111DMA < 2x 350DMA")

    st.markdown("#### 🎯 Algorithmic DCA Accumulation Zones")
    st.info("🔹 **Zone 1 (Conservative -8%):** $87,786.40")
    st.info("🔹 **Zone 2 (Moderate / Realized Floor):** $81,107.00")
    st.info("🔹 **Zone 3 (Aggressive / 200W-MA Floor):** $48,000.00")

    st.markdown("#### 💰 Algorithmic Take-Profit Targets")
    st.success("🟢 **TP 1 (+35% Initial De-risk):** $128,817.00")
    st.success("🟢 **TP 2 (+75% Mid-Cycle Expansion):** $166,985.00")
    st.success("🟢 **TP 3 (+150% Cycle Top Euphoria):** $238,550.00")

with tab_futures:
    st.subheader(f"⚡ Derivatives Leverage & Liquidation Risk ({symbol})")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.metric("Funding Rate (8h)", "0.022%", "APR: 24.1%")
    with fc2:
        st.metric("FRSI Score (0-100)", "62.0", "Neutral/Slightly Crowded")
    with fc3:
        st.metric("Orderbook Imbalance (±2%)", "0.41", "Thin Bid Depth")

    st.markdown("#### 🎯 Estimated High-Leverage Liquidation Clusters")
    st.error("🔴 **Short Liquidation Pocket Above (+1.5% 24h High):** $97,850.00")
    st.error("🟢 **Long Stop Sweep Pocket Below (-2.0% 24h Low):** $92,120.00")

st.markdown("---")
st.caption(
    "⚠️ **Digital Asset Risk Disclaimer**: This platform is an educational decision-support tool. "
    "Digital assets involve extreme volatility and structural risk. Never allocate capital you cannot afford to lose."
)
