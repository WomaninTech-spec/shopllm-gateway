# Architecture
 
## High-level view

┌──────────────┐ ┌─────────────────────────────────────────────┐ ┌──────────────┐
│ │ │ ShopLLM Gateway │ │ │
│ Client App │──────▶│ │──────▶│ Anthropic │
│ (e-commerce │ │ ┌────────┐ ┌────────┐ ┌──────────────┐ │ │ OpenAI │
│ service) │◀──────│ │ Auth │─▶│ PII │─▶│ Router │ │◀──────│ Mistral │
│ │ │ └────────┘ │ Redact │ │ (cost-aware) │ │ │ Ollama │
└──────────────┘ │ └────────┘ └──────────────┘ │ └──────────────┘
│ ┌────────┐ ┌────────┐ ┌──────────────┐ │
│ │ Rate │ │ Circuit│ │ Provider │ │
│ │ Limit │ │ Breaker│ │ Adapter │ │
│ └────────┘ └────────┘ └──────────────┘ │
│ │
│ ┌──────────────────────────────────────┐ │
│ │ Observability: logs, metrics, traces │──┼─▶ Prometheus / Grafana
│ └──────────────────────────────────────┘ │ BigQuery (audit)
└─────────────────────────────────────────────┘

 
## Key components
 
- **API layer (FastAPI)** — exposes an OpenAI-compatible REST API. Async-first.
- **Auth middleware** — validates an API key per tenant (simple bearer token in MVP).
- **PII redaction middleware** — scans the incoming prompt, masks detected PII, attaches a redaction report to the request context.
- **Router** — decides which provider + which model to call, based on request hints (task type, max_cost, max_latency) and runtime policies.
- **Provider adapters** — one class per provider (AnthropicAdapter, OpenAIAdapter, …) implementing a common `ChatProvider` interface. Easy to extend.
- **Rate limiter** — per-tenant request budget (token bucket).
- **Circuit breaker** — per-provider, opens on consecutive errors to prevent cascading failures.
- **Observability pipeline** — structured JSON logs (stdout), Prometheus `/metrics` endpoint, OpenTelemetry traces, optional BigQuery sink for long-term audit.
 
## Key architectural decisions (ADR-style)
 
1. **Language: Python 3.11+** — fastest path to ship, best AI SDK ecosystem, async with `asyncio` is sufficient for a gateway. Trade-off: lower raw throughput than Go, but acceptable for I/O-bound LLM calls (each call is 500ms-10s, CPU is not the bottleneck).
 
2. **Framework: FastAPI** — async-native, automatic OpenAPI doc generation, Pydantic for request validation, large community.
 
3. **API contract: OpenAI-compatible** — clients can use the official `openai` SDK pointed at our gateway URL. Zero learning curve, instant adoption.
 
4. **Storage:**
   - Hot path (logs, metrics): stdout JSON + Prometheus, scraped externally.
   - Audit trail: append-only writes to BigQuery (batched).
   - No application database in MVP — gateway is stateless.
 
5. **Deployment: containerized, target Cloud Run** — stateless service, scale-to-zero, pay-per-request. Terraform for IaC. GitHub Actions for CI/CD. Same Docker image runs locally with Docker Compose.
 
6. **Secrets management:** local = `.env.local` (gitignored). Production = GCP Secret Manager, mounted as env vars at boot.
 
7. **Multi-tenancy model:** tenant identified by API key. Per-tenant rate limits, per-tenant cost tracking. No cross-tenant data leakage by design (no shared cache in MVP).

