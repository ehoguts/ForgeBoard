# ForgeBoard

[![CI](https://github.com/ehoguts/ForgeBoard/actions/workflows/ci.yml/badge.svg)](https://github.com/ehoguts/ForgeBoard/actions/workflows/ci.yml)
[![Security](https://github.com/ehoguts/ForgeBoard/actions/workflows/security.yml/badge.svg)](https://github.com/ehoguts/ForgeBoard/actions/workflows/security.yml)
[![Infrastructure reference](https://github.com/ehoguts/ForgeBoard/actions/workflows/infra.yml/badge.svg)](https://github.com/ehoguts/ForgeBoard/actions/workflows/infra.yml)

**A local Software Engineering, DevOps and AppSec portfolio with an R$0 cloud budget.** Start with the [portfolio walkthrough](docs/PORTFOLIO.md) for screenshots, architecture diagrams, source pointers and reproducible evidence. No cloud account, credentials or domain is needed to evaluate ForgeBoard.

Phase 3 adds an AWS reference in Terraform, production container packaging, and a local HTTPS/PostgreSQL TLS smoke test. AWS resources are **not provisioned**; no public application deployment or paid service is part of this project. Read the [infrastructure runbook](docs/CLOUD_RUNBOOK.md), [theoretical costs](docs/CLOUD_COSTS.md), and [Phase 3 validation evidence](docs/PHASE3_VALIDATION.md). GitHub Actions checks source, dependencies, containers and mocked infrastructure plans without deploying or publishing images.

ForgeBoard is a small issue tracker for personal software projects. Phase 1 includes account registration, login/logout, project and issue CRUD, issue search and filters, pagination, and an account-scoped dashboard.

The stack is FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 16, React, TypeScript, Vite, React Router, and TanStack Query. It runs locally without cloud accounts or paid services. Read [the product specification](docs/PROJECT_SPEC.md), [architecture decisions](docs/ARCHITECTURE.md), and [roadmap](docs/ROADMAP.md).

![ForgeBoard dashboard on desktop](docs/screenshots/dashboard-desktop.png)

Captured from the running Compose stack. See the [mobile dashboard](docs/screenshots/dashboard-mobile.png) and [project with issue filters](docs/screenshots/project-desktop.png).

```mermaid
flowchart LR
    Browser -->|HTTP localhost:5173| UI[React / Vite]
    UI -->|same-origin API proxy| API[FastAPI]
    API -->|SQLAlchemy / psycopg| DB[(Local PostgreSQL 16)]
```

The diagram shows the working development stack. The separate [AWS reference diagram](docs/CLOUD_RUNBOOK.md#reference-architecture) describes future infrastructure, not running cloud services.

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

The [delivery guide](docs/DELIVERY.md) documents CodeQL, dependency audits and image-scanning gates. See the [threat model](docs/THREAT_MODEL.md), [security policy](SECURITY.md) and [Phase 2 evidence](docs/PHASE2_VALIDATION.md) for the earlier delivery/security milestone.

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

## Phase 3: production packaging and infrastructure reference

The regular Compose stack above remains the application demo. A separate runtime serves the built React files through Caddy, uses a non-root FastAPI image, and requires HTTPS, Secure cookies and a TLS-verified PostgreSQL connection. With Docker running and Python 3.12+ installed, run this disposable check from the repository root:

```powershell
docker build -f backend/Dockerfile.production -t forgeboard-backend:production backend
docker build -f frontend/Dockerfile.production -t forgeboard-frontend:production .
docker build -t forgeboard-database:local infra/postgres
python scripts/production_smoke.py
```

The helper uses loopback ports 18080/18443, its own randomly named Docker project, an internal certificate authority and a disposable TLS-enabled PostgreSQL database. It explicitly runs Alembic, checks HTTPS/cookie/CSRF/account-isolation behavior and rejects a database certificate hostname mismatch. It cleans only its fixtures and does not change the development database or the operating system's certificate trust. Initial builds need internet access; the test does not contact AWS or a public certificate issuer.

The Caddy runtime is built from a pinned source version with reviewed dependency updates instead of retaining vulnerable dependencies from the upstream binary. The [Phase 3 security notes](docs/PHASE3_SECURITY.md) record the findings, source pins and verification evidence.

`compose.production.yaml` and `.env.production.example` document the runtime contract. The example contains unusable release/domain placeholders; it is not a ready-to-deploy environment. Use the smoke helper for the supported local verification path. Configuration and future migration/rollback/teardown considerations are in the [runbook](docs/CLOUD_RUNBOOK.md).

For Terraform **1.17.2**, follow the checksum-verified [tool installation and account-free commands](infra/terraform/README.md). The permitted checks are `fmt`, `init -backend=false -lockfile=readonly`, `validate`, and `test` with mocked plan runs in `bootstrap/` and `app/`. Provider downloads need internet access; these checks do not use AWS credentials, initialize remote state or exercise AWS APIs. Do not run `terraform apply` or a real provider plan. The [validation record](docs/PHASE3_VALIDATION.md) distinguishes actual local/CI results from untested future deployment assumptions.

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
| `APP_ENV` | Backend runtime policy; production requires HTTPS/Secure cookies/PostgreSQL TLS | `development` by default |
| `ENABLE_API_DOCS` | Publish OpenAPI UI/schema; production Compose disables it | `true` in development |

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
infra/postgres/       Patched local PostgreSQL image
infra/runtime/        Production reverse proxy configuration
infra/terraform/      AWS reference modules and mocked plan tests
scripts/              Browser/TLS smoke tests and security report gates
.github/workflows/    Quality, security, CodeQL and infrastructure checks
docs/                 Portfolio, diagrams, costs, runbook and validation
compose.yaml          PostgreSQL + API + frontend, local only
compose.production.yaml  Production runtime contract; local smoke overrides
.env.example          Disposable local configuration
.env.production.example  Non-deployable runtime placeholders
```

Phase 2 includes GitHub Actions checks/container builds, CodeQL, dependency/Trivy scanning, and a documented threat model. Application image bases and actions are pinned; Python transitive versions are constrained in `backend/constraints.txt`. The PostgreSQL image is built from `infra/postgres/` to patch system packages and replace the old Go-based privilege-drop helper with Alpine's `su-exec`.

Phase 3 is an account-free AWS reference with local production-container validation. The user's R$0 constraint replaces the original real-cloud-deployment gate in the [roadmap](docs/ROADMAP.md); no apply, paid infrastructure or public deployment is needed for completion. The theoretical reference costs are incompatible with the current budget and are documentation only.

The next milestone is Phase 4: observability and reliability. Metrics, tracing, an observability stack and a controlled incident exercise are not implemented in Phase 3. Any future work must preserve the zero-budget constraint unless the user changes it. Local production packaging and mock tests do not establish production readiness or cloud availability.
