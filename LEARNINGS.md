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