import ast
import operator
import uuid

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}


class CalculateInput(BaseModel):
    expression: str = Field(min_length=1, max_length=200)


class CalculateOutput(BaseModel):
    result: float


class UnsafeExpressionError(ValueError):
    pass


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.operand))
    raise UnsafeExpressionError(f"Unsupported expression element: {ast.dump(node)}")


async def calculate(
    db: AsyncSession, organization_id: uuid.UUID, input: CalculateInput
) -> CalculateOutput:
    """Evaluates a plain arithmetic expression (e.g. contract fee math) —
    for questions like 'what is 2% of $500,000 over 3 years'. Parses via
    Python's `ast` module and only permits numeric literals and +-*/%**,
    so it can never execute arbitrary code (no `eval`/`exec` involved).
    """
    try:
        tree = ast.parse(input.expression, mode="eval")
        result = _eval_node(tree.body)
    except (SyntaxError, UnsafeExpressionError, ZeroDivisionError) as exc:
        raise ValueError(f"Invalid arithmetic expression: {exc}") from exc
    return CalculateOutput(result=result)
