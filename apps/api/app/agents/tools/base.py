import asyncio
import time
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger("agent.tools")

TOOL_TIMEOUT_SECONDS = 10.0


@dataclass
class ToolCallRecord:
    name: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    latency_ms: float
    error: str | None = None


async def run_tool(
    name: str,
    input_model: BaseModel,
    fn,
) -> ToolCallRecord:
    """Executes a tool with validation (the caller must pass an already-
    validated pydantic input model), a timeout, structured logging, and
    error containment — a failing tool becomes a recorded error on the
    agent state, not an unhandled exception that kills the whole run."""
    start = time.perf_counter()
    input_dict = input_model.model_dump(mode="json")
    logger.info("tool_call.start", tool=name, input=input_dict)

    try:
        result: BaseModel = await asyncio.wait_for(fn(input_model), timeout=TOOL_TIMEOUT_SECONDS)
        latency_ms = (time.perf_counter() - start) * 1000
        output_dict = result.model_dump(mode="json")
        logger.info("tool_call.success", tool=name, latency_ms=latency_ms)
        return ToolCallRecord(name=name, input=input_dict, output=output_dict, latency_ms=latency_ms)
    except asyncio.TimeoutError:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning("tool_call.timeout", tool=name, latency_ms=latency_ms)
        return ToolCallRecord(
            name=name,
            input=input_dict,
            output=None,
            latency_ms=latency_ms,
            error=f"Tool '{name}' timed out after {TOOL_TIMEOUT_SECONDS}s.",
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.error("tool_call.error", tool=name, latency_ms=latency_ms, error=str(exc))
        return ToolCallRecord(
            name=name, input=input_dict, output=None, latency_ms=latency_ms, error=str(exc)
        )
