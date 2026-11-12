# Backend-specific instructions

Scope: all files under `backend/`. Follow root `AGENTS.md` too.

## Architecture
- Use FastAPI + Pydantic v2 for HTTP interfaces; SQLAlchemy 2 + Alembic + PostgreSQL for persistence.
- Organize code by responsibility (`api`, `core`, `db`, `models`, `schemas`, `services`) without unnecessary layers.
- Make database changes through versioned Alembic migrations; do not rely on `create_all()` in application startup.
- Use explicit response models and validate pagination, filters, and field lengths.
- Keep errors consistent, safe, and appropriate (`400`, `401`, `403`, `404`, `409`, `422`).

## Authentication and authorization
- Implement first-party session authentication with a cryptographically random opaque session token in an HttpOnly cookie; store only a hash of the session token server-side, with expiry and logout revocation.
- Hash passwords with Argon2id; never store plaintext passwords.
- Set `Secure` for session cookies in production; use appropriate `SameSite` settings and protect unsafe cookie-authenticated requests against CSRF. Support localhost HTTP for development without weakening production defaults.
- Every project/issue query must be scoped to the authenticated user on the server. Never trust a client-supplied owner/user ID.
- Unauthorized or cross-account resource access must not reveal another user's private data; prefer a non-disclosing `404` when applicable.
- Do not expose session tokens, password hashes, secret keys, or sensitive request data in logs.

## Quality
- Use dependency injection for database sessions and current-user resolution.
- Keep business rules in independently testable functions/services.
- Use parameterized ORM queries, explicit transactions, and predictable error handling.
- Provide pytest integration tests for registration/login/logout, projects/issues CRUD, validation, CSRF handling, and cross-account isolation.
- Provide `/health/live` (process) and `/health/ready` (database availability) endpoints.
- Do not add external auth providers, background queues, or cloud dependencies in milestone 1.
