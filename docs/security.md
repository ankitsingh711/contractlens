# Security

> Status: implemented through Phase 7 (auth, structured errors, document-level authorization, rate limiting, upload content validation, audit logging, agent guardrails). See "Not yet implemented" at the bottom for what's still open.

## Authentication & authorization

- **Authentication**: email/password with bcrypt hashing (`passlib`), JWT bearer tokens (`PyJWT`, HS256, `SECRET_KEY` from environment — never hardcoded).
- **Multi-tenancy at the token level**: JWTs carry both `sub` (user id) and `org_id`. Every authenticated request resolves the current user server-side via `get_current_user`; the frontend never asserts identity, it only holds an opaque token.
- **Document-level authorization**: every document, conversation, agent run, evaluation run, and comparison query filters by `organization_id` server-side — a user cannot address another org's resource by ID even if they guess it (verified by cross-org tests on every one of those resource types).
- **Role-based access on sensitive endpoints**: `GET /api/audit-logs` requires `UserRole.ADMIN` — any other authenticated org member gets a 403, not a filtered response. This is the first endpoint in the app to differentiate by role rather than just by organization, deliberately: an audit trail is exactly the kind of resource where "any logged-in member" is too broad.

## Rate limiting (Phase 7)

Redis-backed request throttling (`app/core/rate_limit.py`), applied as global ASGI middleware rather than a per-route dependency so new endpoints are covered automatically. A fixed-window counter (`INCR` + `EXPIRE` per minute) keyed by the authenticated user's id when a valid JWT is present, falling back to client IP (respecting `X-Forwarded-For`, since the API sits behind a load balancer in the target AWS architecture — see `docs/architecture.md`) for unauthenticated requests like login/register, which is exactly where brute-force protection matters most.

**Only mutating requests are rate-limited** (POST/PUT/PATCH/DELETE) — GET/HEAD/OPTIONS are exempt, alongside `/api/health`/`/docs`/`/openapi.json`. This wasn't the original design (a request-agnostic limiter is simpler) but the app's own polling-based UX forced the distinction: document processing status and evaluation run status are polled via GET every ~1–1.5s while a background job runs, which can easily exceed a low per-minute budget under completely normal single-user use. The actual abuse surface this middleware needs to cover — login/register brute-forcing, write spam — is entirely on mutating requests, so exempting safe methods closes the real gap without breaking the app's own UI patterns.

On limit exceeded, returns the same structured `{error: {code: "RATE_LIMITED", message, request_id}}` shape as every other error, plus a `Retry-After` header. If Redis itself is unreachable, the middleware fails **open** (allows the request through, logs a warning) rather than closed — availability was judged more important than the marginal security gain, given this app has no other redundancy for Redis yet; a production deployment with a highly-available Redis cluster might reasonably flip that trade-off.

## Upload hardening (Phase 7)

- **File size limits**: `MAX_UPLOAD_SIZE_MB` (config), enforced before anything else touches the file.
- **MIME allowlist**: only PDF, DOCX, and TXT `Content-Type` values are accepted (`document_service.resolve_document_type`).
- **Content signature validation**: the client-supplied `Content-Type` header is a claim, not a fact — a request can set it to anything. `document_service._validate_file_content()` checks the file's actual bytes against its declared type (PDF must start with `%PDF-`, DOCX must start with the zip/OOXML signature `PK\x03\x04`, TXT must decode as UTF-8 and must *not* match either binary signature) before the file is stored or processed. A `.exe` renamed to `report.pdf` with a spoofed `Content-Type: application/pdf` is rejected at this check, not silently processed. See `tests/test_upload_mime_validation.py`.

## Audit logging (Phase 7)

`app/models/audit_log.py` / `app/services/audit_service.py`: a structured, org-scoped, queryable log of compliance-relevant actions — `user.register`, `user.login`, `user.login_failed`, `document.upload`, `document.delete`, `document.analyze`, `comparison.create` — each entry recording the acting user (when known), the affected resource, a small metadata payload (e.g. filename), the client IP, and a timestamp. Exposed via `GET /api/audit-logs` (admin-only, see above) and rendered in Settings for admin users.

**Design choice**: `log_action()` never raises — a failure to write an audit entry is logged and swallowed rather than propagated, so audit logging can never break the feature it's observing (the same fail-safe philosophy as the observability client in `app/observability/`, applied to security events instead of LLM traces).

**Known gap, stated plainly**: a failed login for an email that doesn't match any account is *not* audited, because `AuditLog.organization_id` is required (audit logs are inherently org-scoped for the "admin views their org's activity" use case) and there is no organization to attribute the attempt to. A failed login for a real account (wrong password) *is* audited, since that's the case an org admin actually cares about — "someone is guessing passwords against one of my users." A global, org-independent security log for unknown-account attempts would need a separate table and is out of scope here.

## Prompt injection guardrails (Phase 3, reused by the Phase 4 agent)

The QA prompt template (`prompts/qa/v1.txt`) places SYSTEM INSTRUCTIONS before an explicitly labeled EVIDENCE section, and instructs the model to treat evidence as untrusted document content, never as commands — verified by `tests/test_prompt_injection.py`, which asserts a malicious payload always lands after the instructions/evidence boundary, and that a fake citation marker embedded in document text is never treated as a real citation by `validate_citations()`. The agent's `reason` node uses this same prompt template rather than a separate mechanism.

## Tool-level authorization (Phase 4)

Every agent tool (`app/agents/tools/`) filters its own SQL query by `organization_id` rather than trusting the caller — so even if a future LLM-driven planner asked a tool for another org's `document_id`, the query itself returns nothing. This is defense at the same layer as the API endpoints, not just at the HTTP boundary.

## Tool input safety (Phase 4)

The `calculate` tool parses expressions with Python's `ast` module and only permits numeric literals and `+ - * / % **` — never `eval()`/`exec()` — so it cannot execute arbitrary code even if a malicious query tried to smuggle one in. See `tests/test_agent_tools.py::test_calculate_rejects_code_injection_attempts`.

## Structured errors (Phase 1)

API errors never leak stack traces or raw exception messages to the client — every error response is `{ error: { code, message, request_id } }`, with the unhandled-exception handler catching anything unexpected and returning a generic message while still logging the real exception server-side.

## Why environment-based config over hardcoded values

`app/core/config.py` centralizes every configurable value (secrets, provider selection, budgets, CORS origins) behind a single `Settings` class read from environment variables, so there is exactly one place secrets can leak from (and one place to audit), and so the same codebase runs in demo mode, local dev, and production by changing environment, not code.

## Not yet implemented

- **Fine-grained RBAC beyond the audit log**: `UserRole` (admin/member/viewer) exists on every user, but only `GET /api/audit-logs` currently checks it — document/chat/analysis endpoints treat every org member equally. A natural Phase 8+ extension, not built here to avoid speculative complexity ahead of an actual need.
- **Secrets management for production**: `.env` files are appropriate for local dev; a real deployment should pull secrets from AWS Secrets Manager or SSM Parameter Store rather than environment variables baked into a task definition — sketched in `docs/architecture.md`'s AWS section, not implemented (there's no AWS deployment yet — that's Phase 8).
- **Per-organization rate limit tiers**: the current limiter is a single global `RATE_LIMIT_PER_MINUTE` for every user; differentiated limits (e.g. higher for paying orgs) would need a plan/tier concept that doesn't exist yet.
