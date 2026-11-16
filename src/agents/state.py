"""
LangGraph Multi-Agent State Schema for CryptoIntel-Engine.
Implements the canonical CryptoIntelState specification.
"""

from datetime import UTC, datetime
from typing import Any, TypedDict


class SpecialistDossier(TypedDict):
    """Structured report produced by an analytical specialist agent."""

    agent_id: str
    verdict: str
    confidence_score: float
    risk_level: str
    key_observations: list[str]
    critical_vulnerabilities: list[str]
    timestamp: str


class CryptoIntelState(TypedDict):
    """Canonical LangGraph execution state for CryptoIntel-Engine multi-agent auditing."""

    # Ingestion & Context
    symbol: str
    timestamp: str
    execution_mode: str  # "MODE_SPOT", "MODE_FUTURES", or "DUAL_AUDIT"

    # Pre-calculated Immutable Quant Payloads (from src/engine/)
    spot_valuation_data: dict[str, Any] | None
    futures_squeeze_data: dict[str, Any] | None
    etf_flow_data: dict[str, Any] | None
    whale_flow_data: dict[str, Any] | None
    token_vesting_data: dict[str, Any] | None

    # User Trade Proposal Context
    proposed_action: str | None  # e.g., "LONG_BTC_5X", "DCA_BUY_SPOT"
    proposed_entry: float | None
    time_horizon_days: int

    # Specialist Analytical Dossiers
    spot_dossier: SpecialistDossier | None
    futures_dossier: SpecialistDossier | None
    whale_etf_dossier: SpecialistDossier | None

    # Hard Forensic Red Flags
    hard_red_flags: list[str] | None

    # Socratic Devil's Advocate Outputs
    fomo_index: float
    fatal_socratic_questions: list[str]  # Exactly 3 Fatal Questions
    worst_case_invalidation_price: float
    thesis_refutations: list[str]
    anti_fomo_verdict: str  # "SCALE_IN_SPOT", "PROCEED_WITH_CAUTION", "REJECT_SETUP_TOO_RISKY"

    # Final Synthesis & Presentation Payloads
    investment_memo: dict[str, Any] | None
    telegram_alert_payload: dict[str, Any] | None
    errors: list[str]
    trace_id: str


def create_initial_state(
    symbol: str,
    execution_mode: str = "DUAL_AUDIT",
    spot_valuation_data: dict[str, Any] | None = None,
    futures_squeeze_data: dict[str, Any] | None = None,
    etf_flow_data: dict[str, Any] | None = None,
    whale_flow_data: dict[str, Any] | None = None,
    token_vesting_data: dict[str, Any] | None = None,
    proposed_action: str | None = None,
    proposed_entry: float | None = None,
    time_horizon_days: int = 30,
    trace_id: str = "",
    hard_red_flags: list[str] | None = None,
) -> CryptoIntelState:
    """Factory function to build a clean initialized state."""
    return {
        "symbol": symbol.upper(),
        "timestamp": datetime.now(UTC).isoformat(),
        "execution_mode": execution_mode,
        "spot_valuation_data": spot_valuation_data,
        "futures_squeeze_data": futures_squeeze_data,
        "etf_flow_data": etf_flow_data,
        "whale_flow_data": whale_flow_data,
        "token_vesting_data": token_vesting_data,
        "proposed_action": proposed_action,
        "proposed_entry": proposed_entry,
        "time_horizon_days": time_horizon_days,
        "spot_dossier": None,
        "futures_dossier": None,
        "whale_etf_dossier": None,
        "hard_red_flags": hard_red_flags,
        "fomo_index": 0.0,
        "fatal_socratic_questions": [],
        "worst_case_invalidation_price": 0.0,
        "thesis_refutations": [],
        "anti_fomo_verdict": "PROCEED_WITH_CAUTION",
        "investment_memo": None,
        "telegram_alert_payload": None,
        "errors": [],
        "trace_id": trace_id or f"audit_{symbol.lower()}_{int(datetime.now(UTC).timestamp())}",
    }
