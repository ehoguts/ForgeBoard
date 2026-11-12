# ForgeBoard

[![CI](https://github.com/ehoguts/ForgeBoard/actions/workflows/ci.yml/badge.svg)](https://github.com/ehoguts/ForgeBoard/actions/workflows/ci.yml)
[![Security](https://github.com/ehoguts/ForgeBoard/actions/workflows/security.yml/badge.svg)](https://github.com/ehoguts/ForgeBoard/actions/workflows/security.yml)

Phase 2 adds automated quality/build checks, CodeQL, dependency audits, and container vulnerability gates. Read the [delivery guide](docs/DELIVERY.md), [threat model](docs/THREAT_MODEL.md), [security policy](SECURITY.md), and [Phase 2 validation evidence](docs/PHASE2_VALIDATION.md). The application remains local; these workflows do not deploy or publish images.

ForgeBoard is a small issue tracker for personal software projects. Phase 1 includes account registration, login/logout, project and issue CRUD, issue search and filters, pagination, and an account-scoped dashboard.

The stack is FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 16, React, TypeScript, Vite, React Router, and TanStack Query. It runs locally without cloud accounts or paid services. Read [the product specification](docs/PROJECT_SPEC.md), [architecture decisions](docs/ARCHITECTURE.md), and [roadmap](docs/ROADMAP.md).

![ForgeBoard dashboard on desktop](docs/screenshots/dashboard-desktop.png)

Captured from the running Compose stack. See the [mobile dashboard](docs/screenshots/dashboard-mobile.png) and [project with issue filters](docs/screenshots/project-desktop.png).

## Start the local stack

Install Docker with the Compose v2 plugin. Docker Desktop must be running and configured for Linux containers. Run these commands from the repository root:

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up --build
```

On Linux/macOS, use `cp .env.example .env` for the first command. The first build needs internet access to retrieve images and dependencies. The example password is only for a disposable local database. Keep `.env` out of version control.

Open [ForgeBoard](http://localhost:5173). Always use this origin for the browser UI. The API's [OpenAPI documentation](http://localhost:8000/docs), [liveness](http://localhost:8000/health/live), and [database readiness](http://localhost:8000/health/ready) are also available. PostgreSQL is reachable only inside the Compose network; no database port is published.

The database health check gates API startup. The API container runs `alembic upgrade head` before Uvicorn. This migration step is intentional for the single-instance local stack; application startup does not call `create_all()`. The frontend starts after API readiness succeeds.

To run in the background and inspect status/logs:

```powershell
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 backend frontend
```

## Demonstrate the complete flow

1. Register an account, then log in with that email and password.
2. Create a project, open it, and create issues with different statuses, priorities, and due dates.
3. Search by title and combine status and priority filters. Refresh the page to verify URL filter state. Change an issue to **Done**, edit its fields, and inspect the dashboard counts.
4. Rename a project, update its description, and delete an issue. Project deletion also permanently deletes its issues; the interface asks for confirmation.
5. Log out. Private pages must require authentication again.

For an account-isolation demonstration, use two separate browser profiles, or a normal window and an incognito window:

1. In account A, create a project and issue; note their IDs from the URL/API responses.
2. In account B, verify its project list and dashboard have no A data.
3. While signed in as B, open `/api/v1/projects/A_PROJECT_ID` and `/api/v1/issues/A_ISSUE_ID` through the frontend origin. Both must return `404`.
4. With B's CSRF token, attempt PATCH/DELETE requests against A's IDs. Both must return `404`; a missing/incorrect CSRF token instead returns `403` before resource access.
5. Return to A and verify its data is intact. Automated API tests exercise these boundaries as well.

You can reproduce the write check in B's browser developer console. Replace the two IDs with A's IDs:

```javascript
const { csrf_token } = await fetch('/api/v1/auth/csrf').then(r => r.json());
await fetch('/api/v1/projects/A_PROJECT_ID', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token },
  body: JSON.stringify({ name: 'Forbidden change' }),
}).then(r => r.status); // 404
await fetch('/api/v1/issues/A_ISSUE_ID', {
  method: 'DELETE',
  headers: { 'X-CSRF-Token': csrf_token },
}).then(r => r.status); // 404
```

## Migrations and database access

The normal startup applies migrations automatically. To inspect the current revision or explicitly reapply pending migrations:

```powershell
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec database psql -U forgeboard -d forgeboard
```

The `psql` command assumes the example database/user names. If you change them in `.env`, adjust the command. Exit `psql` with `\q`. Schema changes belong in versioned Alembic revisions under `backend/alembic/versions/`.

## Run without containers

This alternative needs Python 3.12+, Node.js 24.22+, npm, and a running local PostgreSQL 16 installation. Keep PostgreSQL bound to loopback and create a dedicated development role/database. For a fresh local PostgreSQL installation, open `psql -h localhost -U postgres` as its administrator and run:

```sql
CREATE USER forgeboard WITH PASSWORD 'forgeboard_local_only';
CREATE DATABASE forgeboard OWNER forgeboard;
```

Use your own local credentials if these names already exist. The following PowerShell commands assume PostgreSQL is on port 5432. The root `.env` file is read by Compose; for this host workflow, set environment variables in the terminal explicitly.

In the first terminal, from the repository root:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:DATABASE_URL = "postgresql+psycopg://forgeboard:forgeboard_local_only@127.0.0.1:5432/forgeboard"
$env:COOKIE_SECURE = "false"
$env:APP_ORIGIN = "http://localhost:5173"
$env:SESSION_TTL_HOURS = "24"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, from the repository root:

```powershell
Set-Location frontend
npm ci --no-audit --no-fund
$env:API_PROXY_TARGET = "http://127.0.0.1:8000"
npm run dev -- --host 127.0.0.1
```

Open [http://localhost:5173](http://localhost:5173). On Linux/macOS, replace `.venv\Scripts\python.exe` and `.venv\Scripts\alembic.exe` with `.venv/bin/python` and `.venv/bin/alembic`, and use `export NAME=value` instead of PowerShell's `$env:NAME = "value"`. Stop each server with `Ctrl+C`; the database remains intact. New backend terminals need the same environment variables.

## Quality checks

Run the checks inside the built containers so a host Python/Node installation is unnecessary:

```powershell
docker compose exec backend python -m pytest
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
docker compose exec backend mypy app
docker compose exec frontend npm test
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
docker compose exec frontend npm run build
docker compose exec frontend npm run format:check
```

API tests cover registration/login/logout, session expiry/revocation, validation, CSRF enforcement, project/issue CRUD, filtering/pagination, dashboard counts, and two-account isolation. Frontend tests cover representative authentication and issue forms, filtering, and async/error states. Test behavior and the validation results from this implementation session are recorded in [VALIDATION.md](docs/VALIDATION.md).

### Optional browser smoke test

With the Compose stack running, the checked-in browser test exercises registration, login, project/issue creation and editing, status changes, combined URL filters, dashboard counts, mobile width, two-account isolation, confirmed deletion, and logout. It creates disposable local accounts and captures screenshots in `docs/screenshots/`. Its sample project is deleted after the assertions. Run from the repository root with Node.js 24.22+ and npm:

```powershell
npm install --prefix .local/browser-tools --no-save --no-audit --no-fund playwright@1.62.1
node .local/browser-tools/node_modules/playwright/cli.js install chromium
node scripts/browser-smoke.cjs
```

This optional tooling stays in the ignored `.local/` directory. To use an existing Chromium-family executable instead of downloading Chromium, set `BROWSER_PATH` to its absolute path. `PLAYWRIGHT_MODULE` can point to an existing Playwright package. Each run uses isolated browser contexts; it never opens a personal browser profile. The test targets only `http://localhost:5173`.

### Test against PostgreSQL

By default, the API suite creates a temporary SQLite database and applies the real Alembic migration before running. To verify PostgreSQL behavior as well, create a dedicated test database once, then run the same suite with `TEST_DATABASE_URL`:

```powershell
docker compose exec database createdb -U forgeboard forgeboard_test
docker compose exec -e TEST_DATABASE_URL=postgresql+psycopg://forgeboard:forgeboard_local_only@database:5432/forgeboard_test backend python -m pytest
```

These commands use the disposable credentials from `.env.example`. If you changed the database user/password in `.env`, adjust both commands accordingly. The `createdb` command is only needed the first time; reuse the existing test database for later runs.

The test harness requires the database name in `TEST_DATABASE_URL` to end in `_test`. It applies Alembic migrations and clears application tables in that database before each test. Always use a dedicated disposable test database: **never point the suite at the application database or any database containing data you want to retain**. The normal `forgeboard` application database is not touched by the commands above.

## Configuration

| Variable | Purpose | Local example |
| --- | --- | --- |
| `POSTGRES_USER` | Compose database user | `forgeboard` |
| `POSTGRES_PASSWORD` | Compose database password; use URL-safe characters | `forgeboard_local_only` |
| `POSTGRES_DB` | Compose application database | `forgeboard` |
| `DATABASE_URL` | Backend SQLAlchemy URL; constructed by Compose | `postgresql+psycopg://...@database:5432/forgeboard` |
| `APP_ORIGIN` | Expected browser origin for write requests | `http://localhost:5173` |
| `COOKIE_SECURE` | Send session cookie only over HTTPS; backend default is `true` | `false` for localhost HTTP |
| `SESSION_TTL_HOURS` | Absolute server-side session lifetime | `24` |
| `API_PROXY_TARGET` | Vite server's API target; set by Compose | `http://backend:8000` |

Registration creates an account; login creates a server-side session. Passwords use Argon2id. The opaque session cookie is `HttpOnly` and `SameSite=Lax`; only the token hash is stored in the database. The CSRF bootstrap endpoint is `GET /api/v1/auth/csrf`, and authenticated writes require `X-CSRF-Token`. The UI keeps CSRF values in memory and never places session tokens in browser storage. Every resource query is authorized on the backend.

Changing `POSTGRES_PASSWORD` after a database volume exists does not rotate the existing database password. Keep existing values unless you intentionally manage that database change. If port 5173 is occupied, stop its current process; changing the browser origin also requires updating `APP_ORIGIN` and the frontend published port consistently.

## Stop, rebuild, or remove data

Stop services while retaining the database:

```powershell
docker compose down
```

After source/dependency changes, rebuild with `docker compose up --build`. This local Compose setup builds source into images; it does not mount your checkout for live updates.

Only when you intentionally want to permanently delete **all local accounts, projects, and issues**, remove the database volume:

```powershell
docker compose down --volumes
```

## Repository layout and next phase

```text
backend/              FastAPI API, SQLAlchemy models, Alembic, pytest
frontend/             React app, typed API client, component tests
infra/                Local infrastructure guidance
docs/                 Specification, architecture, roadmap, validation
compose.yaml          PostgreSQL + API + frontend, local only
.env.example          Disposable local configuration
```

Phase 2 includes GitHub Actions checks/container builds, CodeQL, dependency/Trivy scanning, and a documented threat model. Application image bases and actions are pinned; Python transitive versions are constrained in `backend/constraints.txt`. The PostgreSQL image is built from `infra/postgres/` to patch system packages and replace the old Go-based privilege-drop helper with Alpine's `su-exec`.

Phase 3 is cloud and Infrastructure as Code design. Provisioning paid resources or deploying publicly requires separate explicit authorization. Kubernetes and an observability stack are not part of Phase 2. The local MVP is not a production deployment.
