# Architecture

> Status: Phase 1 (foundations). Updated as each phase lands — see the roadmap in the root README.

## System overview

ContractLens AI is a monorepo with two independently deployable applications:

- **`apps/web`** — Next.js 15 (App Router, TypeScript, Tailwind, shadcn/ui). Talks to the API over REST (and SSE for streaming responses, added in Phase 4).
- **`apps/api`** — FastAPI (Python 3.12, async SQLAlchemy). Owns all business logic, persistence, and AI orchestration.

They communicate over HTTP only — no shared runtime, no shared database access from the frontend. This keeps the two deployable independently (e.g., web on Vercel/CloudFront, API on ECS) and keeps all sensitive operations (document access control, LLM calls, retrieval) server-side.

## Why a monorepo, two apps

A single repo simplifies coordinated changes (e.g., a new API field and the UI that renders it) without the overhead of cross-repo versioning, while `apps/web` and `apps/api` remain independently buildable, testable, and deployable — there is no runtime coupling between them.

## Backend layering

```
app/
├── api/          # HTTP layer: routers, request/response wiring, auth dependency
├── core/         # config, security, logging, structured errors, middleware
├── db/           # session factory, declarative base, Alembic migrations
├── models/       # SQLAlchemy ORM models
├── schemas/      # Pydantic request/response schemas
├── services/      # business logic (auth_service, and later: document_service, retrieval, etc.)
├── agents/        # LangGraph agent + tools (Phase 4)
├── retrieval/      # hybrid retrieval, reranking (Phase 3)
├── evaluation/      # eval harness, regression testing (Phase 6)
└── observability/    # Langfuse integration, cost/latency tracking (Phase 6)
```

Routers depend on services, services depend on models/db — never the reverse. Pydantic schemas are the only types that cross the API boundary; ORM models never get serialized directly.

## Multi-tenancy

Every user belongs to an `Organization`. JWTs carry both `sub` (user id) and `org_id`, and (starting Phase 2, once there is org-scoped data beyond users) all queries for tenant-owned resources filter by `organization_id` — no user can address another org's data by ID alone. See `docs/security.md` for the full authorization model as it's built out.

## Error handling

All API errors are structured JSON: `{ "error": { "code", "message", "request_id" } }`. A `RequestContextMiddleware` assigns a request ID to every request (from the incoming `x-request-id` header if present) and logs a structured access record; the same ID is returned in the error body and the `x-request-id` response header, so a user-reported error can be traced through logs.

## Database

PostgreSQL, accessed exclusively through async SQLAlchemy sessions with Alembic-managed migrations. The `vector` extension (pgvector) was enabled from the first migration, before any vector columns existed, so Phase 2 could add `document_chunks.embedding` (with an HNSW index) plus a generated `tsvector`/GIN column for full-text search without a separate extension-enabling migration. Rationale for Postgres+pgvector over a dedicated vector database is in `docs/rag.md`.

## Document processing pipeline

Upload → object storage → parse (PDF/DOCX/TXT) → document-aware chunk → embed → index, implemented in `app/services/document_service.py` and run as a `FastAPI BackgroundTask` after the upload response returns. `Document.status` moves through `uploading → processing → parsing → chunking → embedding → indexing → completed` (or `failed`, with a stored `error_message`), which is what the frontend polls to show live progress. See `docs/rag.md` for why chunking is document-structure-aware rather than fixed-size, and the README's trade-offs section for why this runs in-process today instead of on a dedicated queue.

### Why asynchronous document processing

Parsing, chunking, and embedding a multi-page contract can take longer than a client wants to wait on an HTTP request. The upload endpoint does the fast, synchronous part (validate, store the file, create the `Document` row) and returns immediately with `status: processing`; the slow part runs as a background task the client polls for. This is also why `Document.status` has multiple intermediate values instead of just "processing"/"done" — the UI can show the user which stage is currently running, not just a spinner.

## Local development vs. production

`docker-compose.yml` runs Postgres, Redis, the API, and the web app together with health checks, matching the shape of the production deployment (see the AWS section of the README, expanded in Phase 8) without requiring AWS credentials for local work. The API container mounts the source tree as a volume and runs `uvicorn --reload` in dev; the production image (Phase 8) drops the reload flag and volume mount.
