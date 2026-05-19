"""Tests for rate limiter (429), circuit breaker (503), and PII redaction."""
import asyncio

import pytest

from shopllm.guardrails.circuit_breaker import CircuitBreaker, State
from shopllm.guardrails.rate_limit import RateLimiter
from shopllm.redaction.engine import RedactionEngine


# ── Rate Limiter (429) ───────────────────────────────────────────────────────

async def test_rate_limit_blocks_after_capacity():
    rl = RateLimiter(capacity=3, refill_per_sec=1.0)
    results = [await rl.allow("acme") for _ in range(4)]
    assert results == [True, True, True, False]


async def test_rate_limit_returns_429_key():
    rl = RateLimiter(capacity=2, refill_per_sec=1.0)
    await rl.allow("x")
    await rl.allow("x")
    assert await rl.allow("x") is False


async def test_rate_limit_isolates_tenants():
    rl = RateLimiter(capacity=1, refill_per_sec=1.0)
    assert await rl.allow("tenant-a") is True
    assert await rl.allow("tenant-a") is False
    assert await rl.allow("tenant-b") is True  # bucket indépendant


async def test_rate_limit_refills_over_time():
    rl = RateLimiter(capacity=1, refill_per_sec=10.0)
    assert await rl.allow("x") is True
    assert await rl.allow("x") is False
    await asyncio.sleep(0.15)  # 10 tok/s → ~1.5 tokens rechargés
    assert await rl.allow("x") is True


# ── Circuit Breaker (503) ────────────────────────────────────────────────────

async def test_breaker_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=60.0)
    for _ in range(3):
        await cb.on_failure()
    assert cb.state is State.OPEN


async def test_breaker_blocks_when_open():
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=60.0)
    await cb.on_failure()
    with pytest.raises(RuntimeError, match="OPEN"):
        await cb.before_call()


async def test_breaker_resets_on_success():
    cb = CircuitBreaker(failure_threshold=2, recovery_seconds=60.0)
    await cb.on_failure()
    assert cb.state is State.CLOSED  # seuil pas encore atteint
    await cb.on_success()
    await cb.on_failure()
    assert cb.state is State.CLOSED  # compteur remis à zéro par on_success


async def test_breaker_recovers_to_half_open():
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=0.05)
    await cb.on_failure()
    assert cb.state is State.OPEN
    await asyncio.sleep(0.1)
    await cb.before_call()  # ne lève pas → passé en HALF_OPEN
    assert cb.state is State.HALF_OPEN


# ── PII Redaction ────────────────────────────────────────────────────────────

def test_pii_email_and_phone_redacted():
    eng = RedactionEngine()
    r = eng.redact("Contactez support@acme.com ou +33 6 12 34 56 78 pour votre commande.")
    assert "support@acme.com" not in r.redacted_text
    assert "+33 6 12 34 56 78" not in r.redacted_text
    assert r.counts == {"EMAIL": 1, "PHONE_FR": 1}


def test_pii_credit_card_redacted():
    eng = RedactionEngine()
    r = eng.redact("Paiement avec 4111 1111 1111 1111 accepté.")
    assert "4111" not in r.redacted_text
    assert r.counts.get("CREDIT_CARD") == 1


def test_pii_clean_prompt_unchanged():
    eng = RedactionEngine()
    text = "Génère une description pour des baskets vegan."
    r = eng.redact(text)
    assert r.redacted_text == text
    assert r.total == 0
