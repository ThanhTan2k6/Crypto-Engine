"""
Streamlit Web Dashboard for CryptoIntel-Engine.
Simplified, clean, and professional FinTech Decision-Support Copilot.
Features:
- Live Binance Public API Integration (Real-Time Price & Funding Rate)
- Socratic Devil's Advocate Anti-FOMO Traffic Light Verdict tailored to Spot vs Futures
- Algorithmic Spot DCA Accumulation & Take-Profit Targets
- Real-time Futures Leverage Squeeze & Liquidation Pocket Visuals
- Vietnamese Circular 200/2014/TT-BTC Accounting & Impairment Balance Sheet
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
import plotly.graph_objects as go
import streamlit as st

from src.agents.graph import run_crypto_audit
from src.agents.state import CryptoIntelState
from src.engine.accounting_tt200 import (
    CryptoTransaction,
    TransactionType,
    TT200AccountCode,
    accounting_ledger,
)
from src.engine.core_quant import CoreQuantEngine, get_symbol_market_profile
from src.execution import (
    BotMode,
    HistoricalBacktester,
    SignalDirection,
    trading_bot_coordinator,
)
from src.ingestion.binance_client import BinancePublicClient

# Page Configuration
st.set_page_config(
    page_title="CryptoIntel-Engine | Trợ Lý Thẩm Định Rủi Ro & Chống FOMO",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for Professional FinTech Look
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .brand-header {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 16px;
    }
    .brand-title {
        font-size: 1.55rem;
        font-weight: 700;
        color: #f9fafb;
        margin: 0;
    }
    .brand-subtitle {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-top: 4px;
        margin-bottom: 0;
    }
    /* Metric Cards that never truncate */
    .ci-metric-card {
        background: rgba(31, 41, 55, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 14px 16px;
        text-align: left;
    }
    .ci-metric-label {
        font-size: 0.8rem;
        color: #9ca3af;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .ci-metric-val {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f9fafb;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .ci-metric-sub {
        font-size: 0.76rem;
        color: #60a5fa;
        margin-top: 3px;
    }
    /* Traffic Light Banners */
    .verdict-red {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.18) 0%, rgba(153, 27, 27, 0.28) 100%);
        border: 1px solid #ef4444;
        border-radius: 10px;
        padding: 16px 20px;
        color: #fca5a5;
        margin-bottom: 16px;
    }
    .verdict-yellow {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.18) 0%, rgba(180, 83, 9, 0.28) 100%);
        border: 1px solid #f59e0b;
        border-radius: 10px;
        padding: 16px 20px;
        color: #fde68a;
        margin-bottom: 16px;
    }
    .verdict-green {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(4, 120, 87, 0.28) 100%);
        border: 1px solid #10b981;
        border-radius: 10px;
        padding: 16px 20px;
        color: #a7f3d0;
        margin-bottom: 16px;
    }
    .socratic-card {
        background: rgba(30, 41, 59, 0.55);
        border-left: 4px solid #38bdf8;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


async def fetch_live_binance_data(symbol: str) -> dict[str, Any]:
    """Fetch live ticker and funding rate from public Binance endpoints."""
    try:
        client = BinancePublicClient(timeout_seconds=3.0)
        ticker = await client.get_futures_ticker_24h(symbol)
        funding = await client.get_funding_rate(symbol)
        depth = await client.get_orderbook_depth(symbol, limit=20)
        return {
            "current_price": ticker["last_price"],
            "high_24h": ticker["high_price_24h"],
            "low_24h": ticker["low_price_24h"],
            "funding_rate_8h": funding["funding_rate_8h"],
            "bids": depth["bids"],
            "asks": depth["asks"],
            "is_live": True,
        }
    except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError, httpx.HTTPError):
        return {"is_live": False}


def perform_quant_and_audit(
    symbol: str,
    analysis_mode: str,
    proposed_trade: str,
    proposed_entry: float,
    time_horizon: int,
) -> tuple[dict[str, Any], CryptoIntelState, dict[str, Any], bool]:
    """Helper to compute deterministic quant and multi-agent audit with live Binance data."""
    profile = get_symbol_market_profile(symbol)

    # Fetch live Binance data
    live_data = asyncio.run(fetch_live_binance_data(symbol))
    is_live = bool(live_data.get("is_live", False))

    current_px = float(live_data.get("current_price", profile["current_price"]))
    high_px = float(live_data.get("high_24h", current_px * 1.02))
    low_px = float(live_data.get("low_24h", current_px * 0.98))
    fr_8h = float(live_data.get("funding_rate_8h", 0.0001))
    bids = live_data.get("bids")
    asks = live_data.get("asks")

    circulating = float(profile["circulating_supply"])
    total_sup = float(profile["total_supply"])
    market_cap = current_px * circulating
    fdv = current_px * total_sup

    entry_price = proposed_entry if proposed_entry > 0.0 else current_px

    engine = CoreQuantEngine()
    quant_audit = engine.run_full_quant_audit(
        symbol=symbol,
        current_price=current_px,
        high_24h=high_px,
        low_24h=low_px,
        funding_rate_8h=fr_8h,
        bids=bids,
        asks=asks,
        market_cap=market_cap,
        realized_cap=profile["realized_cap"],
        std_market_cap=profile["std_market_cap"],
        sma_200d=profile["sma_200d"],
        sma_200w=profile["sma_200w"],
        sma_111d=profile["sma_111d"],
        sma_350d=profile["sma_350d"],
        open_interest_usd=profile["open_interest_usd"],
        oi_24h_ago=profile["oi_24h_ago"],
        circulating_supply=circulating,
        total_supply=total_sup,
        fdv_usd=fdv,
    )

    spot_dict = quant_audit["spot"].model_dump()
    futures_dict = quant_audit["futures"].model_dump()
    whale_dict = quant_audit["whale"].model_dump()
    etf_dict = quant_audit["etf"].model_dump()
    vesting_dict = quant_audit["vesting"].model_dump()

    whale_dict["exchange_netflow_24h_usd"] = whale_dict.get("netflow_24h_usd", 0.0)
    etf_dict["netflow_24h_usd"] = etf_dict.get("daily_net_inflow_usd", 0.0)
    vesting_dict["unlock_percent_of_circulating"] = vesting_dict.get(
        "next_unlock_pct_of_circulating", 0.0
    )

    audit_state = asyncio.run(
        run_crypto_audit(
            symbol=symbol,
            execution_mode=analysis_mode,
            spot_valuation_data=spot_dict,
            futures_squeeze_data=futures_dict,
            whale_flow_data=whale_dict,
            etf_flow_data=etf_dict,
            token_vesting_data=vesting_dict,
            proposed_action=proposed_trade,
            proposed_entry=entry_price,
            time_horizon_days=time_horizon,
        )
    )
    return quant_audit, audit_state, profile, is_live


# --- Top Brand Header ---
st.markdown(
    """
    <div class="brand-header">
        <div class="brand-title">🛡️ CryptoIntel-Engine | Trợ Lý Thẩm Định Rủi Ro & Chống FOMO</div>
        <div class="brand-subtitle">
            Toán học định lượng không ảo giác • Phản biện Socratic Devil's Advocate • Quản trị danh mục Thông tư 200
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Control Panel (Sidebar) ---
st.sidebar.markdown("### ⚙️ Thiết Lập Thẩm Định")

preset_symbol = st.sidebar.selectbox(
    "1. Chọn tài sản cần phân tích",
    options=["BTCUSDT (Bitcoin)", "ETHUSDT (Ethereum)", "SOLUSDT (Solana)", "Tùy chọn khác..."],
    index=0,
)

if "Tùy chọn khác" in preset_symbol:
    custom_input = st.sidebar.text_input("Nhập mã token (ví dụ: BNB, AVAX)", value="BNB").upper()
    selected_symbol = custom_input.replace("USDT", "") + "USDT"
else:
    selected_symbol = preset_symbol.split(" ")[0]

proposed_intent = st.sidebar.selectbox(
    "2. Kế hoạch / Tâm lý dự định vào lệnh",
    options=[
        "BUY_SPOT_DCA (Mua tích sản dài hạn)",
        "BUY_BREAKOUT (Mua đuổi theo nến tăng)",
        "LONG_LEVERAGE (Mở Long đòn bẩy)",
        "SHORT_HEDGE (Mở Short phòng hộ / lướt sóng)",
        "TAKE_PROFIT (Chốt lời từng phần)",
    ],
    index=0,
)
action_code = proposed_intent.split(" ")[0]

entry_override = st.sidebar.number_input(
    "3. Mức giá dự kiến khớp lệnh ($) (0 = Dùng giá thị trường)",
    min_value=0.0,
    value=0.0,
    step=50.0,
)

mode_choice = st.sidebar.radio(
    "4. Chế độ phân tích",
    options=["DUAL_AUDIT (Toàn diện Spot + Futures)", "MODE_SPOT (Tập trung Tích sản)", "MODE_FUTURES (Tập trung Đòn bẩy)"],
    index=0,
)
exec_mode = mode_choice.split(" ")[0]

run_button = st.sidebar.button("🚀 Chạy Thẩm Định Lại", type="primary", use_container_width=True)

# Auto-initialize session state if first visit or symbol changed
if "quant_audit" not in st.session_state or run_button:
    with st.spinner(f"Đang kết nối Binance & thẩm định rủi ro cho {selected_symbol}..."):
        q_audit, a_state, prof, live_status = perform_quant_and_audit(
            symbol=selected_symbol,
            analysis_mode=exec_mode,
            proposed_trade=action_code,
            proposed_entry=entry_override,
            time_horizon=30,
        )
        st.session_state["quant_audit"] = q_audit
        st.session_state["audit_state"] = a_state
        st.session_state["profile"] = prof
        st.session_state["active_symbol"] = selected_symbol
        st.session_state["is_live"] = live_status

quant_audit = st.session_state["quant_audit"]
audit_state = st.session_state["audit_state"]
profile = st.session_state["profile"]
active_symbol = st.session_state.get("active_symbol", selected_symbol)
is_live_feed = st.session_state.get("is_live", False)

spot_data = quant_audit["spot"]
futures_data = quant_audit["futures"]
whale_data = quant_audit["whale"]

# Status Pill
feed_label = "🟢 Dữ liệu Thời gian thực (Binance Public API)" if is_live_feed else "🟠 Dữ liệu Tham chiếu Chuẩn hóa (Offline Baseline)"
st.caption(f"Trạng thái nguồn cấp: **{feed_label}**")

# --- Traffic Light Hero Verdict ---
verdict = audit_state.get("anti_fomo_verdict", "PROCEED_WITH_CAUTION")
fomo_score = float(audit_state.get("fomo_index", 50.0))
invalidation_px = float(audit_state.get("worst_case_invalidation_price", spot_data.current_price * 0.95))
is_spot_plan = "SPOT" in action_code or "DCA" in action_code

if verdict == "REJECT_SETUP_TOO_RISKY":
    if is_spot_plan:
        title_text = "🔴 CẢNH BÁO ĐỎ: VÙNG GIÁ QUÁ CAO ĐỂ MUA GOM"
        body_text = (
            f"Thị trường đang ở vùng đỉnh chu kỳ (FOMO Index: {fomo_score:.1f}/100, MVRV: {spot_data.mvrv_zscore:.2f}). "
            f"Với chiến lược Tích sản (Spot DCA), KHÔNG NÊN mua ở vùng hưng phấn này mà hãy kiên nhẫn đợi giá chiết khấu về các vùng DCA sàn bên dưới."
        )
    else:
        title_text = "🔴 CẢNH BÁO ĐỎ: TỪ CHỐI SETUP - RỦI RO ĐÒN BẨY CỰC KỲ CAO"
        body_text = (
            f"Thị trường đang ở trạng thái rủi ro bất cân xứng (FOMO Index: {fomo_score:.1f}/100). "
            f"Tuyệt đối KHÔNG nên mở vị thế mua đuổi hoặc Long đòn bẩy ở vùng giá này do nguy cơ quét bẫy thanh lý hoặc điều chỉnh mạnh."
        )
    st.markdown(
        f"""
        <div class="verdict-red">
            <h3 style="margin: 0 0 6px 0; color: #ef4444;">{title_text}</h3>
            <b>Kết luận thẩm định:</b> {body_text}
        </div>
        """,
        unsafe_allow_html=True,
    )
elif verdict == "SCALE_IN_SPOT":
    st.markdown(
        f"""
        <div class="verdict-green">
            <h3 style="margin: 0 0 6px 0; color: #10b981;">🟢 TÍN HIỆU XANH: VÙNG TÍCH SẢN TỐT - CHIA VỐN MUA GOM</h3>
            <b>Kết luận thẩm định:</b> Định giá tài sản đang ở vùng tích lũy an toàn của chu kỳ (FOMO Index: {fomo_score:.1f}/100, MVRV: {spot_data.mvrv_zscore:.2f}).
            Phù hợp kế hoạch mua gom chia làm nhiều đợt (DCA). Tránh tất tay (All-in) trong một lệnh đơn lẻ.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    if is_spot_plan:
        title_text = "🟡 TÍN HIỆU VÀNG: ĐỊNH GIÁ HỢP LÝ - CHIA VỐN DCA THẬN TRỌNG"
        body_text = (
            f"Định giá MVRV ở mức cân bằng ({spot_data.mvrv_zscore:.2f}) với FOMO Index đạt {fomo_score:.1f}/100. "
            f"Bạn có thể kích hoạt kế hoạch Mua gom từng phần (DCA) theo 3 mức giá sàn bên dưới, không nên giải ngân 100% vốn ngay lập tức."
        )
    else:
        title_text = "🟡 CẢNH BÁO VÀNG: THẬN TRỌNG - CHỈ ĐI VỐN THĂM DÒ (10-20%)"
        body_text = (
            f"Tín hiệu thị trường đang giằng co và có rủi ro quét râu dừng lỗ (FOMO Index: {fomo_score:.1f}/100). "
            f"Nếu giải ngân, chỉ phân bổ tỷ trọng nhỏ, đặt dừng lỗ chặt chẽ tại vùng vô hiệu hóa kịch bản."
        )
    st.markdown(
        f"""
        <div class="verdict-yellow">
            <h3 style="margin: 0 0 6px 0; color: #f59e0b;">{title_text}</h3>
            <b>Kết luận thẩm định:</b> {body_text}
        </div>
        """,
        unsafe_allow_html=True,
    )

# Clean Metric Cards (No Truncation)
regime_map = {
    "CYCLE_BOTTOM_CAPITULATION": "Đáy Hoảng Loạn",
    "EARLY_ACCUMULATION": "Tích Lũy Sớm",
    "MID_BULL_EXPANSION": "Tăng Trưởng Giữa",
    "LATE_BULL_OVERHEATED": "Tăng Nóng Cuối",
    "CYCLE_TOP_EUPHORIA": "Đỉnh Hưng Phấn",
}
regime_vn = regime_map.get(spot_data.cycle_regime.value, spot_data.cycle_regime.value)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f"""
        <div class="ci-metric-card">
            <div class="ci-metric-label">Giá Thị Trường ({active_symbol})</div>
            <div class="ci-metric-val">${spot_data.current_price:,.2f}</div>
            <div class="ci-metric-sub">24h: ${quant_audit['futures'].current_price:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f"""
        <div class="ci-metric-card">
            <div class="ci-metric-label">Chỉ Số FOMO Index</div>
            <div class="ci-metric-val">{fomo_score:.1f} / 100</div>
            <div class="ci-metric-sub">{'Thấp (An toàn)' if fomo_score < 40 else ('Trung bình' if fomo_score < 70 else 'Cực cao')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f"""
        <div class="ci-metric-card">
            <div class="ci-metric-label">Chu Kỳ Định Giá Spot</div>
            <div class="ci-metric-val">{regime_vn}</div>
            <div class="ci-metric-sub">MVRV Z-Score: {spot_data.mvrv_zscore:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m4:
    floor_label = "Sàn Đỡ 200W-MA" if is_spot_plan else "Dừng Lỗ Kịch Bản"
    floor_val = spot_data.dca_zone_aggressive if is_spot_plan else invalidation_px
    st.markdown(
        f"""
        <div class="ci-metric-card">
            <div class="ci-metric-label">{floor_label}</div>
            <div class="ci-metric-val">${floor_val:,.2f}</div>
            <div class="ci-metric-sub">{'Vùng hỗ trợ chu kỳ' if is_spot_plan else 'Worst-case stop'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# --- 5 Concise Tabs (Never Truncated) ---
tab_socratic, tab_spot, tab_futures, tab_accounting, tab_bot = st.tabs([
    "🛡️ Phản Biện Socratic",
    "🎯 Vùng DCA & Chốt Lời",
    "⚡ Đòn Bẩy Futures",
    "💼 Sổ Cái TT 200",
    "🤖 Bot Tự Động (Auto-Trading)",
])

# ==================== TAB 1: SOCRATIC AUDIT ====================
with tab_socratic:
    st.markdown("#### 🗣️ 3 Câu Hỏi Chất Vấn Chí Mạng (Socratic Devil's Advocate)")
    st.caption("Hãy tự trả lời trung thực 3 câu hỏi dưới đây trước khi bạn bấm nút Mua/Bán trên sàn giao dịch.")

    fatal_questions = audit_state.get("fatal_socratic_questions", [])
    if fatal_questions:
        for idx, q in enumerate(fatal_questions, 1):
            st.markdown(
                f"""
                <div class="socratic-card">
                    <b style="color: #38bdf8;">❓ Câu hỏi chất vấn {idx}:</b><br/>
                    <span style="font-size: 1.0rem; color: #f1f5f9; line-height: 1.5;">{q}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Chưa ghi nhận câu hỏi phản biện cho kịch bản hiện tại.")

    st.markdown("#### 🚫 Luận Điểm Phản Bác & Cảnh Báo Tâm Lý")
    refutations = audit_state.get("thesis_refutations", [])
    if refutations:
        for r in refutations:
            st.markdown(f"• ⚠️ **Lưu ý rủi ro:** {r}")
    else:
        st.write("Không phát hiện tín hiệu bất thường nghiêm trọng.")

# ==================== TAB 2: SPOT DCA & TP ====================
with tab_spot:
    st.markdown(f"#### 🎯 Chiến Lược Tích Sản & Phân Bổ Vốn ({active_symbol})")
    st.caption("Các vùng giá được toán học định lượng tính sẵn dựa trên 200W-MA và Realized Price sàn chu kỳ.")

    col_dca, col_tp = st.columns(2)

    with col_dca:
        st.markdown("##### 📥 Vùng Giá Mua Gom (DCA Accumulation)")
        st.info(
            f"🔹 **Vùng 1 (Thận trọng - Tỷ trọng 25% vốn):**  \n"
            f"**${spot_data.dca_zone_conservative:,.2f}**  \n"
            f"*(Chiết khấu -8% từ giá thị trường, phù hợp đặt lệnh Limit đầu tiên)*"
        )
        st.info(
            f"🔹 **Vùng 2 (Vừa phải - Tỷ trọng 35% vốn):**  \n"
            f"**${spot_data.dca_zone_moderate:,.2f}**  \n"
            f"*(Vùng giá vốn Realized Price của toàn mạng lưới)*"
        )
        st.info(
            f"🔹 **Vùng 3 (Bắt đáy chu kỳ - Tỷ trọng 40% vốn):**  \n"
            f"**${spot_data.dca_zone_aggressive:,.2f}**  \n"
            f"*(Vùng sàn lịch sử 200-Tuần MA - Vùng gom tối ưu nhất)*"
        )

    with col_tp:
        st.markdown("##### 💰 Vùng Giá Chốt Lời Từng Phần (Take Profit)")
        st.success(
            f"🟢 **Mục tiêu 1 (+35% Lợi nhuận):**  \n"
            f"**${spot_data.take_profit_target_1:,.2f}**  \n"
            f"*(Thu hồi vốn ban đầu để đưa tài khoản về thế an toàn)*"
        )
        st.success(
            f"🟢 **Mục tiêu 2 (+75% Lợi nhuận):**  \n"
            f"**${spot_data.take_profit_target_2:,.2f}**  \n"
            f"*(Chốt lời giai đoạn tăng trưởng mở rộng chu kỳ)*"
        )
        st.success(
            f"🟢 **Mục tiêu 3 (+150% Lợi nhuận):**  \n"
            f"**${spot_data.take_profit_target_3:,.2f}**  \n"
            f"*(Chốt lời đỉnh hưng phấn chu kỳ - Tuyệt đối không giữ thêm)*"
        )

# ==================== TAB 3: FUTURES & LEVERAGE ====================
with tab_futures:
    st.markdown(f"#### ⚡ Áp Lực Đòn Bẩy & Cụm Dừng Lỗ Thanh Lý ({active_symbol})")

    f1, f2, f3 = st.columns(3)
    with f1:
        st.metric(
            "Funding Rate (8h)",
            f"{futures_data.current_funding_rate * 100:.4f}%",
            f"APR: {futures_data.annualized_funding_rate:.1f}%",
        )
    with f2:
        st.metric(
            "FRSI Score (0-100)",
            f"{futures_data.frsi_score:.1f}",
            help="> 75: Quá nóng (nguy cơ bẫy Long) | < 25: Quá nguội (nguy cơ Short squeeze)",
        )
    with f3:
        st.metric(
            "Mất Cân Đối Sổ Lệnh (±2%)",
            f"{futures_data.orderbook_imbalance_ratio:.2f}",
            help="Tỷ lệ thanh khoản Bid / (Bid + Ask) trong biên độ 2%",
        )

    # Plotly Liquidation Chart
    fig = go.Figure()
    curr_p = futures_data.current_price
    fig.add_trace(
        go.Bar(
            name="Biên Độ Thanh Lý",
            x=["Quét Dừng Lỗ Long (Bên Dưới)", "Giá Thị Trường Hiện Tại", "Quét Dừng Lỗ Short (Bên Trên)"],
            y=[futures_data.liquidation_pocket_below, curr_p, futures_data.liquidation_pocket_above],
            text=[
                f"${futures_data.liquidation_pocket_below:,.1f}",
                f"${curr_p:,.1f}",
                f"${futures_data.liquidation_pocket_above:,.1f}",
            ],
            textposition="auto",
            marker_color=["#10b981", "#3b82f6", "#ef4444"],
        )
    )
    fig.update_layout(
        title=f"Bản Đồ Cụm Thanh Lý & Biên Độ Quét Râu Đòn Bẩy ({active_symbol})",
        yaxis_title="Đơn Giá (USD)",
        template="plotly_dark",
        height=360,
        margin={"l": 40, "r": 40, "t": 50, "b": 40},
    )
    st.plotly_chart(fig, use_container_width=True)

    c_box1, c_box2 = st.columns(2)
    with c_box1:
        st.error(
            f"🔴 **Vùng Quét Stop-loss Short (Bên Trên):** ${futures_data.liquidation_pocket_above:,.2f}  \n"
            f"*Nếu mở vị thế Short, đặt điểm dừng lỗ an toàn cao hơn mức này để tránh bị quét râu.*"
        )
    with c_box2:
        st.error(
            f"🟢 **Vùng Quét Stop-loss Long (Bên Dưới):** ${futures_data.liquidation_pocket_below:,.2f}  \n"
            f"*Nếu mở vị thế Long, đặt điểm dừng lỗ sâu hơn mức này để không bị sàn săn thanh khoản.*"
        )

# ==================== TAB 4: TT 200 ACCOUNTING ====================
with tab_accounting:
    st.markdown("#### 📚 Bảng Cân Đối Danh Mục Theo Thông Tư 200/2014/TT-BTC")
    st.caption("Quản trị tài sản số chuyên nghiệp: Tách bạch rõ Lãi/Lỗ đã chốt (TK 515/635) và Quỹ dự phòng giảm giá (TK 2291).")

    # Evaluate current ledger
    prices = {
        "BTCUSDT": get_symbol_market_profile("BTCUSDT")["current_price"],
        "ETHUSDT": get_symbol_market_profile("ETHUSDT")["current_price"],
        "SOLUSDT": get_symbol_market_profile("SOLUSDT")["current_price"],
    }
    prices[active_symbol] = spot_data.current_price
    balance_sheet = accounting_ledger.evaluate_portfolio(prices)

    a1, a2, a3, a4 = st.columns(4)
    with a1:
        st.metric("Tiền Gửi Khả Dụng (TK 112)", f"${balance_sheet.cash_balance_usd:,.2f}")
    with a2:
        st.metric("Tài Sản Lướt Sóng (TK 121)", f"${balance_sheet.trading_assets_book_value_usd:,.2f}")
    with a3:
        st.metric("Tài Sản Ví Lạnh (TK 228)", f"${balance_sheet.strategic_assets_book_value_usd:,.2f}")
    with a4:
        st.metric(
            "Dự Phòng Giảm Giá (TK 2291)",
            f"${balance_sheet.total_impairment_provision_usd:,.2f}",
            help="Trích lập dự phòng theo TT 200: max(0, Giá trị ghi sổ - Giá trị thị trường)",
        )

    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Lãi/Lỗ Đã Thực Hiện (TK 515/635)", f"${balance_sheet.cumulative_realized_pnl_usd:,.2f}")
    with r2:
        st.metric("Chênh Lệch Đánh Giá Lại (TK 412)", f"${balance_sheet.unrealized_revaluation_usd:,.2f}")
    with r3:
        st.metric("Tổng Tài Sản Ròng (NAV)", f"${balance_sheet.net_asset_value_usd:,.2f}")

    st.markdown("##### 📋 Chi Tiết Danh Mục Đầu Tư")
    table_rows = []
    for pos in balance_sheet.positions:
        table_rows.append({
            "Tài sản": pos.symbol,
            "Tài khoản TT 200": "TK 121 (Lướt sóng)" if pos.account == TT200AccountCode.TK_121 else "TK 228 (Ví lạnh)",
            "Số lượng": f"{pos.total_quantity:.4f}",
            "Giá gốc bình quân (FIFO)": f"${pos.average_unit_cost_usd:,.2f}",
            "Giá thị trường": f"${pos.current_mark_price_usd:,.2f}",
            "Giá trị ghi sổ": f"${pos.total_book_value_usd:,.2f}",
            "Giá trị thị trường": f"${pos.market_value_usd:,.2f}",
            "Dự phòng TK 2291": f"${pos.impairment_provision_required_usd:,.2f}",
            "Trạng thái": "⚠️ Cần trích lập" if pos.is_impaired else "✅ An toàn",
        })

    if table_rows:
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("Hiện chưa có tài sản nào trong danh mục. Hãy nhập phiếu mua đầu tiên ở form bên dưới!")

    # Interactive Voucher Form
    with (
        st.expander("📝 Ghi Nhận Phiếu Giao Dịch Mua/Bán (Hạch Toán Chuẩn TT 200)"),
        st.form("quick_trade_voucher_form"),
    ):
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            f_symbol = st.selectbox("Mã tài sản", ["BTCUSDT", "ETHUSDT", "SOLUSDT"], index=0)
            f_acc = st.selectbox("Mục đích đầu tư", ["TK 228 (Ví lạnh tích sản)", "TK 121 (Lướt sóng ngắn hạn)"])
        with tc2:
            f_action = st.selectbox("Loại lệnh", ["BUY (Mua vào)", "SELL (Bán ra)"])
            f_qty = st.number_input("Số lượng coin", min_value=0.0001, value=0.1, step=0.05)
        with tc3:
            default_p = get_symbol_market_profile(f_symbol)["current_price"]
            f_price = st.number_input("Đơn giá khớp lệnh ($)", min_value=0.1, value=default_p)
            f_fee = st.number_input("Phí sàn ($)", min_value=0.0, value=2.0)

        submitted = st.form_submit_button("💾 Xác Nhận & Hạch Toán Vào Sổ Cái", type="primary")

        if submitted:
            acc_code = TT200AccountCode.TK_121 if "121" in f_acc else TT200AccountCode.TK_228
            act_type = TransactionType.BUY if "BUY" in f_action else TransactionType.SELL
            tx = CryptoTransaction(
                tx_id=f"tx_{int(datetime.now(UTC).timestamp())}",
                timestamp=datetime.now(UTC),
                symbol=f_symbol,
                account=acc_code,
                action=act_type,
                quantity=f_qty,
                price_usd=f_price,
                fee_usd=f_fee,
            )
            try:
                accounting_ledger.record_transaction(tx)
                st.success(f"✅ Đã hạch toán thành công lệnh {f_action.split(' ')[0]} {f_qty} {f_symbol}!")
                st.rerun()
            except ValueError as err:
                st.error(f"❌ Lỗi hạch toán: {err}")

# ==================== TAB 5: AUTOMATED TRADING BOT ====================
with tab_bot:
    st.markdown("#### 🤖 Bot Định Lượng Tự Động (Quantitative Auto-Trading Engine)")
    st.caption(
        "Kỷ luật giao dịch cơ học không tâm lý: Quản trị rủi ro 1.5% vốn/lệnh • "
        "Tỷ lệ R:R cố định 1:1.5 - 1:2.0 • Lọc rủi ro Socratic Veto • Tự động hạch toán Thông tư 200."
    )

    st.info(
        "💾 **Dữ liệu được lưu trữ tự động**: Mọi vị thế mở, lịch sử lệnh và tỷ lệ thắng được lưu tại "
        "`data/paper_trading_state.json`. Khi bạn tắt máy, đóng terminal hay restart, toàn bộ số dư và "
        "winrate được bảo lưu 100%."
    )

    # Bot Status & Control Row
    bc_col1, bc_col2, bc_col3, bc_col4, bc_col5 = st.columns([2, 1, 1, 1.5, 1.2])
    with bc_col1:
        st.markdown(
            f"Trạng thái: **{trading_bot_coordinator.status.value}** | Chế độ: **{trading_bot_coordinator.mode.value}**"
        )
    with bc_col2:
        if st.button("▶️ Khởi Động", type="primary", use_container_width=True):
            trading_bot_coordinator.start(mode=BotMode.PAPER_TRADING)
            st.rerun()
    with bc_col3:
        if st.button("⏹️ Dừng Bot", use_container_width=True):
            trading_bot_coordinator.stop()
            st.rerun()
    with bc_col4:
        trigger_tick = st.button("⚡ Quét & Khớp Lệnh", use_container_width=True)
    with bc_col5:
        if st.button("🔄 Đặt Lại Ví", use_container_width=True):
            trading_bot_coordinator.paper_engine.reset_account()
            st.rerun()

    if trigger_tick:
        with st.spinner("Bot đang quét tín hiệu và kiểm tra Socratic Veto..."):
            tick_res = asyncio.run(
                trading_bot_coordinator.evaluate_tick(
                    symbol=active_symbol,
                    current_price=spot_data.current_price,
                    quant_audit=quant_audit,
                    audit_state=audit_state,
                )
            )
            exec_orders = tick_res.get("executed_orders", [])
            vetoed = tick_res.get("vetoed_signals", [])
            if exec_orders:
                st.success(f"🚀 Bot đã mở {len(exec_orders)} lệnh mới thành công!")
            elif vetoed:
                st.warning(f"🛡️ Socratic Filter đã VETO chặn {len(vetoed)} lệnh có rủi ro bất cân xứng!")
            else:
                st.info(f"ℹ️ Không có tín hiệu mới hoặc trạng thái: {tick_res.get('action')}")

    # Telemetry Cards
    stats = trading_bot_coordinator.get_stats()
    b1, b2, b3, b4, b5 = st.columns(5)
    with b1:
        st.metric("Số Lệnh Đã Đóng", f"{stats.total_trades}")
    with b2:
        win_label = "✅ Đạt chuẩn (>51%)" if stats.win_rate_pct >= 51.0 else "Đang tích lũy mẫu"
        st.metric("Tỷ Lệ Thắng (Winrate)", f"{stats.win_rate_pct:.1f}%", win_label)
    with b3:
        st.metric("Hệ Số Lợi Nhuận (PF)", f"{stats.profit_factor:.2f}")
    with b4:
        st.metric("Kỳ Vọng Toán Học (EV)", f"{stats.expected_value_r:+.2f} R")
    with b5:
        st.metric("Số Dư Ví Paper", f"${stats.current_balance_usd:,.2f}", f"${stats.total_realized_pnl_usd:+,.2f}")

    # Active Positions Table
    st.markdown("##### 📌 Vị Thế Đang Mở (Open Positions)")
    active_pos = trading_bot_coordinator.get_active_positions()
    if active_pos:
        pos_rows = []
        for p in active_pos:
            unrealized = (
                (spot_data.current_price - p.entry_price) * p.quantity
                if p.direction == SignalDirection.BUY
                else (p.entry_price - spot_data.current_price) * p.quantity
            )
            pos_rows.append({
                "Mã": p.symbol,
                "Chiều": p.direction.value,
                "Chiến lược": p.strategy.value,
                "Khối lượng": f"{p.quantity:.4f}",
                "Giá vào": f"${p.entry_price:,.2f}",
                "Cắt lỗ (SL)": f"${p.stop_loss:,.2f}",
                "Chốt lời (TP)": f"${p.take_profit:,.2f}",
                "PnL Tạm Tính": f"${unrealized:+,.2f}",
            })
        st.dataframe(pos_rows, use_container_width=True, hide_index=True)
    else:
        st.info("Hiện không có vị thế mở nào. Bấm '⚡ Quét & Khớp Lệnh Ngay' khi bot đang Bật để tìm tín hiệu.")

    # Closed Trade History Table
    st.markdown("##### 📜 Lịch Sử Lệnh Đã Đóng (Closed Trades)")
    closed_trades = trading_bot_coordinator.get_trade_history()
    if closed_trades:
        hist_rows = []
        for t in reversed(closed_trades[-15:]):
            hist_rows.append({
                "Mã": t.symbol,
                "Chiều": t.direction.value,
                "Giá vào": f"${t.entry_price:,.2f}",
                "Giá đóng": f"${t.exit_price:,.2f}" if t.exit_price else "-",
                "Lý do đóng": t.exit_reason,
                "Lãi/Lỗ Ròng": f"${t.realized_pnl_usd:+,.2f}",
                "Kết quả": "🟢 THẮNG" if t.is_winner else "🔴 THUA",
            })
        st.dataframe(hist_rows, use_container_width=True, hide_index=True)
    else:
        st.write("Chưa có lịch sử lệnh nào hoàn tất.")

    # Expandable Logs
    with st.expander("📋 Nhật Ký Hoạt Động Của Bot (Activity Logs)"):
        logs = trading_bot_coordinator.activity_logs
        if logs:
            for item in reversed(logs[-15:]):
                st.caption(f"`{item['timestamp']}` - **[{item['event']}]** {item['message']}")
        else:
            st.caption("Chưa có sự kiện nào.")

    # Historical Backtest Section
    st.markdown("---")
    st.markdown("### 🧪 Khảo Sát Winrate Lịch Sử (Historical Backtesting)")
    st.caption(
        "Kiểm định tỷ lệ thắng (Winrate) và Lợi nhuận kỳ vọng (EV) ngay lập tức trên dữ liệu nến thật từ Binance "
        "mà không cần mở máy 24/7 hay chờ đợi nhiều tuần."
    )

    bk_c1, bk_c2, bk_c3, bk_c4 = st.columns([2, 1, 1, 2])
    with bk_c1:
        bk_strat = st.selectbox(
            "Chiến lược kiểm định",
            [
                "TREND_PULLBACK (Bám trend EMA50 R:R 1:2.0)",
                "COMBINED_QUANT (Tổng hợp Trend Pullback + Sweep)",
                "LIQUIDATION_SWEEP (Bắt râu đảo chiều biên độ)",
            ],
            index=0,
        )
    with bk_c2:
        bk_interval = st.selectbox("Khung nến", ["15m", "1h", "4h"], index=0)
    with bk_c3:
        bk_candles = st.selectbox("Số lượng nến", [100, 300, 500, 1000], index=3)
    with bk_c4:
        st.write("")
        run_bk_btn = st.button("⚡ Chạy Backtest Binance Ngay", type="primary", use_container_width=True)

    if run_bk_btn:
        strat_key = (
            "TREND_PULLBACK"
            if "TREND_PULLBACK" in bk_strat
            else "LIQUIDATION_SWEEP"
            if "LIQUIDATION_SWEEP" in bk_strat
            else "COMBINED_QUANT"
        )
        with st.spinner(f"Đang tải {bk_candles} nến {bk_interval} từ Binance và chạy mô phỏng toán học..."):
            tester = HistoricalBacktester()
            bk_res = asyncio.run(
                tester.run_backtest(
                    symbol=active_symbol,
                    interval=bk_interval,
                    candle_count=bk_candles,
                    strategy_mode=strat_key,
                )
            )

        res_c1, res_c2, res_c3, res_c4, res_c5 = st.columns(5)
        with res_c1:
            st.metric("Tổng Số Lệnh", f"{bk_res.total_trades}")
        with res_c2:
            st.metric(
                "Tỷ Lệ Thắng",
                f"{bk_res.win_rate_pct:.1f}%",
                f"{bk_res.winning_trades}W - {bk_res.losing_trades}L",
            )
        with res_c3:
            st.metric("Hệ Số Lợi Nhuận (PF)", f"{bk_res.profit_factor:.2f}")
        with res_c4:
            st.metric("Kỳ Vọng Toán Học (EV)", f"{bk_res.expected_value_r:+.2f} R")
        with res_c5:
            st.metric(
                "Lợi Nhuận / Sụt Giảm",
                f"${bk_res.total_pnl_usd:+,.2f}",
                f"Max DD: {bk_res.max_drawdown_pct:.1f}%",
            )

        if bk_res.trades:
            st.markdown("##### 📜 Chi Tiết Các Lệnh Đã Kiểm Định Trong Quá Khứ")
            bk_trade_rows = [
                {
                    "#": t.trade_id,
                    "Chiều": t.direction.value,
                    "Chiến lược": t.strategy,
                    "Giá vào": f"${t.entry_price:,.2f}",
                    "Giá thoát": f"${t.exit_price:,.2f}",
                    "Cắt lỗ (SL)": f"${t.stop_loss:,.2f}",
                    "Chốt lời (TP)": f"${t.take_profit:,.2f}",
                    "Kết quả": "🟢 THẮNG" if t.is_winner else "🔴 THUA",
                    "Lý do": t.exit_reason,
                    "PnL ($)": f"${t.pnl_usd:+,.2f}",
                }
                for t in reversed(bk_res.trades)
            ]
            st.dataframe(bk_trade_rows, use_container_width=True, hide_index=True)

# --- Footer Disclaimer ---
st.markdown("---")
st.caption(
    "⚠️ **Khuyến cáo rủi ro tài sản số (Digital Asset Risk Disclaimer)**: "
    "Hệ thống là công cụ hỗ trợ ra quyết định và kiểm soát tâm lý, không phải lời khuyên đầu tư tài chính. "
    "Thị trường tài sản số biến động rất mạnh, tuyệt đối không bao giờ mạo hiểm số vốn bạn không thể chấp nhận mất."
)
