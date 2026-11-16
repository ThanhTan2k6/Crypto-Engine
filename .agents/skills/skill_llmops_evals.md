# Agent Skill: LLMOps, Redis Semantic Caching & DeepEval Benchmark

## 1. Description
Guidelines for configuring Redis Semantic Caching, Langfuse distributed tracing, and DeepEval automated regression testing for CryptoIntel-Engine.

---

## 2. Redis Caching Implementation Pattern
```python
import hashlib
import json
import redis
from typing import Optional

redis_client = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

def generate_cache_key(symbol: str, mode: str, cycle_regime: str, frsi_bucket: int) -> str:
    raw = f"{symbol}:{mode}:{cycle_regime}:{frsi_bucket}"
    return f"cryptointel:cache:{hashlib.sha256(raw.encode()).hexdigest()}"

def get_cached_audit(cache_key: str) -> Optional[dict]:
    data = redis_client.get(cache_key)
    return json.loads(data) if data else None

def set_cached_audit(cache_key: str, audit_dict: dict, ttl_seconds: int = 300) -> None:
    redis_client.setex(cache_key, ttl_seconds, json.dumps(audit_dict))
```

---

## 3. DeepEval Benchmark Implementation Pattern
```python
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, HallucinationMetric

def test_socratic_agent_faithfulness(contract_input_json: str, agent_output_text: str):
    test_case = LLMTestCase(
        input=contract_input_json,
        actual_output=agent_output_text,
        retrieval_context=[contract_input_json]
    )
    faithfulness = FaithfulnessMetric(threshold=0.95)
    hallucination = HallucinationMetric(threshold=0.05)
    assert_test(test_case, [faithfulness, hallucination])
```
