import uuid

import pytest

from app.agents.tools.calculate import CalculateInput, calculate
from app.agents.tools.registry import call_tool

pytestmark = pytest.mark.asyncio


async def test_calculate_evaluates_basic_arithmetic(db_session):
    result = await calculate(db_session, uuid.uuid4(), CalculateInput(expression="2 * 500000 * 0.02"))
    assert result.result == 20000.0


async def test_calculate_rejects_code_injection_attempts(db_session):
    with pytest.raises(ValueError):
        await calculate(
            db_session, uuid.uuid4(), CalculateInput(expression="__import__('os').system('echo pwned')")
        )


async def test_calculate_rejects_name_lookups():
    with pytest.raises(ValueError):
        await calculate(None, uuid.uuid4(), CalculateInput(expression="os.system('ls')"))


async def test_call_tool_returns_error_record_for_unknown_tool(db_session):
    record = await call_tool({}, "nonexistent_tool", {})
    assert record.error is not None
    assert "Unknown tool" in record.error


async def test_call_tool_returns_error_record_for_invalid_input(db_session):
    from app.agents.tools import build_tool_registry

    registry = build_tool_registry(db_session, uuid.uuid4())
    record = await call_tool(registry, "calculate", {"expression": ""})
    assert record.error is not None


async def test_call_tool_succeeds_for_valid_calculate_input(db_session):
    from app.agents.tools import build_tool_registry

    registry = build_tool_registry(db_session, uuid.uuid4())
    record = await call_tool(registry, "calculate", {"expression": "10 + 5"})
    assert record.error is None
    assert record.output["result"] == 15.0
