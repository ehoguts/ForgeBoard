# ForgeBoard — product and technical specification

## Product
ForgeBoard is a compact web app for tracking software projects and their issues. It is intentionally designed as a portfolio-quality **vertical slice** that can later grow into a cloud-deployed, monitored, secured application. The MVP is personal-account-based (no teams/multi-tenant organizations yet).

## Milestone 1 (MVP) — user-visible behavior
1. A visitor can register with email and password, log in, log out, and view the current account.
2. Authenticated users can create, list, rename/update, view, and delete their own projects. A project has a name and optional description.
3. Within a project, users can create, list, update, and delete issues. Fields: title, optional description, status (`todo`, `in_progress`, `done`), priority (`low`, `medium`, `high`), optional due date, timestamps.
4. Issues can be filtered by status and priority, searched by title, and listed in predictable newest-first order with pagination.
5. A simple dashboard displays project count, total issues, and issue counts by status, scoped to the current user.
6. Users cannot read, mutate, or infer private project/issue data belonging to another account.
7. The UI works on desktop and mobile, and handles loading, empty, validation, and error states.

## Required API contracts
Use versioned JSON endpoints under `/api/v1`. Exact nested paths may be improved if documented consistently.
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- A documented CSRF-token bootstrap or equivalent mechanism for browser writes.
- `GET|POST /api/v1/projects`
- `GET|PATCH|DELETE /api/v1/projects/{project_id}`
- `GET|POST /api/v1/projects/{project_id}/issues`
- `GET|PATCH|DELETE /api/v1/issues/{issue_id}`
- `GET /api/v1/dashboard/summary`
- `GET /health/live`, `GET /health/ready`

## Technical architecture
- Monorepo: `backend/`, `frontend/`, `infra/`, `docs/`.
- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, pytest.
- Frontend: React, TypeScript, Vite, React Router, TanStack Query, Vitest and React Testing Library.
- Development: Docker Compose. Vite proxies `/api` to backend to keep browser traffic on the same origin.
- Auth: opaque server-side sessions, HttpOnly cookie, Argon2id password hashing, CSRF protection, server-side authorization.
- API: OpenAPI docs in local development; clear errors; validated inputs and paginated lists.

## Data model (minimum)
- `users`: id, email (unique), password_hash, created_at.
- `sessions`: id, user_id, token_hash (unique), expires_at, revoked_at, created_at.
- `projects`: id, owner_id, name, description, created_at, updated_at.
- `issues`: id, project_id, title, description, status, priority, due_date, created_at, updated_at.
- Use sensible indexes and foreign keys. Document deletion behavior (e.g. project deletion cascading to its issues).

## Local development acceptance criteria
- `.env.example`, `.gitignore`, `.dockerignore`, `compose.yaml`, and documented README commands exist.
- `docker compose up --build` starts a usable local stack; migrations are applied explicitly or by a documented safe local-only startup step.
- A developer can register two accounts and verify isolation of project and issue data.
- Automated API tests verify CRUD, auth, validation, CSRF, and account isolation.
- Frontend tests cover representative forms and state handling.
- README includes stack, architecture overview, setup, common commands, tests, and screenshots/illustrative UI captures when available.
- The codebase has formatting, linting, basic type checks, and clearly reported verification results.

## Non-goals for milestone 1
- No billing, email invitations, teams, RBAC, OAuth/social login, Kubernetes, queues, WebSockets, microservices, or mobile apps.
- No cloud deployments, Terraform provisioning, GitHub Actions pipelines, security scanner integration, or Grafana/Prometheus stack yet. These are deliberate later milestones.
- No production launch or production-readiness claim merely because the local MVP works.
