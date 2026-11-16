"""
Socratic Devil's Advocate Inquisitor Node for CryptoIntel-Engine LangGraph.
Challenges retail FOMO, exposes systemic fragility, and generates 3 Fatal Cross-Examinations.
"""

from src.agents.llm_client import LLMReasoningClient
from src.agents.state import CryptoIntelState


async def socratic_node(state: CryptoIntelState) -> dict[str, object]:
    """Execute Socratic Devil's Advocate cross-examination."""
    symbol = state.get("symbol", "BTCUSDT")
    spot_dossier = state.get("spot_dossier")
    futures_dossier = state.get("futures_dossier")
    whale_dossier = state.get("whale_etf_dossier")

    spot_quant = state.get("spot_valuation_data")
    futures_quant = state.get("futures_squeeze_data")
    whale_quant = state.get("whale_flow_data")
    proposed_action = state.get("proposed_action")
    hard_red_flags = state.get("hard_red_flags")

    client = LLMReasoningClient()
    critique = await client.generate_socratic_critique(
        symbol=symbol,
        spot_dossier=spot_dossier,
        futures_dossier=futures_dossier,
        whale_dossier=whale_dossier,
        spot_quant=spot_quant,
        futures_quant=futures_quant,
        whale_quant=whale_quant,
        proposed_action=proposed_action,
        hard_red_flags=hard_red_flags,
    )

    return {
        "fomo_index": critique["fomo_index"],
        "fatal_socratic_questions": critique["fatal_socratic_questions"],
        "worst_case_invalidation_price": critique["worst_case_invalidation_price"],
        "thesis_refutations": critique["thesis_refutations"],
        "anti_fomo_verdict": critique["anti_fomo_verdict"],
    }
