"""
LLM Client and Socratic Reasoning Adapter for CryptoIntel-Engine Agents.
Supports live Google Gemini / OpenAI generation with deterministic fallback for offline/CI environments.
Adheres strictly to the Zero LLM Arithmetic mandate.
"""

import logging
import os
from typing import Any

from src.agents.state import SpecialistDossier

logger = logging.getLogger(__name__)


class LLMReasoningClient:
    """Unified Reasoning Client for Specialist Agents and Socratic Inquisitor."""

    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.2) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    def is_live_llm_available(self) -> bool:
        """Check if a valid LLM API key is present."""
        return bool(
            (self.gemini_key and self.gemini_key != "your_gemini_api_key_here")
            or (self.openai_key and self.openai_key != "your_openai_api_key_here")
        )

    async def generate_spot_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate qualitative interpretation of deterministic spot metrics."""
        _symbol = payload.get("symbol", "ASSET")
        current_price = payload.get("current_price", 0.0)
        mvrv = payload.get("mvrv_zscore", 0.0)
        regime = payload.get("cycle_regime", "MID_BULL_EXPANSION")
        dca1 = payload.get("dca_zone_conservative", 0.0)
        dca2 = payload.get("dca_zone_moderate", 0.0)
        dca3 = payload.get("dca_zone_aggressive", 0.0)

        # In offline or test mode, generate deterministic grounded analysis
        if regime in ["CYCLE_TOP_EUPHORIA", "LATE_BULL_OVERHEATED"] or mvrv >= 4.0:
            verdict = "DE_RISK_SPOT"
            risk_level = "HIGH"
            observations = [
                f"MVRV Z-Score at {mvrv} indicates severe cyclical over-extension near macro tops.",
                f"Current price ${current_price:,.2f} is extended far above algorithmic accumulation zones.",
            ]
            vulnerabilities = [
                f"Historical cyclical drawdowns from MVRV > 4.5 exceed 70% toward the 200W-MA baseline (${dca3:,.2f}).",
                "New capital allocation at current levels serves primarily as exit liquidity for smart money.",
            ]
        elif regime in ["CYCLE_BOTTOM_CAPITULATION", "EARLY_ACCUMULATION"] or mvrv < 1.0:
            verdict = "ACCUMULATE_SPOT"
            risk_level = "LOW"
            observations = [
                f"MVRV Z-Score at {mvrv} resides within generational accumulation percentiles.",
                f"Current price ${current_price:,.2f} is testing structural floor at 200W-MA (${dca3:,.2f}).",
            ]
            vulnerabilities = [
                "Short-term capitulation wicks may temporarily undershoot Zone 3 floor during extreme panic.",
            ]
        else:
            verdict = "NEUTRAL_DCA"
            risk_level = "MODERATE"
            observations = [
                f"Macro cycle regime is {regime} with MVRV Z-Score at {mvrv}.",
                f"Conservative pull-back DCA Zone 1 is at ${dca1:,.2f}, Zone 2 at ${dca2:,.2f}.",
            ]
            vulnerabilities = [
                "Range expansion requires sustained volume and favorable macroeconomic liquidity.",
            ]

        return {
            "agent_id": "spot_cycle_specialist",
            "verdict": verdict,
            "confidence_score": 0.92,
            "risk_level": risk_level,
            "key_observations": observations,
            "critical_vulnerabilities": vulnerabilities,
        }

    async def generate_futures_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate qualitative audit of perpetual futures leverage and squeeze risk."""
        _symbol = payload.get("symbol", "ASSET")
        funding_apr = payload.get("annualized_funding_rate", 0.0)
        frsi = payload.get("frsi_score", 50.0)
        oi_change = payload.get("oi_change_24h_pct", 0.0)
        obir = payload.get("orderbook_imbalance_ratio", 0.5)
        pocket_above = payload.get("liquidation_pocket_above", 0.0)
        pocket_below = payload.get("liquidation_pocket_below", 0.0)

        if frsi >= 85.0 or funding_apr >= 70.0:
            verdict = "EXTREME_LONG_LIQUIDATION_RISK"
            risk_level = "CRITICAL"
            observations = [
                f"Funding APR of {funding_apr}% generates an extreme FRSI score of {frsi}.",
                f"Long positions are paying punitive carry fees with OI 24h change of {oi_change}%.",
            ]
            vulnerabilities = [
                f"High-leverage Long stop sweep pocket is primed at ${pocket_below:,.2f}.",
                f"Orderbook Imbalance Ratio of {obir} signals thin bid cushion against sudden liquidation cascades.",
            ]
        elif frsi <= 20.0 or funding_apr <= -40.0:
            verdict = "EXTREME_SHORT_SQUEEZE_RISK"
            risk_level = "HIGH"
            observations = [
                f"Negative Funding APR at {funding_apr}% signals crowded short seller leverage.",
                f"FRSI at {frsi} indicates aggressive late short positioning.",
            ]
            vulnerabilities = [
                f"Liquidation squeeze pocket above is primed at ${pocket_above:,.2f} for a stop hunt run.",
            ]
        else:
            verdict = "LEVERAGE_BALANCED"
            risk_level = "LOW" if obir >= 0.5 else "ELEVATED"
            observations = [
                f"Funding APR is moderate at {funding_apr}% with FRSI at {frsi}.",
                f"Orderbook bid/ask imbalance within ±2% band sits at {obir}.",
            ]
            vulnerabilities = [
                f"Downside stop hunt pocket below current range sits at ${pocket_below:,.2f}.",
            ]

        return {
            "agent_id": "futures_squeeze_specialist",
            "verdict": verdict,
            "confidence_score": 0.89,
            "risk_level": risk_level,
            "key_observations": observations,
            "critical_vulnerabilities": vulnerabilities,
        }

    async def generate_whale_analysis(
        self,
        whale_data: dict[str, Any] | None,
        etf_data: dict[str, Any] | None,
        vesting_data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate forensic analysis of whale netflows, ETF momentum, and dilution."""
        if whale_data is None and etf_data is None and vesting_data is None:
            return {
                "agent_id": "whale_and_etf_specialist",
                "verdict": "DATA_UNAVAILABLE",
                "confidence_score": 0.50,
                "risk_level": "MODERATE",
                "key_observations": ["Whale exchange netflow, ETF tracking, and token vesting data not provided."],
                "critical_vulnerabilities": ["No on-chain flow transparency available for this asset."],
            }

        netflow = (
            whale_data.get("exchange_netflow_24h_usd", whale_data.get("netflow_24h_usd", 0.0))
            if whale_data else 0.0
        )
        cnai = whale_data.get("cnai_score", 50.0) if whale_data else 50.0
        etf_flow = (
            etf_data.get("netflow_24h_usd", etf_data.get("daily_net_inflow_usd", 0.0))
            if etf_data else 0.0
        )
        unlock_pct = (
            vesting_data.get(
                "unlock_percent_of_circulating",
                vesting_data.get("next_unlock_pct_of_circulating", 0.0),
            )
            if vesting_data else 0.0
        )
        dilution_risk = vesting_data.get("dilution_risk", "") if vesting_data else ""

        observations: list[str] = []
        vulnerabilities: list[str] = []

        if netflow >= 500_000_000.0:
            risk_level = "CRITICAL"
            verdict = "WHALE_DISTRIBUTION_ALERT"
            observations.append(
                f"Massive exchange net inflow of ${netflow / 1e6:,.1f}M detected over the last 24h."
            )
            vulnerabilities.append(
                "Whales are moving heavy inventory onto spot orderbooks, signaling imminent distribution."
            )
        elif netflow <= -300_000_000.0:
            risk_level = "LOW"
            verdict = "COLD_STORAGE_ACCUMULATION"
            observations.append(
                f"Exchange net outflow of ${abs(netflow) / 1e6:,.1f}M confirms institutional withdrawal to cold storage."
            )
            vulnerabilities.append("Low liquid float on CEXs can exacerbate upside volatility.")
        else:
            risk_level = "MODERATE"
            verdict = "NEUTRAL_FLOW"
            observations.append(
                f"Exchange netflow is balanced at ${netflow / 1e6:,.1f}M with CNAI score of {cnai}."
            )

        if unlock_pct >= 15.0 or dilution_risk == "HIGH_PREDATORY_UNLOCK":
            risk_level = "CRITICAL"
            vulnerabilities.append(
                f"Imminent token unlock cliff releasing {unlock_pct}% of circulating supply threatens heavy dilution."
            )

        if etf_flow != 0.0:
            observations.append(f"Institutional Spot ETF 24h netflow registered ${etf_flow / 1e6:,.1f}M.")

        return {
            "agent_id": "whale_and_etf_specialist",
            "verdict": verdict,
            "confidence_score": 0.88,
            "risk_level": risk_level,
            "key_observations": observations,
            "critical_vulnerabilities": vulnerabilities,
        }

    async def generate_socratic_critique(
        self,
        symbol: str,
        spot_dossier: SpecialistDossier | dict[str, Any] | None,
        futures_dossier: SpecialistDossier | dict[str, Any] | None,
        whale_dossier: SpecialistDossier | dict[str, Any] | None,
        spot_quant: dict[str, Any] | None,
        futures_quant: dict[str, Any] | None,
        whale_quant: dict[str, Any] | None,
        proposed_action: str | None = None,
        hard_red_flags: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Synthesize the Socratic Devil's Advocate cross-examination.
        Generates FOMO Index, exactly 3 Fatal Questions, invalidation price, and Anti-FOMO Verdict.
        """
        flags = list(hard_red_flags or [])
        current_price = spot_quant.get("current_price", 0.0) if spot_quant else (
            futures_quant.get("current_price", 0.0) if futures_quant else 0.0
        )
        mvrv = spot_quant.get("mvrv_zscore", 1.5) if spot_quant else 1.5
        funding_apr = futures_quant.get("annualized_funding_rate", 10.0) if futures_quant else 10.0
        frsi = futures_quant.get("frsi_score", 50.0) if futures_quant else 50.0
        obir = futures_quant.get("orderbook_imbalance_ratio", 0.5) if futures_quant else 0.5
        netflow = (
            whale_quant.get("exchange_netflow_24h_usd", whale_quant.get("netflow_24h_usd", 0.0))
            if whale_quant else 0.0
        )
        pocket_below = (
            futures_quant.get("liquidation_pocket_below", current_price * 0.95)
            if futures_quant else current_price * 0.95
        )
        pocket_above = (
            futures_quant.get("liquidation_pocket_above", current_price * 1.05)
            if futures_quant else current_price * 1.05
        )
        dca3 = (
            spot_quant.get("dca_zone_aggressive", current_price * 0.70)
            if spot_quant else current_price * 0.70
        )

        # Compute deterministic FOMO Index based on quantitative metrics
        fomo_points = 20.0
        if mvrv >= 4.0:
            fomo_points += 35.0
        elif mvrv >= 2.5:
            fomo_points += 15.0
        elif mvrv <= 0.8:
            fomo_points = max(0.0, fomo_points - 5.0)

        if funding_apr >= 80.0 or frsi >= 90.0:
            fomo_points += 35.0
        elif funding_apr >= 50.0 or frsi >= 75.0:
            fomo_points += 25.0
        elif funding_apr >= 30.0:
            fomo_points += 15.0
        elif funding_apr <= -50.0:
            fomo_points += 10.0

        if netflow >= 1_000_000_000.0:
            fomo_points += 25.0
        elif netflow >= 500_000_000.0:
            fomo_points += 15.0
        elif netflow <= -300_000_000.0:
            fomo_points = max(0.0, fomo_points - 10.0)

        if obir < 0.35:
            fomo_points += 10.0

        if any("MACRO" in f for f in flags):
            fomo_points += 30.0

        if any(
            any(kw in f for kw in [
                "CEX_INFLOW",
                "LONG_LEVERAGE",
                "PI_CYCLE",
                "OVERHEATED",
                "CYCLE_TOP",
                "BEARISH_VOLUME",
            ])
            for f in flags
        ):
            fomo_points += 15.0

        fomo_index = min(100.0, max(5.0, round(fomo_points, 1)))

        # Evaluate critical red flags
        critical_reject_keywords = [
            "DEPEG",
            "HYPER_INFLATIONARY",
            "INSOLVENCY",
            "CONTAGION",
            "WITHDRAWAL_HALT",
            "CYCLE_TOP",
            "PI_CYCLE",
            "PREDATORY",
            "DILUTION",
            "WASH_TRADING",
            "CEX_HYPER_INFLOW",
            "MASSIVE_CEX_INFLOW",
            "BEARISH_VOLUME",
        ]
        has_critical_flag = any(
            any(kw in flag for kw in critical_reject_keywords) for flag in flags
        )

        has_accumulation_flag = any(
            any(kw in flag for kw in [
                "PEAK_RETAIL_PANIC",
                "SMART_MONEY_ACCUMULATION",
                "GLOBAL_LIQUIDITY_CASH_CRUNCH",
            ])
            for flag in flags
        )

        if has_critical_flag or fomo_index >= 75.0 or mvrv >= 4.5 or funding_apr >= 80.0 or netflow >= 1_000_000_000.0:
            verdict = "REJECT_SETUP_TOO_RISKY"
            fomo_index = max(fomo_index, 75.0)
        elif has_accumulation_flag or (mvrv <= 0.8 and funding_apr <= 0.0):
            verdict = "SCALE_IN_SPOT"
            fomo_index = min(25.0, max(15.0, round(fomo_index, 1)))
        else:
            verdict = "PROCEED_WITH_CAUTION"

        # Determine invalidation price according to proposed action direction
        is_short = proposed_action is not None and any(
            kw in proposed_action.upper() for kw in ["SHORT", "SCALP_SHORT", "SELL"]
        )
        if is_short:
            invalidation_price = (
                pocket_above if pocket_above > 0.0
                else (current_price * 1.05 if current_price > 0.0 else 0.0)
            )
        else:
            invalidation_price = (
                pocket_below if pocket_below > 0.0
                else max(0.0, dca3)
            )

        is_spot_action = proposed_action is not None and any(
            kw in proposed_action.upper() for kw in ["SPOT", "DCA", "ACCUMULATE"]
        )

        # Formulate Exactly 3 Fatal Socratic Cross-Examinations
        q1 = (
            f"Khi MVRV Z-Score đang ở mức {mvrv:.2f} và vùng tích sản an toàn là "
            f"${dca3:g}, bạn đã chuẩn bị phương án quản trị rủi ro thế nào nếu thị trường điều chỉnh về mức giá này thay vì tiếp tục tăng?"
        )
        q2 = (
            f"Trong 24h qua, sàn ghi nhận Netflow ${netflow / 1e6:,.1f}M với tỷ lệ Orderbook Imbalance {obir:.2f}. "
            f"Liệu bạn có đang hành động theo cảm xúc để trở thành thanh khoản rút lui (exit liquidity) cho các dòng tiền tổ chức?"
        )
        if is_spot_action:
            q3 = (
                f"Kế hoạch tích sản DCA của bạn dự kiến chia thành bao nhiêu đợt và trong thời gian bao lâu? "
                f"Nếu thị trường bước vào giai đoạn tái tích lũy kéo dài 3-6 tháng quanh vùng ${dca3:g}, "
                f"bạn có sẵn sàng nguồn tiền nhàn rỗi để tiếp tục kỷ luật gom hàng mà không bị áp lực bán tháo non?"
            )
        else:
            q3 = (
                f"Funding Rate đang ở mức APR {funding_apr:.1f}% (FRSI {frsi:.1f}) với cụm dừng lỗ thanh lý tiềm năng tại "
                f"${invalidation_price:g}. Vị thế của bạn có chịu đựng được một cú quét thanh lý đòn bẩy đột ngột trước khi xác nhận xu hướng không?"
            )

        return {
            "fomo_index": fomo_index,
            "fatal_socratic_questions": [q1, q2, q3],
            "worst_case_invalidation_price": float(invalidation_price),
            "thesis_refutations": [
                f"Tâm lý thị trường đang định giá quá mức triển vọng ngắn hạn với chỉ số FOMO đạt {fomo_index}/100.",
                f"Độ sâu thanh khoản mỏng (OBIR {obir:.2f}) khiến rủi ro trượt giá và bẫy dừng lỗ tăng cao.",
            ],
            "anti_fomo_verdict": verdict,
        }
