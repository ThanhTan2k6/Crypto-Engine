"""
Spot Cycle Specialist Node for CryptoIntel-Engine LangGraph.
Evaluates MVRV Z-Score, 200W-MA, Mayer Multiple, Pi Cycle, and DCA Accumulation Zones.
"""

from datetime import UTC, datetime

from src.agents.llm_client import LLMReasoningClient
from src.agents.state import CryptoIntelState, SpecialistDossier


async def spot_node(state: CryptoIntelState) -> dict[str, object]:
    """Execute spot cycle specialist evaluation."""
    spot_data = state.get("spot_valuation_data")
    if state.get("errors") or not spot_data:
        # Default fallback dossier if errors or spot data wasn't provided
        dossier: SpecialistDossier = {
            "agent_id": "spot_cycle_specialist",
            "verdict": "DATA_UNAVAILABLE",
            "confidence_score": 0.0,
            "risk_level": "UNKNOWN",
            "key_observations": ["Spot valuation data not supplied or contract invalid."],
            "critical_vulnerabilities": [],
            "timestamp": datetime.now(UTC).isoformat(),
        }
        return {"spot_dossier": dossier}

    client = LLMReasoningClient()
    analysis = await client.generate_spot_analysis(spot_data)
    analysis["timestamp"] = datetime.now(UTC).isoformat()

    return {"spot_dossier": analysis}
