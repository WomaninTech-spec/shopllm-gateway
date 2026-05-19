"""ShopLLM Gateway — v0.3.0: obs + redaction + guardrails + routing."""
from __future__ import annotations
 
import time
import uuid
 
from fastapi import FastAPI, HTTPException, Request
 
from shopllm.api.schemas import (
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Usage,
)
from shopllm.guardrails.circuit_breaker import CircuitBreaker
from shopllm.guardrails.rate_limit import RateLimiter
from shopllm.obs.logging import configure_logging, get_logger
from shopllm.obs.pricing import estimate_cost_usd
from shopllm.providers.anthropic_adapter import AnthropicAdapter
from shopllm.redaction.engine import RedactionEngine
from shopllm.routing.router import route
 
configure_logging()
log = get_logger()
 
app = FastAPI(
    title="ShopLLM Gateway",
    version="0.3.0",
    description="OpenAI-compatible LLM gateway for e-commerce teams.",
)
 
_anthropic = AnthropicAdapter()
_redactor = RedactionEngine()
_rate_limiter = RateLimiter(capacity=60, refill_per_sec=1.0)  # 60 req burst, 1 rps sustained
_breaker_anthropic = CircuitBreaker(failure_threshold=5, recovery_seconds=30.0)
 
 
@app.middleware("http")
async def request_logger(request: Request, call_next):
    request_id = uuid.uuid4().hex
    start = time.perf_counter()
    log.info("request.start", request_id=request_id, path=request.url.path, method=request.method)
    try:
        response = await call_next(request)
    except Exception as exc:  # noqa: BLE001
        duration_ms = (time.perf_counter() - start) * 1000
        log.error("request.error", request_id=request_id, duration_ms=round(duration_ms, 2), error=str(exc))
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    log.info("request.end", request_id=request_id, path=request.url.path,
             status_code=response.status_code, duration_ms=round(duration_ms, 2))
    return response
 
 
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
 
 
@app.get("/admin/breaker")
async def breaker_state() -> dict[str, str]:
    return {"anthropic": _breaker_anthropic.state.value}
 
 
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(req: ChatCompletionRequest) -> ChatCompletionResponse:
    # 1. Rate limit per tenant.
    if not await _rate_limiter.allow(req.tenant_id):
        log.warning("rate_limit.blocked", tenant_id=req.tenant_id)
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
 
    # 2. Extract content.
    system = next((m.content for m in req.messages if m.role == "system"), None)
    user_parts = [m.content for m in req.messages if m.role == "user"]
    if not user_parts:
        raise HTTPException(status_code=400, detail="At least one user message is required.")
    raw_prompt = "\n\n".join(user_parts)
 
    # 3. Redact PII.
    redaction = _redactor.redact(raw_prompt)
    if redaction.total > 0:
        log.info("pii.redacted", tenant_id=req.tenant_id,
                 counts=redaction.counts, total=redaction.total)
 
    # 4. Route to a model.
    decision = route(req.model, redaction.redacted_text, hint=req.task_hint)
    log.info("routing.decision", provider=decision.provider, model=decision.model, reason=decision.reason)
 
    # 5. Circuit breaker gate.
    try:
        await _breaker_anthropic.before_call()
    except RuntimeError as exc:
        log.error("breaker.open", provider=decision.provider)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
 
    # 6. Provider call.
    started = time.perf_counter()
    try:
        result = await _anthropic.chat(
            redaction.redacted_text,
            model=decision.model,
            max_tokens=req.max_tokens,
            system=system,
        )
        await _breaker_anthropic.on_success()
    except Exception as exc:  # noqa: BLE001
        await _breaker_anthropic.on_failure()
        log.error("llm.call.error", model=decision.model, error=str(exc))
        raise HTTPException(status_code=502, detail=f"Provider error: {exc}") from exc
 
    latency_ms = (time.perf_counter() - started) * 1000
    cost_usd = estimate_cost_usd(result.model, result.input_tokens, result.output_tokens)
 
    log.info(
        "llm.call.ok",
        tenant_id=req.tenant_id,
        provider=decision.provider,
        model=result.model,
        routing_reason=decision.reason,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=round(latency_ms, 2),
        cost_usd=round(cost_usd, 6),
        pii_hits=redaction.total,
    )
 
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=result.model,
        choices=[ChatChoice(message=ChatMessage(role="assistant", content=result.text))],
        usage=Usage(
            prompt_tokens=result.input_tokens,
            completion_tokens=result.output_tokens,
            total_tokens=result.input_tokens + result.output_tokens,
        ),
    )