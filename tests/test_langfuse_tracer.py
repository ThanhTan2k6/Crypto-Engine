"""
Unit Tests for Langfuse Observability & LLMOps Tracer.
Verifies trace lifecycle recording, node spans, and graceful local degradation.
"""

from src.llmops.langfuse_tracer import LangfuseAuditTracer


def test_tracer_lifecycle_in_local_mode():
    """Verify tracer records full multi-agent audit lifecycle without external dependencies."""
    tracer = LangfuseAuditTracer(public_key=None, secret_key=None)
    assert not tracer.is_enabled

    trace_id = "test_trace_123"
    # Start trace
    start_rec = tracer.trace_audit_start(
        trace_id=trace_id,
        symbol="BTCUSDT",
        execution_mode="DUAL_AUDIT",
        proposed_action="BUY_SPOT_DCA",
    )
    assert start_rec["trace_id"] == trace_id
    assert start_rec["status"] == "RUNNING"

    # Record node spans
    tracer.trace_node_span(
        trace_id=trace_id,
        node_name="spot_specialist",
        inputs={"mvrv": 1.8},
        outputs={"verdict": "ACCUMULATE"},
        latency_ms=45.2,
    )
    tracer.trace_node_span(
        trace_id=trace_id,
        node_name="socratic_devil",
        inputs={"fomo_index": 35.0},
        outputs={"anti_fomo_verdict": "PROCEED_WITH_CAUTION"},
        latency_ms=88.5,
    )

    # End trace
    end_rec = tracer.trace_audit_end(
        trace_id=trace_id,
        anti_fomo_verdict="PROCEED_WITH_CAUTION",
        fomo_index=35.0,
        fatal_questions=["Q1", "Q2", "Q3"],
    )

    assert end_rec["status"] == "COMPLETED"
    assert end_rec["anti_fomo_verdict"] == "PROCEED_WITH_CAUTION"
    assert end_rec["duration_ms"] > 0.0
    assert len(end_rec["spans"]) == 2

    # Check recent traces retrieval
    recent = tracer.get_recent_traces(limit=5)
    assert len(recent) >= 1
    assert any(t["trace_id"] == trace_id for t in recent)
