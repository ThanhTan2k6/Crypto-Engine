---
name: skill_multi_agent_langgraph
description: LangGraph state-machine patterns, parallel fan-out/fan-in, conditional routing, and error resilience for trading intelligence.
---

# Skill: Multi-Agent Architecture with LangGraph

## 1. Scope & Objective
Defines implementation patterns for orchestrating deterministic signals through specialized agents and converging on Socratic debate.

## 2. Graph Engineering Guidelines

### Concurrent Execution Pattern (Fan-Out)
```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(CryptoIntelState)

# 1. Register Nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("macro_analyst", macro_agent_node)
builder.add_node("whale_analyst", whale_agent_node)
builder.add_node("derivatives_analyst", derivatives_agent_node)
builder.add_node("socratic_debater", socratic_agent_node)

# 2. Parallel Fan-Out from Supervisor
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "macro_analyst")
builder.add_edge("supervisor", "whale_analyst")
builder.add_edge("supervisor", "derivatives_analyst")

# 3. Fan-In Convergence into Socratic Agent
builder.add_edge("macro_analyst", "socratic_debater")
builder.add_edge("whale_analyst", "socratic_debater")
builder.add_edge("derivatives_analyst", "socratic_debater")

# 4. Final Exit
builder.add_edge("socratic_debater", END)
```

### Invariants:
- State must remain immutable per node execution; return partial state dictionaries.
- Every node must catch external LLM timeouts and return fallback deterministic summaries without crashing the state machine.
