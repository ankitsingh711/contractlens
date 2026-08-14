from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    input_per_1k: float
    output_per_1k: float


# Approximate published per-1K-token pricing (USD) for cost *estimation*,
# not billing — good enough to compare relative cost across runs/evals and
# to demonstrate cost tracking end to end. Update as provider pricing
# changes; this is intentionally a small, explicit table rather than a
# live pricing API call, which would add a network dependency to every
# agent run just to estimate a number that's already approximate.
_PRICING: dict[str, ModelPricing] = {
    "mock-llm": ModelPricing(input_per_1k=0.0, output_per_1k=0.0),
    "gpt-4o-mini": ModelPricing(input_per_1k=0.00015, output_per_1k=0.0006),
    "gpt-4o": ModelPricing(input_per_1k=0.0025, output_per_1k=0.01),
}

_DEFAULT_PRICING = ModelPricing(input_per_1k=0.00015, output_per_1k=0.0006)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = _PRICING.get(model, _DEFAULT_PRICING)
    return round(
        (input_tokens / 1000) * pricing.input_per_1k
        + (output_tokens / 1000) * pricing.output_per_1k,
        6,
    )
