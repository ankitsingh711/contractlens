# Security

> Status: Phase 1 baseline (auth, password hashing, structured errors). Rate limiting, audit logging, and full authorization coverage land in Phase 7 — this document tracks what's implemented vs. planned.

## Implemented (Phase 1)

- **Authentication**: email/password with bcrypt hashing (`passlib`), JWT bearer tokens (`PyJWT`, HS256, `SECRET_KEY` from environment — never hardcoded).
- **Multi-tenancy at the token level**: JWTs carry both `sub` (user id) and `org_id`. Every authenticated request resolves the current user server-side via `get_current_user`; the frontend never asserts identity, it only holds an opaque token.
- **No secrets in source**: all credentials and keys are environment-driven (`app/core/config.py` via `pydantic-settings`); `.env` is gitignored, `.env.example` documents required variables without values.
- **Structured errors**: API errors never leak stack traces or raw exception messages to the client — every error response is `{ error: { code, message, request_id } }`, with the unhandled-exception handler catching anything unexpected and returning a generic message while still logging the real exception server-side.
- **Password requirements**: minimum 8 characters enforced at the schema layer (Pydantic), with room to strengthen as needed.

## Planned (Phase 7)

- **Document-level authorization**: once documents exist (Phase 2), every document query filters by `organization_id` server-side — a user cannot address another org's document by ID even if they guess it.
- **Rate limiting**: per-user/IP request throttling (`RATE_LIMIT_PER_MINUTE`, already reserved in config) via Redis.
- **Upload hardening**: MIME type validation, file size limits (`MAX_UPLOAD_SIZE_MB`, already reserved in config), and content sniffing beyond trusting the client-provided extension.
- **Audit logging**: structured, queryable log of who did what to which resource, for compliance-sensitive operations (document access, deletion, sharing).
- **Prompt injection guardrails**: covered in `docs/agent.md` — document content is treated as untrusted data, never concatenated into system/developer instructions.

## Why environment-based config over hardcoded values

`app/core/config.py` centralizes every configurable value (secrets, provider selection, budgets, CORS origins) behind a single `Settings` class read from environment variables, so there is exactly one place secrets can leak from (and one place to audit), and so the same codebase runs in demo mode, local dev, and production by changing environment, not code.
