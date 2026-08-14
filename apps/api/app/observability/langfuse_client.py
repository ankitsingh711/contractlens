from langfuse import Langfuse

from app.core.logging import get_logger
from app.observability.base import AgentTrace, ObservabilityClient

logger = get_logger("observability.langfuse")


class LangfuseObservability(ObservabilityClient):
    """Sends agent traces to Langfuse (cloud or self-hosted — whatever
    LANGFUSE_HOST points at). All calls are wrapped defensively: a
    Langfuse outage or SDK error must never break the agent run itself,
    since observability is an export target, not a dependency of the
    feature it's observing.
    """

    def __init__(self, public_key: str, secret_key: str, host: str):
        self._client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)

    def record_agent_trace(self, trace: AgentTrace) -> None:
        try:
            lf_trace = self._client.trace(
                id=trace.trace_id,
                name="agent_run",
                input=trace.query,
                output=trace.answer,
                metadata={
                    "organization_id": trace.organization_id,
                    "intent": trace.intent,
                    "evidence_score": trace.evidence_score,
                    "confidence": trace.confidence,
                },
                tags=[t for t in [trace.intent] if t],
            )

            for step in trace.steps:
                lf_trace.span(
                    name=step.name,
                    input=step.input,
                    output=step.output,
                    level="ERROR" if step.error else "DEFAULT",
                    status_message=step.error,
                )

            if trace.model:
                lf_trace.generation(
                    name="reason",
                    model=trace.model,
                    input=trace.query,
                    output=trace.answer,
                    usage={
                        "input": trace.input_tokens,
                        "output": trace.output_tokens,
                        "unit": "TOKENS",
                    },
                    metadata={
                        "prompt_version": trace.prompt_version,
                        "estimated_cost_usd": trace.estimated_cost_usd,
                    },
                )
        except Exception as exc:
            logger.warning("langfuse.record_trace_failed", trace_id=trace.trace_id, error=str(exc))
