"""
Futures Squeeze Specialist Node for CryptoIntel-Engine LangGraph.
Evaluates Funding APR, FRSI, OI Divergence, Orderbook Imbalance, and Liquidation Pockets.
"""

from datetime import UTC, datetime

from src.agents.llm_client import LLMReasoningClient
from src.agents.state import CryptoIntelState, SpecialistDossier


async def futures_node(state: CryptoIntelState) -> dict[str, object]:
    """Execute perpetual futures leverage & liquidation risk evaluation."""
    futures_data = state.get("futures_squeeze_data")
    if not futures_data:
        dossier: SpecialistDossier = {
            "agent_id": "futures_squeeze_specialist",
            "verdict": "DATA_UNAVAILABLE",
            "confidence_score": 0.0,
            "risk_level": "UNKNOWN",
            "key_observations": ["Futures squeeze data not supplied."],
            "critical_vulnerabilities": [],
            "timestamp": datetime.now(UTC).isoformat(),
        }
        return {"futures_dossier": dossier}

    client = LLMReasoningClient()
    analysis = await client.generate_futures_analysis(futures_data)
    analysis["timestamp"] = datetime.now(UTC).isoformat()

    return {"futures_dossier": analysis}
