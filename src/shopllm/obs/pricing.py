"""Static pricing table. Update as providers change prices.
 
Prices in USD per 1M tokens, last updated 2026-05.
"""
from __future__ import annotations
 
from dataclasses import dataclass
 
 
@dataclass(frozen=True, slots=True)
class ModelPrice:
    input_per_million: float
    output_per_million: float
 
 
PRICING: dict[str, ModelPrice] = {
    # Anthropic
    "claude-haiku-4-5": ModelPrice(1.00, 5.00),
    "claude-3-5-haiku-latest": ModelPrice(0.80, 4.00),
    "claude-sonnet-4-5": ModelPrice(3.00, 15.00),
    # OpenAI
    "gpt-4o-mini": ModelPrice(0.15, 0.60),
    "gpt-4o": ModelPrice(2.50, 10.00),
}
 
 
def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price = PRICING.get(model)
    if price is None:
        return 0.0
    return (
        input_tokens * price.input_per_million / 1_000_000
        + output_tokens * price.output_per_million / 1_000_000
    )