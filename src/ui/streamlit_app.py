"""
Streamlit Web Dashboard for CryptoIntel-Engine.
Simplified, clean, and professional FinTech Decision-Support Copilot & Quantitative Trading Hub.
Features:
- Streamlined Full-Width UI (No Cluttered Sidebar)
- Live Binance Public API Integration (Real-Time Price & Funding Rate)
- Algorithmic Spot DCA Accumulation & Take-Profit Targets
- Multi-Symbol Automated Quantitative Trading Bot (BTC, ETH, SOL)
- 24/7 GitHub Actions & Headless Cloud Runner
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
    run_single_tick_for_symbols,
    trading_bot_coordinator,
)
from src.ingestion.binance_client import BinancePublicClient

# Page Configuration - Full Width, Sidebar Hidden
st.set_page_config(
    page_title="CryptoIntel-Engine | Trợ Lý Định Lượng & Bot Tự Động",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Styling for Professional FinTech Look - Hide Sidebar Completely
st.markdown(
    """
    <style>
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 98% !important;
    }
    .brand-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px 22px;
        margin-bottom: 14px;
    }
    .brand-title {
        font-size: 1.55rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
    }
    .brand-subtitle {
        font-size: 0.88rem;
        color: #94a3b8;
        margin-top: 4px;
        margin-bottom: 0;
    }
    .ci-control-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 16px;
    }
    .ci-metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 16px;
        text-align: left;
    }
    .ci-metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 500;
        margin-bottom: 3px;
    }
    .ci-metric-val {
        font-size: 1.35rem;
        font-weight: 700;
        color: #f8fafc;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .ci-metric-sub {
        font-size: 0.75rem;
        color: #38bdf8;
        margin-top: 2px;
    }
    .verdict-red {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.18) 0%, rgba(153, 27, 27, 0.28) 100%);
        border: 1px solid #ef4444;
        border-radius: 10px;
        padding: 14px 18px;
        color: #fca5a5;
        margin-bottom: 14px;
    }
    .verdict-yellow {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.18) 0%, rgba(180, 83, 9, 0.28) 100%);
        border: 1px solid #f59e0b;
        border-radius: 10px;
        padding: 14px 18px;
        color: #fde68a;
        margin-bottom: 14px;
    }
    .verdict-green {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(4, 120, 87, 0.28) 100%);
        border: 1px solid #10b981;
        border-radius: 10px;
        padding: 14px 18px;
        color: #a7f3d0;
        margin-bottom: 14px;
    }
    .socratic-card {
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid #38bdf8;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 10px;
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


# --- Top Header ---
st.markdown(
    """
    <div class="brand-header">
        <div class="brand-title">🛡️ CryptoIntel-Engine | Trợ Lý Định Lượng & Bot Giao Dịch Tự Động</div>
        <div class="brand-subtitle">
            Toán học định lượng không ảo giác • Quản trị rủi ro cố định 1.5% • Đa tài sản BTC/ETH/SOL • Chạy ngầm 24/7
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Top Analysis Bar (Main Screen, No Cluttered Sidebar) ---
with st.container():
    c_sym, c_goal, c_entry, c_btn = st.columns([1.5, 2.5, 1.3, 1.4])
    with c_sym:
        preset_symbol = st.selectbox(
            "🪙 Chọn Coin Thẩm Định:",
            options=["BTCUSDT (Bitcoin)", "ETHUSDT (Ethereum)", "SOLUSDT (Solana)"],
            index=0,
        )
        selected_symbol = preset_symbol.split(" ")[0]
    with c_goal:
        proposed_intent = st.selectbox(
            "🎯 Mục Đích Thẩm Định:",
            options=[
                "BUY_SPOT_DCA (Mua tích sản dài hạn)",
                "LONG_LEVERAGE (Mở Long đòn bẩy ngắn hạn)",
                "SHORT_HEDGE (Mở Short phòng hộ / lướt sóng)",
                "DUAL_AUDIT (Toàn diện Spot + Futures + Chống FOMO)",
            ],
            index=0,
        )
        action_code = proposed_intent.split(" ")[0]
        exec_mode = (
            "MODE_SPOT"
            if "SPOT" in action_code
            else (
                "MODE_FUTURES"
                if "LEVERAGE" in action_code or "SHORT" in action_code
                else "DUAL_AUDIT"
            )
        )
    with c_entry:
        entry_override = st.number_input(
            "💵 Giá Dự Kiến ($):",
            min_value=0.0,
            value=0.0,
            step=50.0,
            help="Để 0 = Sử dụng giá thị trường Binance trực tiếp",
        )
    with c_btn:
        st.write("")
        st.write("")
        run_button = st.button("🔍 Thẩm Định Ngay", type="primary", use_container_width=True)

# Auto-initialize session state if first visit or trigger
if "quant_audit" not in st.session_state or run_button:
    with st.spinner(f"Đang kết nối Binance & thẩm định định lượng cho {selected_symbol}..."):
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

# Status Feed Pill
feed_label = "🟢 Dữ liệu Thời gian thực (Binance Public API)" if is_live_feed else "🟠 Dữ liệu Tham chiếu Chuẩn hóa (Offline Baseline)"
st.caption(f"Trạng thái nguồn cấp cho {active_symbol}: **{feed_label}**")

# --- 4 Clean Dedicated Tabs ---
tab_bot, tab_plan, tab_cloud, tab_accounting = st.tabs([
    "🤖 1. Bot Tự Động & Forward-Test",
    "🛡️ 2. Thẩm Định Rủi Ro & Kế Hoạch DCA",
    "☁️ 3. Treo Bot 24/7 (GitHub Actions)",
    "📒 4. Quản Trị Danh Mục (Thông Tư 200)",
])

# ==================== TAB 1: AUTOMATED TRADING BOT ====================
with tab_bot:
    st.markdown("#### 🤖 Trung Tâm Bot Định Lượng (Quantitative Multi-Symbol Trading)")
    st.caption(
        "Kỷ luật giao dịch cơ học không cảm xúc: Quản trị rủi ro 1.5% vốn/lệnh • "
        "Tỷ lệ R:R $\\ge 1:2.0$ • Đệm ATR chống quét râu • Tự động dời SL về hòa vốn khi chạy được 1R."
    )

    st.info(
        "💾 **Dữ liệu được lưu trữ tự động**: Mọi vị thế mở, lịch sử lệnh và tỷ lệ thắng được lưu tại "
        "`data/paper_trading_state.json`. Khi bạn tắt máy, đóng terminal hay restart, toàn bộ số dư và "
        "winrate được bảo lưu 100%."
    )

    # Multi-Symbol Configuration
    selected_bot_coins = st.multiselect(
        "🪙 Danh mục Coin quét & giao dịch song song (1 - 3 coin cùng lúc):",
        ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        default=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        help="Bot sẽ đồng thời quét tín hiệu, mở vị thế và quản trị rủi ro 1.5% độc lập cho từng coin.",
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
        target_coins = selected_bot_coins if selected_bot_coins else [active_symbol]
        with st.spinner(f"Bot đang quét tín hiệu trực tiếp cho {target_coins}..."):
            tick_summary = asyncio.run(
                run_single_tick_for_symbols(
                    symbols=target_coins,
                    quant_engine=CoreQuantEngine(),
                    client=BinancePublicClient(),
                )
            )
            total_new = sum(d.get("new_orders", 0) for d in tick_summary.values() if isinstance(d, dict))
            total_closed = sum(d.get("closed", 0) for d in tick_summary.values() if isinstance(d, dict))
            coins_str = ", ".join(target_coins)
            if total_new > 0 or total_closed > 0:
                st.success(f"🚀 Hoàn tất quét {coins_str}: Đã mở {total_new} vị thế mới | Đã đóng {total_closed} vị thế!")
            else:
                st.info(f"ℹ️ Đã quét {coins_str}: Thị trường chưa có tín hiệu mới đạt chuẩn an toàn.")

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
        st.info("Hiện không có vị thế mở nào. Bấm '⚡ Quét & Khớp Lệnh' khi bot đang Bật để tìm tín hiệu.")

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


# ==================== TAB 2: RISK AUDIT & DCA PLAN ====================
with tab_plan:
    st.markdown(f"#### 🛡️ Thẩm Định Rủi Ro & Kế Hoạch DCA ({active_symbol})")

    # Traffic Light Hero Verdict
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

    # Metric Cards
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
                <div class="ci-metric-sub">24h High: ${futures_data.high_24h:,.2f}</div>
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

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Explicit DCA Order Matrix Table
    st.markdown("##### 📥 Kế Hoạch Đặt Lệnh Chờ Mua Gom (Limit DCA Order Matrix)")
    dca_table = [
        {
            "Lệnh": "Limit 1 (Thăm dò / Retest ngắn hạn)",
            "Mức Giá Đặt": f"${spot_data.dca_zone_conservative:,.2f}",
            "Tỷ Trọng Vốn": "25% Vốn DCA",
            "Cơ Sở Định Lượng": "Chiết khấu -8% từ giá thị trường, kiểm tra lực cầu hỗ trợ gần nhất",
            "Trạng Thái": "Chờ khớp",
        },
        {
            "Lệnh": "Limit 2 (Tích lũy chiến lược)",
            "Mức Giá Đặt": f"${spot_data.dca_zone_moderate:,.2f}",
            "Tỷ Trọng Vốn": "40% Vốn DCA",
            "Cơ Sở Định Lượng": "Vùng Realized Price toàn mạng lưới (Giá vốn bình quân on-chain)",
            "Trạng Thái": "Chờ khớp",
        },
        {
            "Lệnh": "Limit 3 (Bắt đáy đại chu kỳ)",
            "Mức Giá Đặt": f"${spot_data.dca_zone_aggressive:,.2f}",
            "Tỷ Trọng Vốn": "35% Vốn DCA",
            "Cơ Sở Định Lượng": "Đường trung bình 200 tuần (200W-MA) - Sàn cứng lịch sử chưa từng thủng",
            "Trạng Thái": "Chờ khớp",
        },
    ]
    st.dataframe(dca_table, use_container_width=True, hide_index=True)

    col_dca_left, col_dca_right = st.columns(2)
    with col_dca_left:
        st.markdown("##### 🎯 Mục Tiêu Chốt Lời (Take-Profit Targets)")
        st.success(
            f"🟢 **Mục tiêu 1 (+35% Lợi nhuận):** **${spot_data.take_profit_target_1:,.2f}**  \n"
            f"*(Thu hồi vốn ban đầu để đưa tài khoản về vị thế an toàn tuyệt đối)*"
        )
        st.success(
            f"🟢 **Mục tiêu 2 (+75% Lợi nhuận):** **${spot_data.take_profit_target_2:,.2f}**  \n"
            f"*(Chốt lời giai đoạn tăng trưởng mở rộng của chu kỳ)*"
        )
        st.success(
            f"🟢 **Mục tiêu 3 (+150% Lợi nhuận):** **${spot_data.take_profit_target_3:,.2f}**  \n"
            f"*(Chốt lời đỉnh hưng phấn chu kỳ - Tuyệt đối không giữ thêm)*"
        )

    with col_dca_right:
        st.markdown("##### 🗣️ Phản Biện Socratic Devil's Advocate")
        fatal_questions = audit_state.get("fatal_socratic_questions", [])
        if fatal_questions:
            for idx, q in enumerate(fatal_questions[:2], 1):
                st.markdown(
                    f"""
                    <div class="socratic-card">
                        <b style="color: #38bdf8;">❓ Câu hỏi chất vấn {idx}:</b><br/>
                        <span style="font-size: 0.95rem; color: #f1f5f9; line-height: 1.4;">{q}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Chưa ghi nhận câu hỏi phản biện cho kịch bản hiện tại.")

    # Futures Liquidation Chart
    st.markdown("##### ⚡ Bản Đồ Cụm Thanh Lý & Biên Độ Quét Râu Đòn Bẩy (Futures)")
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
        title=f"Bản Đồ Cụm Thanh Lý & Biên Độ Quét Râu ({active_symbol})",
        yaxis_title="Đơn Giá (USD)",
        template="plotly_dark",
        height=320,
        margin={"l": 40, "r": 40, "t": 50, "b": 40},
    )
    st.plotly_chart(fig, use_container_width=True)


# ==================== TAB 3: 24/7 CLOUD RUNNER ====================
with tab_cloud:
    st.markdown("#### ☁️ Treo Bot Tự Động 24/7 Khi Tắt Máy (Miễn Phí 0đ)")
    st.caption("Cơ chế tự động hóa đám mây giúp bot giao dịch liên tục mà không cần mở máy tính ở nhà.")

    cl_col1, cl_col2 = st.columns(2)
    with cl_col1:
        st.markdown("##### 🚀 Cách 1: GitHub Actions Cloud Runner (Khuyên Dùng)")
        st.markdown(
            """
            Hệ thống đã tích hợp sẵn workflow tự động: `.github/workflows/forward_test_runner.yml`.
            - **Cơ chế hoạt động:** Cứ mỗi **30 phút**, máy chủ của GitHub tự động thức dậy, kéo nến từ Binance cho cả 3 coin (`BTC`, `ETH`, `SOL`), khớp lệnh TP/SL, và tự động lưu trạng thái vào repo.
            - **Cách kích hoạt:**
              1. Đẩy code lên GitHub cá nhân của bạn (`git push origin main`).
              2. Truy cập tab **Actions** trên GitHub và thấy workflow **24/7 Automated Forward-Test Runner** đang chạy.
              3. Bạn có thể tắt máy tính đi ngủ, bot vẫn tự động giao dịch 24/7/365.
            """
        )
    with cl_col2:
        st.markdown("##### 💻 Cách 2: Headless Runner Trên Máy Tính (Gập màn hình)")
        st.markdown(
            """
            Nếu máy tính cắm sạc và chỉ tắt màn hình (Sleep: Never):
            - Mở PowerShell / Terminal và chạy lệnh nền:
              ```bash
              python -m src.execution.runner --symbols BTCUSDT,ETHUSDT,SOLUSDT --interval 60
              ```
            - Runner chạy ngầm không cần giao diện web, cứ **60 giây** quét một lần cho cả 3 coin và lưu thẳng vào ổ đĩa.
            """
        )


# ==================== TAB 4: TT 200 ACCOUNTING ====================
with tab_accounting:
    st.markdown("#### 📚 Bảng Cân Đối Danh Mục Theo Thông Tư 200/2014/TT-BTC")
    st.caption("Quản trị tài sản số minh bạch: Tách bạch rõ Lãi/Lỗ đã chốt (TK 515/635) và Quỹ dự phòng giảm giá (TK 2291).")

    prices = {
        "BTCUSDT": get_symbol_market_profile("BTCUSDT")["current_price"],
        "ETHUSDT": get_symbol_market_profile("ETHUSDT")["current_price"],
        "SOLUSDT": get_symbol_market_profile("SOLUSDT")["current_price"],
    }
    prices[active_symbol] = spot_data.current_price

    bs = accounting_ledger.evaluate_portfolio(prices)

    a1, a2, a3, a4 = st.columns(4)
    with a1:
        st.metric("Tổng Giá Gốc (TK 121)", f"${bs.trading_assets_book_value_usd:,.2f}")
    with a2:
        st.metric("Giá Trị Thị Trường (Fair Value)", f"${bs.total_market_value_usd:,.2f}")
    with a3:
        st.metric("Quỹ Dự Phòng Giảm Giá (TK 2291)", f"${bs.total_impairment_provision_usd:,.2f}")
    with a4:
        st.metric("Lãi/Lỗ Đã Thực Hiện (Realized)", f"${bs.cumulative_realized_pnl_usd:+,.2f}")

    # Circular 200 Manual Transaction Booking Form
    with st.expander("📝 Ghi Nhận Giao Dịch Mua/Bán Thủ Công (Hạch toán TT 200)"):
        with st.form("manual_tx_form", clear_on_submit=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                f_symbol = st.selectbox("Mã Coin", ["BTCUSDT", "ETHUSDT", "SOLUSDT"], index=0)
                f_action = st.selectbox("Loại Giao Dịch", ["BUY (Mua vào - TK 121)", "SELL (Bán ra - FIFO)"], index=0)
            with col_f2:
                f_qty = st.number_input("Số lượng", min_value=0.0001, value=0.05, step=0.01)
                f_price = st.number_input("Đơn giá khớp ($)", min_value=0.1, value=float(spot_data.current_price), step=100.0)
            with col_f3:
                f_fee = st.number_input("Phí giao dịch ($)", min_value=0.0, value=1.5, step=0.5)
                f_submit = st.form_submit_button("💾 Hạch Toán Ngay", use_container_width=True)

        if f_submit:
            act_type = TransactionType.BUY if "BUY" in f_action else TransactionType.SELL
            tx = CryptoTransaction(
                tx_id=f"tx_{int(datetime.now(UTC).timestamp())}",
                timestamp=datetime.now(UTC),
                symbol=f_symbol,
                account=TT200AccountCode.TK_121,
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

# --- Footer Disclaimer ---
st.markdown("---")
st.caption(
    "⚠️ **Khuyến cáo rủi ro tài sản số (Digital Asset Risk Disclaimer)**: "
    "Hệ thống là công cụ hỗ trợ ra quyết định và kiểm soát tâm lý, không phải lời khuyên đầu tư tài chính. "
    "Thị trường tài sản số biến động rất mạnh, tuyệt đối không bao giờ mạo hiểm số vốn bạn không thể chấp nhận mất."
)
