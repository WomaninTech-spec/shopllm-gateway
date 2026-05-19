"""ShopLLM Gateway — FastAPI entrypoint with observability + PII redaction."""
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
from shopllm.obs.logging import configure_logging, get_logger
from shopllm.obs.pricing import estimate_cost_usd
from shopllm.providers.anthropic_adapter import AnthropicAdapter
from shopllm.redaction.engine import RedactionEngine
 
configure_logging()
log = get_logger()
 
app = FastAPI(
    title="ShopLLM Gateway",
    version="0.2.0",
    description="OpenAI-compatible LLM gateway for e-commerce teams.",
)
 
_anthropic = AnthropicAdapter()
_redactor = RedactionEngine()
 
 
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
    log.info(
        "request.end",
        request_id=request_id,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    return response
 
 
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
 
 
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(req: ChatCompletionRequest) -> ChatCompletionResponse:
    system = next((m.content for m in req.messages if m.role == "system"), None)
    user_parts = [m.content for m in req.messages if m.role == "user"]
    if not user_parts:
        raise HTTPException(status_code=400, detail="At least one user message is required.")
    raw_prompt = "\n\n".join(user_parts)
 
    # PII redaction BEFORE sending anything to the provider.
    redaction = _redactor.redact(raw_prompt)
    if redaction.total > 0:
        log.info("pii.redacted", request_id=None, counts=redaction.counts, total=redaction.total)
 
    started = time.perf_counter()
    try:
        result = await _anthropic.chat(
            redaction.redacted_text,
            model=req.model,
            max_tokens=req.max_tokens,
            system=system,
        )
    except Exception as exc:  # noqa: BLE001
        log.error("llm.call.error", model=req.model, error=str(exc))
        raise HTTPException(status_code=502, detail=f"Provider error: {exc}") from exc
    latency_ms = (time.perf_counter() - started) * 1000
    cost_usd = estimate_cost_usd(result.model, result.input_tokens, result.output_tokens)
 
    log.info(
        "llm.call.ok",
        provider="anthropic",
        model=result.model,
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