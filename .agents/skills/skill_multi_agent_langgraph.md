# Agent Skill: Multi-Agent StateGraph Architecture with LangGraph

## 1. Description
Implementation blueprint for LangGraph StateGraph, branched execution (Mode Spot / Mode Futures), and structured outputs via Pydantic v2.

---

## 2. Implementation Architecture

### Dual-Engine Fan-Out / Fan-In Pattern
```python
from langgraph.graph import StateGraph, START, END
from src.agents.state import CryptoIntelState

# 1. Initialize StateGraph
workflow = StateGraph(CryptoIntelState)

# 2. Add Specialist Nodes
workflow.add_node("supervisor_node", supervisor_step)
workflow.add_node("spot_node", spot_cycle_step)
workflow.add_node("futures_node", futures_squeeze_step)
workflow.add_node("whale_etf_node", whale_etf_step)
workflow.add_node("socratic_node", socratic_devil_advocate_step)
workflow.add_node("delivery_node", delivery_step)

# 3. Mode-Based Routing Logic
def route_by_mode(state: CryptoIntelState):
    mode = state.get("execution_mode", "DUAL_AUDIT")
    if mode == "MODE_SPOT":
        return ["spot_node", "whale_etf_node"]
    elif mode == "MODE_FUTURES":
        return ["futures_node", "whale_etf_node"]
    return ["spot_node", "futures_node", "whale_etf_node"]

workflow.add_edge(START, "supervisor_node")
workflow.add_conditional_edges("supervisor_node", route_by_mode)

# 4. Join Barrier into Socratic Agent
workflow.add_edge("spot_node", "socratic_node")
workflow.add_edge("futures_node", "socratic_node")
workflow.add_edge("whale_etf_node", "socratic_node")

# 5. Delivery Formatting & Persistence
workflow.add_edge("socratic_node", "delivery_node")
workflow.add_edge("delivery_node", END)

app = workflow.compile()
```
