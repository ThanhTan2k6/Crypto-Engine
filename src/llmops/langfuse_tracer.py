"""
Langfuse Observability & LLMOps Tracing Client for CryptoIntel-Engine.
Monitors multi-agent reasoning, latency per specialist node, token usage, and verdict telemetry.
Operates gracefully with in-memory trace collection when Langfuse credentials are not provided.
"""

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Try importing Langfuse SDK; fallback gracefully if absent
try:
    from langfuse import Langfuse

    LANGFUSE_CLASS: Any = Langfuse
except ImportError:
    LANGFUSE_CLASS = None


class LangfuseAuditTracer:
    """
    LLMOps Tracer for the Multi-Agent Socratic Audit Pipeline.
    Records trace lifecycle, individual node spans, latency, and quality metadata.
    """

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        host: str | None = None,
    ) -> None:
        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        self._client: Any = None
        self._is_enabled: bool = False
        self._in_memory_traces: list[dict[str, Any]] = []

        if LANGFUSE_CLASS is not None and self.public_key and self.secret_key:
            try:
                self._client = LANGFUSE_CLASS(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host,
                )
                self._is_enabled = True
                logger.info("Langfuse observability initialized with host: %s", self.host)
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Failed to initialize Langfuse client: %s; using local trace buffer.", e)
                self._is_enabled = False
        else:
            logger.info("Langfuse credentials absent; operating in local observability mode.")
            self._is_enabled = False

    @property
    def is_enabled(self) -> bool:
        """Return True if connected to live Langfuse backend."""
        return self._is_enabled

    def trace_audit_start(
        self, trace_id: str, symbol: str, execution_mode: str, proposed_action: str | None = None
    ) -> dict[str, Any]:
        """Record the start of a multi-agent audit run."""
        trace_record: dict[str, Any] = {
            "trace_id": trace_id,
            "symbol": symbol.upper(),
            "execution_mode": execution_mode,
            "proposed_action": proposed_action,
            "start_time": time.perf_counter(),
            "timestamp": datetime.now(UTC).isoformat(),
            "spans": [],
            "status": "RUNNING",
        }
        self._in_memory_traces.append(trace_record)

        if self._is_enabled and self._client:
            try:
                self._client.trace(
                    id=trace_id,
                    name=f"CryptoAudit:{symbol.upper()}",
                    metadata={
                        "execution_mode": execution_mode,
                        "proposed_action": proposed_action or "NONE",
                    },
                    tags=["cryptointel", execution_mode.lower(), symbol.lower()],
                )
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Langfuse trace creation failed: %s", e)

        return trace_record

    def trace_node_span(
        self,
        trace_id: str,
        node_name: str,
        inputs: dict[str, Any] | None,
        outputs: dict[str, Any] | None,
        latency_ms: float,
    ) -> None:
        """Record an execution span for an individual agent specialist node."""
        span_data = {
            "node_name": node_name,
            "latency_ms": round(latency_ms, 2),
            "inputs_keys": list(inputs.keys()) if inputs else [],
            "outputs_keys": list(outputs.keys()) if outputs else [],
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Save to local buffer
        for t in self._in_memory_traces:
            if t["trace_id"] == trace_id:
                t["spans"].append(span_data)
                break

        if self._is_enabled and self._client:
            try:
                self._client.span(
                    trace_id=trace_id,
                    name=f"Node:{node_name}",
                    input=inputs,
                    output=outputs,
                    metadata={"latency_ms": latency_ms},
                )
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Langfuse span logging failed for node %s: %s", node_name, e)

    def trace_audit_end(
        self,
        trace_id: str,
        anti_fomo_verdict: str,
        fomo_index: float,
        fatal_questions: list[str],
        errors: list[str] | None = None,
    ) -> dict[str, Any]:
        """Finalize and close an audit trace with outcome metrics."""
        end_time = time.perf_counter()
        target_trace: dict[str, Any] | None = None

        for t in self._in_memory_traces:
            if t["trace_id"] == trace_id:
                total_duration_ms = (end_time - t["start_time"]) * 1000.0
                t["duration_ms"] = round(total_duration_ms, 2)
                t["anti_fomo_verdict"] = anti_fomo_verdict
                t["fomo_index"] = fomo_index
                t["fatal_questions_count"] = len(fatal_questions)
                t["errors"] = errors or []
                t["status"] = "FAILED" if errors else "COMPLETED"
                target_trace = t
                break

        if self._is_enabled and self._client:
            try:
                self._client.score(
                    trace_id=trace_id,
                    name="fomo_index",
                    value=fomo_index,
                    comment=f"Anti-FOMO Verdict: {anti_fomo_verdict}",
                )
            except (RuntimeError, ConnectionError, TimeoutError, ValueError, OSError) as e:
                logger.warning("Langfuse score logging failed: %s", e)

        return target_trace or {}

    def get_recent_traces(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return the most recent in-memory trace summaries."""
        return self._in_memory_traces[-limit:]


# Global singleton instance
llmops_tracer = LangfuseAuditTracer()
