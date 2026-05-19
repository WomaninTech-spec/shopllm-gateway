"""Cost-aware model router. Picks cheap models for simple tasks."""
from __future__ import annotations
 
from dataclasses import dataclass
from typing import Literal
 
TaskHint = Literal["auto", "simple", "complex", "creative"]
 
 
@dataclass(frozen=True, slots=True)
class RoutingDecision:
    provider: str       # "anthropic" | "openai"
    model: str
    reason: str
 
 
# Simple heuristic table. Extend later with per-tenant policy.
CHEAP_ANTHROPIC = "claude-haiku-4-5"
STRONG_ANTHROPIC = "claude-sonnet-4-5"
 
 
def route(
    requested_model: str,
    prompt: str,
    hint: TaskHint = "auto",
) -> RoutingDecision:
    # 1. Explicit user model wins, unless "auto".
    if requested_model and requested_model != "auto":
        return RoutingDecision(
            provider="anthropic",
            model=requested_model,
            reason="explicit_model_requested",
        )
 
    # 2. Hints override heuristic.
    if hint in ("simple",):
        return RoutingDecision("anthropic", CHEAP_ANTHROPIC, "hint=simple")
    if hint in ("complex", "creative"):
        return RoutingDecision("anthropic", STRONG_ANTHROPIC, f"hint={hint}")
 
    # 3. Auto heuristic: short prompt -> cheap; long -> strong.
    prompt_len = len(prompt)
    if prompt_len < 400:
        return RoutingDecision("anthropic", CHEAP_ANTHROPIC, "auto:short_prompt")
    return RoutingDecision("anthropic", STRONG_ANTHROPIC, "auto:long_prompt")