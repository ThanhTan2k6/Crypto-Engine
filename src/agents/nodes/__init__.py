"""Multi-Agent nodes for LangGraph state machine."""

from src.agents.nodes.futures_node import futures_node
from src.agents.nodes.socratic_node import socratic_node
from src.agents.nodes.spot_node import spot_node
from src.agents.nodes.supervisor import supervisor_node
from src.agents.nodes.synthesis_node import synthesis_node
from src.agents.nodes.whale_node import whale_node

__all__ = [
    "futures_node",
    "socratic_node",
    "spot_node",
    "supervisor_node",
    "synthesis_node",
    "whale_node",
]
