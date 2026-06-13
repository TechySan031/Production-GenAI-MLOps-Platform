"""
Structured metrics logging — Azure Monitor observability foundation.

Phase 2 approach: log-based metrics.

Every LLM inference emits a structured JSON log entry with consistent field
names. Azure Monitor Log Analytics ingests container stdout automatically
when connected to a Container App. You can then build metric queries like:

    ContainerAppConsoleLogs_CL
    | where LogEntry contains "llm.inference.complete"
    | extend model = extract('"model":"([^"]+)"', 1, LogEntry)
    | summarize avg_latency=avg(todouble(extract('"latency_ms":([0-9.]+)', 1, LogEntry)))
               by model, bin(TimeGenerated, 1h)

Phase 3 migration path:
    Add azure-monitor-opentelemetry to pyproject.toml.
    Call AzureMonitorTraceExporter here alongside the log call.
    Zero changes to LLMService — this file is the only integration point.
"""

import logging
from dataclasses import asdict, dataclass

logger = logging.getLogger(__name__)


@dataclass
class InferenceMetrics:
    """Metrics captured for every LLM inference attempt (success or failure)."""

    # Correlation
    request_id: str
    environment: str

    # Provider context
    provider: str
    model: str

    # Performance
    latency_ms: float

    # Token usage
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    # Cost
    cost_usd: float

    # Outcome
    success: bool
    error_type: str | None = None


def record_inference_metrics(metrics: InferenceMetrics) -> None:
    """
    Emit inference metrics as a structured log entry for Azure Monitor.

    Uses the event name as the top-level message so Log Analytics
    can filter cheaply before parsing JSON fields.
    """
    event_name = "llm.inference.complete" if metrics.success else "llm.inference.error"
    logger.info(
        event_name,
        extra={
            "metric_type": "llm_inference",
            **asdict(metrics),
        },
    )
