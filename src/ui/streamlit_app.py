"""
Streamlit Web Dashboard for CryptoIntel-Engine.
Visualizes Mode Spot (Cycle Valuation & DCA Targets), Mode Futures (Leverage Squeeze & Liquidation Clusters),
Multi-Agent Socratic Risk Audit, and Circular 200/2014/TT-BTC Accounting & Impairment Balance Sheet.
"""

import asyncio
from datetime import UTC, datetime

import plotly.graph_objects as go
import streamlit as st

from src.agents.graph import run_crypto_audit
from src.api.main import accounting_ledger
from src.engine.accounting_tt200 import (
    CryptoTransaction,
    TransactionType,
    TT200AccountCode,
)
from src.engine.core_quant import CoreQuantEngine, get_symbol_market_profile

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
proposed_entry_input = st.sidebar.number_input(
    "Proposed Entry Price ($)", min_value=0.0, value=0.0, step=100.0
)
time_horizon = st.sidebar.slider("Investment Horizon (Days)", min_value=1, max_value=365, value=30)

run_audit_btn = st.sidebar.button("🚀 Chạy Thẩm định Rủi ro", type="primary")

# Execute audit when requested
if run_audit_btn:
    profile = get_symbol_market_profile(symbol)
    entry_price = proposed_entry_input if proposed_entry_input > 0.0 else profile["current_price"]

    engine = CoreQuantEngine()
    quant_audit = engine.run_full_quant_audit(
        symbol=symbol,
        current_price=profile["current_price"],
        market_cap=profile["market_cap"],
        realized_cap=profile["realized_cap"],
        std_market_cap=profile["std_market_cap"],
        sma_200d=profile["sma_200d"],
        sma_200w=profile["sma_200w"],
        sma_111d=profile["sma_111d"],
        sma_350d=profile["sma_350d"],
        open_interest_usd=profile["open_interest_usd"],
        oi_24h_ago=profile["oi_24h_ago"],
        circulating_supply=profile["circulating_supply"],
        total_supply=profile["total_supply"],
        fdv_usd=profile["fdv_usd"],
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

    with st.spinner(f"Hội đồng AI đang thẩm định {symbol}..."):
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

    st.session_state["quant_audit"] = quant_audit
    st.session_state["audit_state"] = audit_state
    st.session_state["profile"] = profile

if "audit_state" not in st.session_state:
    st.info(
        "👋 **Chào mừng bạn đến với CryptoIntel-Engine!**\n\n"
        "Hệ thống thẩm định độc lập kết hợp toán học lượng hóa không ảo giác (Zero LLM Arithmetic) "
        "và hội đồng tác tử phản biện Socratic Devil's Advocate.\n\n"
        "👉 *Vui lòng chọn tài sản ở menu bên trái và nhấn **🚀 Chạy Thẩm định Rủi ro** để bắt đầu.*"
    )
    st.stop()

quant_audit = st.session_state["quant_audit"]
audit_state = st.session_state["audit_state"]
profile = st.session_state.get("profile", {})
spot_data = quant_audit["spot"]
futures_data = quant_audit["futures"]
whale_data = quant_audit["whale"]

if not profile.get("is_calibrated", True):
    st.warning("⚠️ **Ghi chú:** Đang sử dụng mô hình tham chiếu chuẩn hóa cho tài sản này.")

tab_overview, tab_spot, tab_futures, tab_accounting = st.tabs([
    "🏛️ Socratic Audit & Verdict",
    "📈 Mode Spot (Cycle DCA)",
    "⚡ Mode Futures (Leverage Risk)",
    "📚 Bảng Cân Đối TT 200/2014/TT-BTC",
])

with tab_overview:
    st.subheader(f"🔍 Multi-Agent Audit Summary for {symbol}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Price (USD)", f"${spot_data.current_price:,.2f}")
    with col2:
        st.metric("Cycle Regime", spot_data.cycle_regime.value)
    with col3:
        st.metric(
            "Futures Risk",
            futures_data.futures_risk_level.value,
            f"APR {futures_data.annualized_funding_rate:.1f}%",
        )
    with col4:
        st.metric(
            "Anti-FOMO Verdict",
            audit_state["anti_fomo_verdict"],
            f"FOMO {audit_state['fomo_index']}/100",
        )

    st.markdown("---")
    st.markdown("### 🗣️ Socratic Devil's Advocate - 3 Fatal Cross-Examinations")
    for idx, q in enumerate(audit_state.get("fatal_socratic_questions", []), 1):
        st.warning(f"⚠️ **Câu hỏi {idx}:** {q}")

    price_str = (
        f"${audit_state['worst_case_invalidation_price']:,.2f}"
        if audit_state["worst_case_invalidation_price"] >= 1.0
        else f"${audit_state['worst_case_invalidation_price']:,.6f}"
    )
    st.markdown(
        f"🛑 **Mức giá Vô hiệu hóa Tồi tệ nhất (Worst-Case Invalidation):** `{price_str}`"
    )

    st.markdown("### 🛡️ Luận Điểm Phản Bác Trọng Tâm")
    for refutation in audit_state.get("thesis_refutations", []):
        st.markdown(f"- 🔴 {refutation}")

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
        st.metric(
            "Funding Rate (8h)",
            f"{futures_data.current_funding_rate * 100:.3f}%",
            f"APR: {futures_data.annualized_funding_rate:.1f}%",
        )
    with fc2:
        st.metric("FRSI Score (0-100)", f"{futures_data.frsi_score:.1f}")
    with fc3:
        st.metric("Orderbook Imbalance (±2%)", f"{futures_data.orderbook_imbalance_ratio:.2f}")

    # Plotly Liquidation Pocket Chart
    fig = go.Figure()
    curr_p = futures_data.current_price
    fig.add_trace(
        go.Bar(
            name="Liquidation Risk Bands",
            x=["Liquidation Below (Long Stop)", "Current Price", "Liquidation Above (Short Stop)"],
            y=[futures_data.liquidation_pocket_below, curr_p, futures_data.liquidation_pocket_above],
            marker_color=["#2ecc71", "#3498db", "#e74c3c"],
        )
    )
    fig.update_layout(
        title=f"Bản Đồ Cụm Thanh Lý & Biên Độ Rủi Ro Đòn Bẩy ({symbol})",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🎯 Estimated High-Leverage Liquidation Clusters")
    st.error(
        f"🔴 **Short Liquidation Pocket Above (+1.5% 24h High):** ${futures_data.liquidation_pocket_above:,.2f}"
    )
    st.error(
        f"🟢 **Long Stop Sweep Pocket Below (-2.0% 24h Low):** ${futures_data.liquidation_pocket_below:,.2f}"
    )

with tab_accounting:
    st.subheader("📚 Bảng Cân Đối & Trích Lập Dự Phòng (Thông tư 200/2014/TT-BTC)")
    st.caption("Quản trị danh mục có kiểm toán: Phân tách Realized PnL (TK 515/635) vs Unrealized PnL (TK 412).")

    # Evaluate current ledger with accurate mark prices
    prices = {
        "BTCUSDT": get_symbol_market_profile("BTCUSDT")["current_price"],
        "ETHUSDT": get_symbol_market_profile("ETHUSDT")["current_price"],
        "SOLUSDT": get_symbol_market_profile("SOLUSDT")["current_price"],
    }
    prices[symbol] = spot_data.current_price
    balance_sheet = accounting_ledger.evaluate_portfolio(prices)

    bc1, bc2, bc3, bc4 = st.columns(4)
    with bc1:
        st.metric("Tiền gửi & Tương đương (TK 112)", f"${balance_sheet.cash_balance_usd:,.2f}")
    with bc2:
        st.metric("Tài sản kinh doanh (TK 121)", f"${balance_sheet.trading_assets_book_value_usd:,.2f}")
    with bc3:
        st.metric("Đầu tư dài hạn ví lạnh (TK 228)", f"${balance_sheet.strategic_assets_book_value_usd:,.2f}")
    with bc4:
        st.metric(
            "Dự phòng giảm giá (TK 2291)",
            f"${balance_sheet.total_impairment_provision_usd:,.2f}",
            help="Trích lập dự phòng khi Giá thị trường < Giá gốc ghi sổ",
        )

    pnl1, pnl2, pnl3 = st.columns(3)
    with pnl1:
        st.metric("Lãi/Lỗ Đã Thực Hiện (TK 515/635)", f"${balance_sheet.cumulative_realized_pnl_usd:,.2f}")
    with pnl2:
        st.metric("Chênh lệch Đánh giá lại (TK 412)", f"${balance_sheet.unrealized_revaluation_usd:,.2f}")
    with pnl3:
        st.metric("Tổng Giá Trị Tài Sản Ròng (NAV)", f"${balance_sheet.net_asset_value_usd:,.2f}")

    st.markdown("#### 📋 Chi Tiết Danh Mục & Trạng Thái Trích Lập Dự Phòng (Impairment)")
    table_rows = []
    for pos in balance_sheet.positions:
        table_rows.append({
            "Tài sản": pos.symbol,
            "Tài khoản TT200": pos.account.value,
            "Số lượng": f"{pos.total_quantity:.4f}",
            "Giá gốc bình quân": f"${pos.average_unit_cost_usd:,.2f}",
            "Giá thị trường": f"${pos.current_mark_price_usd:,.2f}",
            "Giá trị ghi sổ": f"${pos.total_book_value_usd:,.2f}",
            "Giá trị thị trường": f"${pos.market_value_usd:,.2f}",
            "Dự phòng TK 2291": f"${pos.impairment_provision_required_usd:,.2f}",
            "Tình trạng": "⚠️ Cần trích lập" if pos.is_impaired else "✅ An toàn",
        })
    if table_rows:
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.info("Chưa có vị thế nắm giữ nào trong danh mục.")

    # Form to add demo trade
    with (
        st.expander("📝 Ghi Nhận Giao Dịch Mới (Phiếu Mua/Bán Theo Chuẩn TT 200)"),
        st.form("trade_form"),
    ):
        f_symbol = st.selectbox("Mã tài sản", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        f_acc = st.selectbox("Tài khoản kế toán", ["TK_121 (Lướt sóng)", "TK_228 (Ví lạnh tích sản)"])
        f_action = st.selectbox("Loại giao dịch", ["BUY", "SELL"])
        f_qty = st.number_input("Số lượng", min_value=0.0001, value=0.5, step=0.01)
        default_price = get_symbol_market_profile(f_symbol)["current_price"]
        f_price = st.number_input("Đơn giá khớp lệnh ($)", min_value=0.1, value=default_price)
        f_fee = st.number_input("Phí giao dịch ($)", min_value=0.0, value=5.0)
        submitted = st.form_submit_button("Hạch Toán Giao Dịch")

        if submitted:
            acc_code = TT200AccountCode.TK_121 if "121" in f_acc else TT200AccountCode.TK_228
            act_type = TransactionType.BUY if f_action == "BUY" else TransactionType.SELL
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
                st.success(f"✅ Đã ghi nhận giao dịch {f_action} {f_qty} {f_symbol} thành công!")
                st.rerun()
            except ValueError as err:
                st.error(f"❌ Lỗi hạch toán: {err}")

st.markdown("---")
st.caption(
    "⚠️ **Digital Asset Risk Disclaimer**: This platform is an educational decision-support tool. "
    "Digital assets involve extreme volatility and structural risk. Never allocate capital you cannot afford to lose."
)
