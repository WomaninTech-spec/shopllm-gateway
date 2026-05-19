# What I learned building ShopLLM Gateway may18 2026

# What I learned building ShopLLM Gateway
 
A running journal — raw, honest, dated. This is the artifact I'll turn into blog posts, talks, and training material.
 
---
 
## Day 1 — [today's date]
 
### What I did
- Set up the project skeleton (repo, README, ARCHITECTURE, gitignore).
- Defined the product vision and non-goals.
- Made first architectural decisions.
 
### What I learned
- Writing non-goals before writing code is what protects a project from scope creep.
- An OpenAI-compatible API contract is a strategic choice: it removes adoption friction to zero.
- PII redaction belongs in a middleware, not in each application — single point of enforcement.
 
### What confused me
- (to fill in as you go)
 
### Next session
- Hello LLM: write a minimal Anthropic client in Python.

---
 
## Day 2 — [today's date]
 
### What I did
- Wired Anthropic SDK with async client and tenacity-based retry.
- Built a provider-agnostic `ChatResult` dataclass to decouple my code from any SDK shape.
- Made first real LLM call from my own infrastructure.
 
### What I learned
- The adapter pattern is what will let me plug OpenAI, Mistral, Ollama tomorrow without touching the rest of the code.
- Token counts come from the provider response — they will be the basis of cost tracking later.
- `pydantic-settings` + `.env.local` is the clean way to handle secrets locally.

---
 
## Day 3 — [today's date]


### What I did
- Built an OpenAI-compatible FastAPI endpoint backed by my Anthropic adapter.
- Proved drop-in compatibility with the official `openai` Python SDK.
- Added structured JSON logging, request-ID propagation, latency measurement, and per-call cost estimation.
 
### What I learned
- Adopting OpenAI's API contract removes 100% of the integration cost for any future user.
- JSON logs are not optional — they are the substrate for SLOs, FinOps, and incident forensics.
- `request_id` propagation is the cheapest reliability investment with the highest ROI.
 
### Trophy
Any app that already uses the `openai` SDK can talk to my gateway by changing one line: `base_url`.

---

## Day 4 — 19 May 2026

### What I shipped
- E-commerce-aware PII redaction with audit reports + unit tests.
- Production-grade guardrails: token-bucket rate limiter, circuit breaker per provider.
- Cost-aware multi-model routing (Haiku/Sonnet auto-selection).
- Containerized, deployed to Cloud Run via Terraform, GitHub Actions pipeline on tag.
 
### Key insights
- PII redaction in the gateway is a structural compliance control — not "nice to have".
- Circuit breakers prevent cascading failures when a provider degrades; the alternative (retries everywhere) makes things worse.
- The OpenAI-compatible API contract + cost-aware routing gives users a "cut your bill 3x without changing code" pitch.
 
### Numbers to remember
- For a 200-input / 400-output token call: Haiku ≈ $0.0022, Sonnet ≈ $0.0066 → ~3x ratio. Most classification/short-rewrite tasks belong on Haiku.

### What I did
- Fixed the French phone regex that was silently never matching.
- Fixed a duplicate class definition in `schemas.py` and added the missing `ChatCompletionResponse`.
- Wrote 11 tests covering rate limiting (429), circuit breaker (503), and PII redaction.
- Dockerized the app properly with a non-root user and Cloud Run `PORT` support.
- Deployed to Google Cloud Run via Terraform: Artifact Registry, Secret Manager, Service Account, Cloud Run v2.
- Wrote `DEPLOY.md` — a step-by-step runbook for the full deployment pipeline.

### What I learned

**Regex:**
`\b` (word boundary) only works between `\w` and `\W` characters. `+` is not a `\w` character, so `\b\+33` never matches anything. Use `(?<!\w)` (negative lookbehind) instead — same intent, works with any character.

**Git:**
Always run `git rev-parse --show-toplevel` to confirm which repo git is actually operating on. When there's no `.git` in the current folder, git silently walks up the tree and can end up operating on your home directory.

**pytest:**
`testpaths = tests` in `pytest.ini` restricts collection to the `tests/` folder. Without it, pytest picks up any file matching `test_*.py` anywhere in the project — including manual scripts in `scripts/`.
`asyncio_mode = auto` in `pytest.ini` (pytest-asyncio >= 0.21) makes all `async def test_*` functions automatically recognized as async tests without requiring `@pytest.mark.asyncio` on each one.

**Docker + Apple Silicon:**
Docker on an M1/M2/M3 Mac builds `linux/arm64` images by default. Cloud Run (and most cloud services) run `linux/amd64`. Always build with `docker buildx build --platform linux/amd64` for production. The failure mode is silent at build time and only surfaces as `exec format error` at container startup.

**Google Cloud auth — two separate credentials:**
- `gcloud auth login` → authenticates *you* for CLI commands (`gcloud run deploy`, `gcloud secrets`, etc.)
- `gcloud auth application-default login` → authenticates the *machine* for SDKs and tools like Terraform that use Application Default Credentials (ADC). Forgetting this is the #1 reason Terraform fails with "could not find default credentials".

**Terraform:**
- `terraform import` adopts an existing cloud resource into the state file. Essential when you create something manually before running Terraform (or to avoid destroying and recreating a resource).
- Use `-target=resource.name` to apply only specific resources — useful for a bootstrap phase where the registry needs to exist before you can push an image.
- `deletion_protection = true` (default in Google provider v6 for Cloud Run) prevents Terraform from destroying the service. Set it to `false` before trying to replace a service.
- HCL blocks with multiple arguments must be multi-line. `variable "x" { type = string  default = "y" }` is invalid — each argument on its own line.

**Cloud Run:**
Cloud Run injects a `PORT` environment variable into the container. Your app must listen on `$PORT`, not a hardcoded port. The safest CMD: `uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}`.

### What confused me
- Why `gcloud auth login` wasn't enough for Terraform. The distinction between user credentials (for the CLI) and application default credentials (for SDKs) is non-obvious but important.
- Why Terraform marked the service as "tainted" after a failed deployment and then couldn't destroy it due to `deletion_protection`. The fix was to untaint it in state, then apply in two passes: first to update `deletion_protection`, then to recreate.

### Trophy
`curl https://shopllm-gateway-1032746299850.europe-west1.run.app/health` returns `{"status":"ok"}` — the gateway is live on Cloud Run, served from a real Docker image pushed to Artifact Registry, with the Anthropic API key stored securely in Secret Manager.

---

## Day 5 — 20 May 2026

### What I did
- Wired authentication and usage tracking into the gateway.
- Created `shopllm.db.models`: three SQLAlchemy ORM tables (`Tenant`, `ApiKey`, `UsageEvent`).
- Created `shopllm.db.session`: async SQLAlchemy engine + `SessionLocal` factory backed by Postgres.
- Created `shopllm.auth.api_keys`: API key generation (`secrets.token_urlsafe`) and SHA-256 hashing.
- Created `shopllm.auth.deps`: FastAPI `authenticate` dependency — reads the Bearer token, hashes it, looks it up in Postgres, returns the `Tenant`.
- Updated `chat_completions` in `main.py`: injected `tenant: Tenant = Depends(authenticate)`, replaced `req.tenant_id` with `tenant.id`, added a `UsageEvent` write after every successful LLM call.
- Fixed `config.py`: `database_url` and `api_key_prefix` were floating at module level outside the `Settings` class — moved them inside so pydantic-settings picks them up from env vars.
- Ran `scripts/bootstrap_db.py` to create tables and seed the first tenant + API key.

### What I learned

**FastAPI `Depends` pattern:**
`Depends(authenticate)` is FastAPI's dependency injection. The function `authenticate` runs before the handler, can raise `HTTPException`, and its return value is injected as a parameter. This is the idiomatic way to handle auth, DB sessions, and any shared setup — keeps handlers clean and the logic testable in isolation.

**SQLAlchemy async setup — three mandatory pieces:**
1. `create_async_engine(url)` — the connection pool. URL must use an async driver (`postgresql+asyncpg://`).
2. `sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)` — the session factory. `expire_on_commit=False` is critical: without it, accessing ORM attributes after `await s.commit()` triggers a lazy load which fails in async context.
3. `async with SessionLocal() as s:` — opens a session, auto-closes on exit. Never share a session across requests.

**Why SHA-256, not bcrypt, for API keys:**
bcrypt is designed for passwords (short, human-chosen, low entropy). API keys are long random tokens (`secrets.token_urlsafe(32)` = 256 bits of entropy) — they don't need bcrypt's slow hashing. SHA-256 is fast and perfectly safe here because there's nothing to brute-force.

**pydantic-settings: fields must be inside the class:**
A `Field(...)` defined at module level (outside the `Settings` class body) is just a plain Python variable — pydantic-settings never sees it and can't load it from env vars. Every configurable value must be a class-level annotation inside the `Settings` class.

**Postgres already running on 5432:**
When a port conflict happens at `docker run`, Docker creates the container but doesn't start it. Always check with `docker ps` what's already on the port and what credentials it uses before trying to create a new container.

### What confused me
- Why `expire_on_commit=False` is needed. SQLAlchemy marks ORM objects as "expired" after a commit (to force a fresh DB read on next access). In async code there's no implicit I/O, so accessing an expired attribute raises a `MissingGreenlet` error. Disabling expiry keeps the Python object usable after commit without a round-trip.
- Why `psql -U postgres` failed on the existing container. The default superuser is only named `postgres` when the image is started with `POSTGRES_USER=postgres`. This container used `admin`, so the correct command was `psql -U admin -d postgres`.

### Trophy
`PYTHONPATH=src python scripts/bootstrap_db.py` printed `Tenant: 1` and a live API key. The gateway now has a real identity layer: every request must carry a valid Bearer token, every call is persisted to Postgres.