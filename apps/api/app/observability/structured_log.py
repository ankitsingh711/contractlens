from app.core.logging import get_logger
from app.observability.base import AgentTrace, ObservabilityClient

logger = get_logger("observability")


class StructuredLogObservability(ObservabilityClient):
    """Fallback used when no Langfuse keys are configured. Logs the same
    trace data (prompts, model, tokens, cost, latency, steps, errors)
    as a structured JSON log line instead of sending it to Langfuse — the
    data isn't lost in demo mode, it's just not in Langfuse's UI. The
    Agent Runs page is the primary trace viewer for this app either way;
    Langfuse is an additional, optional export target."""

    def record_agent_trace(self, trace: AgentTrace) -> None:
        logger.info(
            "agent_trace",
            trace_id=trace.trace_id,
            organization_id=trace.organization_id,
            intent=trace.intent,
            model=trace.model,
            prompt_version=trace.prompt_version,
            evidence_score=trace.evidence_score,
            confidence=trace.confidence,
            input_tokens=trace.input_tokens,
            output_tokens=trace.output_tokens,
            estimated_cost_usd=trace.estimated_cost_usd,
            latency_ms=trace.latency_ms,
            step_count=len(trace.steps),
            error_count=len(trace.errors),
        )
