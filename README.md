# ShopLLM Gateway
*The open-source LLM gateway purpose-built for e-commerce teams.*
 
![status](https://img.shields.io/badge/status-WIP-orange)
![license](https://img.shields.io/badge/license-MIT-blue)
  
## The Problem
 
E-commerce teams want to use LLMs in production — for product descriptions, customer support chatbots, smart search, review moderation, personalized emails. But putting LLMs in production safely is hard:
 
- Costs explode without visibility per feature, per tenant, per request.
- Customer PII (emails, addresses, order numbers, payment info) leaks into prompts.
- Every team reinvents retries, rate limiting, prompt injection detection.
- Switching providers (Anthropic ↔ OpenAI ↔ Mistral) means rewriting 20 services.
- No unified observability: no p95 latency, no error budget, no cost-per-feature dashboard.
 
ShopLLM Gateway solves this with a single, opinionated entry point between your e-commerce apps and any LLM provider.
 
## Who is it for?
 
- **Platform / SRE engineers** in 50-to-500-person e-commerce companies who own AI infrastructure and need observability, cost control, and security guarantees by default.
- **Backend engineers** in product squads who want a simple, OpenAI-compatible API to call from their service, without worrying about retries, PII, or provider lock-in.
 
## What it does (MVP)
 
- **Unified API** — OpenAI-compatible `/v1/chat/completions` endpoint, works with any existing OpenAI SDK.
- **Multi-provider routing** — Anthropic (Claude), OpenAI, with a pluggable adapter pattern for more.
- **Cost-aware model routing** — automatically pick a cheaper/smaller model for simple tasks (e.g. Haiku for classification, Sonnet for generation).
- **PII redaction** — detect and mask emails, phone numbers, addresses, order IDs, and payment info before requests leave your perimeter.
- **Observability built-in** — structured logs, Prometheus metrics, p95 latency, cost-per-call, error rate, fallback rate, exposed via Grafana dashboards.
- **Guardrails** — per-tenant rate limiting, circuit breaker per provider, retry budget, basic prompt injection detection.
- **Audit trail** — every call logged with prompt hash, user, tenant, cost, latency, model, redaction events. GDPR-friendly retention policies.
 
## What it does NOT do (non-goals)
 
- ❌ **No fine-tuning** — we are a runtime layer, not a training platform.
- ❌ **No vector database** — bring your own (Pinecone, Weaviate, pgvector). We focus on the LLM call itself.
- ❌ **No agent framework** — no chains, no tools, no planners. Use LangChain or LlamaIndex on top of us if you need that.
- ❌ **No prompt management UI** — prompts live in your codebase, where they belong.
- ❌ **No fancy frontend** — we ship an API and a metrics dashboard. That's it.
 
## Why another LLM gateway?
 
Generic gateways (LiteLLM, Portkey, Helicone, Kong AI Gateway, Cloudflare AI Gateway) are excellent but generic. ShopLLM Gateway is **opinionated for e-commerce**:
 
- PII detectors trained on e-commerce data (order IDs, SKUs, billing addresses, not just generic regex).
- Pre-packaged use cases: product description generation, review moderation, customer support, search re-ranking.
- Metrics grouped by e-commerce-relevant dimensions (per-storefront, per-locale, per-feature).
- Documentation and examples written for e-commerce engineers, not ML researchers.
 
## Status
 
🚧 Work in progress. MVP roadmap below.
 
## Roadmap
 
- [x] M1 — Hello LLM: minimal Anthropic + OpenAI clients
- [x] M2 — FastAPI gateway with unified `/v1/chat/completions`
- [x] M3 — PII redaction middleware
- [x] M4 — Cost tracking & smart model routing
- [x] M5 — Observability: structured JSON logs, request-ID propagation, per-call cost estimation
- [x] M6 — Guardrails: per-tenant rate limiting, circuit breaker, retry budget
- [x] M7 — Deployment: Docker (linux/amd64) + Cloud Run + Terraform + DEPLOY.md runbook
- [ ] M8 — Productization (docs site, examples, launch)
 
## License
 
MIT
 
## Author
 
Built by Barbara Teslar — Platform Engineering Manager, focused on safe & reliable AI infrastructure.
