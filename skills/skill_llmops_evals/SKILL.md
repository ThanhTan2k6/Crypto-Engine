---
name: skill_llmops_evals
description: LLMOps evaluation pipelines with DeepEval, Langfuse tracing, and CI/CD quality gates for financial multi-agent systems.
---

# Skill: LLMOps, Observability & DeepEval Testing

## 1. Scope & Objective
Automates the evaluation of agent reasoning quality, prevents model drift, and tracks live operational metrics (latency, token costs).

## 2. DeepEval Quality Gate Implementation
```python
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, HallucinationMetric, GEval
from deepeval.test_case import LLMTestCaseParams

def test_socratic_agent_faithfulness_gc01(quant_luna_contract, agent_output):
    test_case = LLMTestCase(
        input=quant_luna_contract.model_dump_json(),
        actual_output=agent_output["socratic_verdict"]["fatal_questions"],
        retrieval_context=[quant_luna_contract.model_dump_json()]
    )
    
    # Assert Faithfulness >= 0.95
    faithfulness = FaithfulnessMetric(threshold=0.95)
    assert_test(test_case, [faithfulness])

def test_socratic_rigor_geval(quant_contract, agent_output):
    rigor_metric = GEval(
        name="Socratic Anti-FOMO Rigor",
        criteria="Evaluate if the 3 questions aggressively target emotional euphoria, highlight leverage risk, and pinpoint structural vulnerabilities.",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.90
    )
    test_case = LLMTestCase(input=quant_contract.model_dump_json(), actual_output=str(agent_output))
    assert_test(test_case, [rigor_metric])
```

## 3. Langfuse Observability Hooks
- Wrap all LangGraph state nodes with the `@observe()` decorator from `langfuse.decorators`.
- Track prompt token consumption, latency per specialist agent, and tag traces with `symbol` and `regime`.
