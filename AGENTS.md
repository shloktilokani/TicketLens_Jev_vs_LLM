# Coding Agent Instructions

You are implementing **TicketLens_Jev_vs_LLM**. Treat this repository's documentation as the source of truth.

## 1. Read before coding

Read, in order:
1. `README.md`
2. `requirements.md`
3. `architecture.md`
4. `data-model.md`
5. `ai-evaluation.md`
6. `design.md`
7. `implementation.md`

Do not begin by generating a large amount of code. Follow the implementation phases and their acceptance criteria sequentially.

## 2. Autonomy expectations

- Make routine implementation decisions using the documented defaults.
- Do not ask the product owner questions for decisions already specified here.
- If an external API detail is uncertain, inspect the provider's current official documentation and implement against the current contract. Do not invent request fields, SDK methods, or pricing.
- If a decision is genuinely blocked (for example, a missing API key or unavailable local MongoDB), implement the surrounding code, provide a precise setup message, and continue with mock/test mode where possible.
- Maintain a `PROGRESS.md` checklist. Update it after each phase with completed work, tests run, and remaining blockers.
- Keep changes scoped. Do not introduce unrelated infrastructure or features.

## 3. Technical guardrails

- Use React + Vite + TypeScript.
- Use Tailwind CSS and shadcn/ui; keep components reusable and accessible.
- Use Python + FastAPI + Pydantic for the backend.
- Use the official `pymongo` package and MongoDB Community Edition locally. Do not add Docker for local development.
- Keep Jev and OpenAI integrations behind separate provider adapter modules and a shared normalized result contract.
- API keys must remain server-side in environment variables. Never place secrets in frontend code, Vite variables, source control, logs, or error responses.
- Use a single canonical taxonomy shared by the UI, backend validation, provider adapters, and evaluation code.
- Use stable IDs and UTC timestamps. Store timestamps as BSON dates.
- Validate all external provider responses before saving or returning them.
- Never send evaluation ground-truth labels, prior model outputs, or the manually selected final answer to either model.
- Never claim Jev generated free-form text. Jev's documented API returns typed decisions (choice, yes/no probability, score, etc.). Mark summary/resolution as unsupported for Jev unless TypeSafe officially adds a text-generation capability.
- Store raw provider request/response payloads for debugging, but redact credentials and sensitive headers. The application is a synthetic-data demo; do not use real customer data.
- Every provider attempt, including failures, must create an execution log whenever the backend has enough information to do so.
- A provider failure must not erase a successful result from the other provider.
- Do not silently retry paid requests. Retry only clearly transient failures with bounded attempts and documented backoff; never retry 400/401/403/402 by default.
- Make CSV imports idempotent and report valid, invalid, and duplicate rows separately.
- Keep UI state consistent with backend state; do not treat optimistic UI changes as successful until the API confirms them.

## 4. Definition of done for each phase

A phase is complete only when:
- Its acceptance criteria in `implementation.md` pass.
- Relevant automated tests exist and pass.
- Error, loading, and empty states are implemented where applicable.
- The application still starts using the documented local commands.
- `PROGRESS.md` is updated.

## 5. Required developer experience

Provide:
- Clear root-level README run instructions.
- Backend `.env.example`; never commit `.env`.
- A health endpoint and a database readiness check.
- Swagger/OpenAPI docs through FastAPI.
- Seed/sample CSV generation or an included sample CSV artifact.
- Unit tests for validation, provider normalization, cost calculations, imports, and deletion behavior.
- A final local verification checklist and a platform-neutral deployment-readiness checklist.

## 6. Scope exclusions

Do not add authentication, customer portal, roles, email sending, notifications, payment processing, external ticketing integrations, LangChain, n8n, Docker-based local MongoDB, or model fine-tuning in the initial version.
