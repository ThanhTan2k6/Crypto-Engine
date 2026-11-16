"""
Whale & Institutional Flow Specialist Node for CryptoIntel-Engine LangGraph.
Decodes CEX netflow, smart money cold storage accumulation, Spot ETF flows, and vesting cliffs.
"""

from datetime import UTC, datetime

from src.agents.llm_client import LLMReasoningClient
from src.agents.state import CryptoIntelState


async def whale_node(state: CryptoIntelState) -> dict[str, object]:
    """Execute forensic whale, institutional ETF, and vesting dilution audit."""
    whale_data = state.get("whale_flow_data")
    etf_data = state.get("etf_flow_data")
    vesting_data = state.get("token_vesting_data")

    client = LLMReasoningClient()
    analysis = await client.generate_whale_analysis(whale_data, etf_data, vesting_data)
    analysis["timestamp"] = datetime.now(UTC).isoformat()

    return {"whale_etf_dossier": analysis}
