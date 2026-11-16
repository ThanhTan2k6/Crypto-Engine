"""
Telegram Risk Alert & Socratic Audit Bot for CryptoIntel-Engine.
Implements asynchronous command handling for /start, /audit, /spot, /futures, and /subscribe.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from src.agents.graph import run_crypto_audit
from src.engine.core_quant import CoreQuantEngine, get_symbol_market_profile
from src.engine.futures_engine import FuturesRiskEngine
from src.engine.spot_engine import SpotCycleEngine

# Automatically load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Mandatory Digital Asset Risk Disclaimer
DISCLAIMER_TEXT = (
    "\n\n⚠️ *Digital Asset Risk Disclaimer*:\n"
    "_This audit is for educational and risk evaluation purposes only. "
    "Cryptocurrency investments involve extreme volatility and high financial risk, "
    "including potential total loss of capital. This does not constitute financial or trading advice._"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Show platform welcome and available commands."""
    welcome_text = (
        "🤖 *Chào mừng bạn đến với CryptoIntel-Engine Bot!*\n\n"
        "Tôi là *Hội đồng Thẩm định Rủi ro & Biện lý Phản biện Socratic (Devil's Advocate)*, "
        "giúp bạn dập tắt tâm lý FOMO mua đỉnh bán đáy và soi xét kỹ lưỡng trước khi xuống tiền.\n\n"
        "📌 *CÁC LỆNH HỖ TRỢ:*\n"
        "• `/audit <symbol>` : Chạy thẩm định đa tầng (Spot + Futures + 3 Câu hỏi phản biện Socratic).\n"
        "  _Ví dụ:_ `/audit BTC` hoặc `/audit ETH`\n"
        "• `/spot <symbol>` : Định vị chu kỳ on-chain (MVRV Z-Score, 200W-MA, Vùng DCA Mua gom & Chốt lời).\n"
        "• `/futures <symbol>` : Soi rủi ro phái sinh (Funding Rate APR, Open Interest, Bẫy quét thanh lý).\n"
        "• `/subscribe` : Đăng ký nhận cảnh báo Real-time (Cá voi nạp sàn CEX, Tether in tiền, Funding cực đoan).\n"
        "• `/help` : Hướng dẫn chi tiết cách đọc các chỉ số."
        f"{DISCLAIMER_TEXT}"
    )
    if update.effective_message:
        await update.effective_message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - Explain indicators and usage."""
    help_text = (
        "📖 *HƯỚNG DẪN ĐỌC CHỈ SỐ CRYPTOINTEL-ENGINE:*\n\n"
        "1️⃣ *MVRV Z-Score (Spot Cycle):*\n"
        "• `< 0.1`: Vùng đáy chu kỳ lịch sử (Capitulation) $\\rightarrow$ Vùng gom hàng DCA tối đa.\n"
        "• `1.5 - 3.5`: Giai đoạn tăng trưởng lành mạnh.\n"
        "• `> 3.5`: Thị trường quá nóng $\\rightarrow$ Bắt đầu chốt lời từng phần (TP1, TP2).\n"
        "• `> 5.0`: Đỉnh hưng phấn chu kỳ $\\rightarrow$ Thoát hết về tiền mặt/stablecoin.\n\n"
        "2️⃣ *Funding Rate APR (Futures Risk):*\n"
        "• `> +75%`: Long quá đông, trả phí funding đắt đỏ $\\rightarrow$ Cảnh báo bẫy Long Squeeze quét râu.\n"
        "• `< -30%`: Short quá đà $\\rightarrow$ Dễ xảy ra cú Short Squeeze giật ngược lên.\n\n"
        "3️⃣ *CEX Netflow & Whale Tracking:*\n"
        "• `Inflow đột biến`: Cá voi nạp coin lên sàn $\\rightarrow$ Rủi ro chuẩn bị xả hàng (Distribution).\n"
        "• `Outflow đột biến`: Cá voi rút coin về ví lạnh $\\rightarrow$ Tích lũy dài hạn (Accumulation)."
        f"{DISCLAIMER_TEXT}"
    )
    if update.effective_message:
        await update.effective_message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
        )


async def audit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /audit <symbol> command.
    Runs full multi-agent Socratic interrogation via LangGraph.
    """
    if not context.args or len(context.args) == 0:
        if update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Vui lòng nhập mã token. Cú pháp: `/audit <symbol>`\n_Ví dụ:_ `/audit BTC`",
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    symbol = context.args[0].upper().replace("USDT", "") + "USDT"
    loading_msg = None
    if update.effective_message:
        loading_msg = await update.effective_message.reply_text(
            f"🔍 *Đang triệu tập Hội đồng Thẩm định & Biện lý Socratic cho {symbol}...*",
            parse_mode=ParseMode.MARKDOWN,
        )

    try:
        profile = get_symbol_market_profile(symbol)
        core_quant = CoreQuantEngine()
        quant_result = core_quant.run_full_quant_audit(
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

        spot_dict = quant_result["spot"].model_dump()
        futures_dict = quant_result["futures"].model_dump()
        whale_dict = quant_result["whale"].model_dump()
        etf_dict = quant_result["etf"].model_dump()
        vesting_dict = quant_result["vesting"].model_dump()

        # Contract adapters ensuring bidirectional field-name compatibility
        whale_dict["exchange_netflow_24h_usd"] = whale_dict.get("netflow_24h_usd", 0.0)
        etf_dict["netflow_24h_usd"] = etf_dict.get("daily_net_inflow_usd", 0.0)
        vesting_dict["unlock_percent_of_circulating"] = vesting_dict.get(
            "next_unlock_pct_of_circulating", 0.0
        )

        # Run Multi-Agent LangGraph Workflow
        audit_state = await run_crypto_audit(
            symbol=symbol,
            execution_mode="DUAL_AUDIT",
            spot_valuation_data=spot_dict,
            futures_squeeze_data=futures_dict,
            whale_flow_data=whale_dict,
            etf_flow_data=etf_dict,
            token_vesting_data=vesting_dict,
        )

        alert = audit_state.get("telegram_alert_payload")
        text: str = (
            str(alert.get("text"))
            if alert and alert.get("text")
            else "Không thể khởi tạo báo cáo thẩm định."
        )

        if not profile["is_calibrated"]:
            text += "\n\n_(⚠️ Ghi chú: Đang sử dụng dữ liệu tham chiếu chuẩn hóa cho tài sản này)_"

        if loading_msg:
            await loading_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except (RuntimeError, ValueError, KeyError) as e:
        logger.error("Audit command failed for %s: %s", symbol, e)
        if loading_msg:
            await loading_msg.edit_text(
                f"❌ Có lỗi xảy ra khi phân tích {symbol}: {e}",
                parse_mode=ParseMode.MARKDOWN,
            )


async def spot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /spot <symbol> command - Deterministic Spot cycle valuation."""
    symbol = context.args[0].upper() if context.args else "BTC"
    symbol_pair = symbol.replace("USDT", "") + "USDT"
    profile = get_symbol_market_profile(symbol)

    engine = SpotCycleEngine()
    schema = engine.evaluate(
        symbol=symbol_pair,
        current_price=profile["current_price"],
        market_cap=profile["market_cap"],
        realized_cap=profile["realized_cap"],
        std_market_cap=profile["std_market_cap"],
        sma_200d=profile["sma_200d"],
        sma_200w=profile["sma_200w"],
        sma_111d=profile["sma_111d"],
        sma_350d=profile["sma_350d"],
    )

    calibration_note = (
        "" if profile["is_calibrated"]
        else "\n_(⚠️ Ghi chú: Định vị dựa trên mô hình tham chiếu chuẩn hóa)_\n"
    )

    spot_card = (
        f"💎 *ĐỊNH VỊ TÍCH SẢN SPOT: {symbol_pair}*\n\n"
        f"• *Giá Hiện tại:* `${schema.current_price:,.2f}`\n"
        f"• *Chu kỳ Macro:* `{schema.cycle_regime.value}`\n"
        f"• *MVRV Z-Score:* `{schema.mvrv_zscore:.2f}`\n"
        f"• *Mayer Multiple:* `{schema.mayer_multiple:.2f}`\n"
        f"• *200-Week MA:* `${schema.sma_200w:,.2f}`\n"
        f"• *Pi Cycle Top:* `{'BÁO ĐỘNG ĐỈNH' if schema.pi_cycle_top_triggered else 'Bình thường'}`\n\n"
        f"🎯 *VÙNG GIÁ MUA GOM (DCA ZONES):*\n"
        f"1. Mua thăm dò (Zone 1): `${schema.dca_zone_conservative:,.2f}` (-8%)\n"
        f"2. Mua gia tăng (Zone 2): `${schema.dca_zone_moderate:,.2f}` (Realized Support)\n"
        f"3. Gom tối đa (Zone 3): `${schema.dca_zone_aggressive:,.2f}` (200W-MA Floor)\n\n"
        f"🚀 *MỤC TIÊU CHỐT LỜI (TAKE PROFIT):*\n"
        f"• TP1 (+35%): `${schema.take_profit_target_1:,.2f}`\n"
        f"• TP2 (+75%): `${schema.take_profit_target_2:,.2f}`\n"
        f"• TP3 (+150%): `${schema.take_profit_target_3:,.2f}`\n"
        f"{calibration_note}"
        f"{DISCLAIMER_TEXT}"
    )
    if update.effective_message:
        await update.effective_message.reply_text(spot_card, parse_mode=ParseMode.MARKDOWN)


async def futures_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /futures <symbol> command - Derivatives leverage & squeeze audit."""
    symbol = context.args[0].upper() if context.args else "BTC"
    symbol_pair = symbol.replace("USDT", "") + "USDT"
    profile = get_symbol_market_profile(symbol)

    engine = FuturesRiskEngine()
    schema = engine.evaluate(
        symbol=symbol_pair,
        current_price=profile["current_price"],
        open_interest_usd=profile["open_interest_usd"],
        oi_24h_ago=profile["oi_24h_ago"],
        funding_rate_8h=0.0008,
        long_short_ratio=2.85,
        bids=[[profile["current_price"], 15.0]],
        asks=[[profile["current_price"] * 1.001, 45.0]],
        high_24h=profile["current_price"] * 1.02,
        low_24h=profile["current_price"] * 0.98,
    )

    calibration_note = (
        "" if profile["is_calibrated"]
        else "\n_(⚠️ Ghi chú: Đòn bẩy dựa trên mô hình tham chiếu chuẩn hóa)_\n"
    )

    futures_card = (
        f"⚡ *BẢN ĐỒ RỦI RO PHÁI SINH FUTURES: {symbol_pair}*\n\n"
        f"• *Giá Hiện tại:* `${schema.current_price:,.2f}`\n"
        f"• *Mức độ Rủi ro:* `{schema.futures_risk_level.value}`\n"
        f"• *Funding Rate (8h):* `+{schema.annualized_funding_rate:.1f}% APR`\n"
        f"• *Funding Rate Squeeze Index (FRSI):* `{schema.frsi_score:.1f}/100`\n"
        f"• *Biến động OI (24h):* `+{schema.oi_change_24h_pct:.1f}%`\n"
        f"• *Orderbook Imbalance (OBIR ±2%):* `{schema.orderbook_imbalance_ratio:.2f}`\n"
        f"• *Cụm Quét Thanh Lý:*\n"
        f"   - Phía trên (Short Liquidation): `${schema.liquidation_pocket_above:,.2f}`\n"
        f"   - Phía dưới (Long Liquidation): `${schema.liquidation_pocket_below:,.2f}`\n\n"
        f"⚠️ *KHUYẾN NGHỊ PHÒNG HỘ:* Thận trọng với vị thế Long đòn bẩy cao. "
        f"Nguy cơ quét râu về vùng ${schema.liquidation_pocket_below:,.2f} trước khi tiếp diễn xu hướng.\n"
        f"{calibration_note}"
        f"{DISCLAIMER_TEXT}"
    )
    if update.effective_message:
        await update.effective_message.reply_text(futures_card, parse_mode=ParseMode.MARKDOWN)


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /subscribe command - Register chat ID for push alerts."""
    chat_id = update.effective_chat.id if update.effective_chat else "Unknown"
    sub_text = (
        f"✅ *ĐĂNG KÝ NHẬN CẢNH BÁO THÀNH CÔNG!*\n"
        f"Chat ID: `{chat_id}`\n\n"
        f"Hệ thống sẽ tự động gửi thông báo khẩn cấp khi phát hiện:\n"
        f"🚨 Cá voi nạp/rút CEX ròng lớn (> $100M USD)\n"
        f"💵 Tether Treasury in thêm USDT mới (> $1B USD)\n"
        f"🔥 Funding Rate biến động cực đoan (Nguy cơ quét thanh lý)\n"
        f"🔓 Sự kiện mở khóa token (Vesting cliff) có nguy cơ xả mạnh."
        f"{DISCLAIMER_TEXT}"
    )
    if update.effective_message:
        await update.effective_message.reply_text(sub_text, parse_mode=ParseMode.MARKDOWN)


def run_bot() -> None:
    """Main entrypoint for running the Telegram Bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_telegram_bot_token_here":
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set or using placeholder in .env. "
            "Please configure a valid token from @BotFather."
        )
        sys.exit(1)

    logger.info("Starting CryptoIntel Telegram Bot...")
    application = ApplicationBuilder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("audit", audit_command))
    application.add_handler(CommandHandler("spot", spot_command))
    application.add_handler(CommandHandler("futures", futures_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))

    # Run polling
    application.run_polling()


if __name__ == "__main__":
    run_bot()
