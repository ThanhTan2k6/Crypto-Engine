"""
Synthesis & Delivery Node for CryptoIntel-Engine LangGraph.
Compiles Specialist Dossiers and Socratic Critique into Investment Memo and Telegram payloads.
"""

from datetime import UTC, datetime

from src.agents.state import CryptoIntelState

DISCLAIMER_TEXT = (
    "⚠️ Digital Asset Risk Disclaimer: This audit is produced for educational and risk evaluation "
    "purposes only. Cryptocurrency assets are subject to extreme volatility and total capital risk. "
    "This analysis does not constitute financial, investment, or trading advice."
)


async def synthesis_node(state: CryptoIntelState) -> dict[str, object]:
    """Compile final deliverables and append regulatory risk disclaimer."""
    symbol = state.get("symbol", "BTCUSDT")
    verdict = state.get("anti_fomo_verdict", "PROCEED_WITH_CAUTION")
    fomo_index = state.get("fomo_index", 50.0)
    questions = state.get("fatal_socratic_questions", [])
    invalidation = state.get("worst_case_invalidation_price", 0.0)

    spot_dossier = state.get("spot_dossier")
    futures_dossier = state.get("futures_dossier")
    whale_dossier = state.get("whale_etf_dossier")

    investment_memo = {
        "title": f"CryptoIntel Risk Audit: {symbol}",
        "generated_at": datetime.now(UTC).isoformat(),
        "anti_fomo_verdict": verdict,
        "fomo_index": fomo_index,
        "worst_case_invalidation_price": invalidation,
        "fatal_socratic_questions": questions,
        "specialist_summaries": {
            "spot": spot_dossier.get("verdict") if spot_dossier else "N/A",
            "futures": futures_dossier.get("verdict") if futures_dossier else "N/A",
            "whale": whale_dossier.get("verdict") if whale_dossier else "N/A",
        },
        "disclaimer": DISCLAIMER_TEXT,
    }

    # Format Telegram-ready text payload
    q_text = "\n".join(f"• {q}" for q in questions)
    telegram_text = (
        f"🛡️ *HỘI ĐỒNG THẨM ĐỊNH RỦI RO: {symbol}*\n\n"
        f"📊 *Chỉ số FOMO:* `{fomo_index}/100`\n"
        f"⚖️ *Phán quyết Anti-FOMO:* *{verdict}*\n"
        f"🛑 *Mức giá Vô hiệu hóa (Invalidation):* `${invalidation:,.2f}`\n\n"
        f"🗣️ *3 CÂU HỎI PHẢN BIỆN SOCRATIC:*\n{q_text}\n\n"
        f"_{DISCLAIMER_TEXT}_"
    )

    telegram_alert_payload = {
        "symbol": symbol,
        "text": telegram_text,
        "verdict": verdict,
        "fomo_index": fomo_index,
    }

    return {
        "investment_memo": investment_memo,
        "telegram_alert_payload": telegram_alert_payload,
    }
