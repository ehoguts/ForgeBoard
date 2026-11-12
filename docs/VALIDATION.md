# Phase 1 validation record

Verified on November 12, 2026, against the implemented local MVP. All results below refer to real executions, not planned checks.

## Environment and startup

The initial shell had no working Python, Node, Git, or Docker on PATH. Bundled Python 3.12.14, Node 24.22.1, and Git were located. Docker Desktop and WSL were installed with the user's authorization. Docker initially could not start; after the user restarted Windows to enable virtualization, the Linux engine worked.

The final stack ran with Docker Engine 29.9.3, Docker Compose v5.7.0, PostgreSQL 16.15 (`postgres:16-alpine`), Python 3.12, and Node 24.22.0 in containers. A temporary portable PostgreSQL 16.16 instance used while preparing the environment was stopped once Compose worked.

Executed from the repository root:

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose exec -T backend alembic current
docker compose exec -T backend alembic check
```

Results: configuration valid; images built successfully; all three services healthy; frontend/API published only on `127.0.0.1`; database not published. API startup applied revision `0001_initial`. Alembic reported `0001_initial (head)` and no new upgrade operations. Backend and frontend processes both reported UID 1000.

`.env` was created only if absent during implementation. For an existing checkout, preserve its settings instead of overwriting it.

## Automated checks on the final images

| Check | Command | Actual result |
| --- | --- | --- |
| API integration / SQLite | `docker compose exec -T backend python -m pytest -q` | 15 passed |
| API integration / PostgreSQL | See dedicated database commands below | 15 passed |
| Backend lint | `docker compose exec -T backend ruff check .` | Passed |
| Backend formatting | `docker compose exec -T backend ruff format --check .` | 14 files formatted |
| Backend types | `docker compose exec -T backend mypy app` | Passed, 9 source files |
| Python dependency compatibility | `docker compose exec -T backend python -m pip check` | No broken requirements |
| Frontend tests | `docker compose exec -T frontend npm run test` | 5 files, 14 tests passed |
| Frontend lint | `docker compose exec -T frontend npm run lint` | Passed |
| Frontend types | `docker compose exec -T frontend npm run typecheck` | Passed |
| Frontend formatting | `docker compose exec -T frontend npm run format:check` | Passed |
| Frontend build | `docker compose exec -T frontend npm run build` | Passed, 78 modules; JS 318.46 kB / 98.23 kB gzip |

PostgreSQL tests ran against a separate database, using the disposable credentials from `.env.example`:

```powershell
docker compose exec -T database createdb -U forgeboard forgeboard_test
docker compose exec -T -e TEST_DATABASE_URL=postgresql+psycopg://forgeboard:forgeboard_local_only@database:5432/forgeboard_test backend python -m pytest -q
```

Create the test database only once. Tests apply the actual Alembic migration and clear tables between cases. `TEST_DATABASE_URL` must name a database ending in `_test`; the application database is not used by the suite. The default suite uses a temporary SQLite file and the same migration. A separate disposable SQLite migration cycle (`upgrade → check → downgrade → upgrade → check`) also passed.

API coverage includes password hashing, session hash storage, login failure, duplicate email normalization, cookie flags, logout revocation, session expiry/rotation, CSRF validation (including malformed non-ASCII headers), origin checks, CRUD, validation, literal title search, pagination, dashboard counts, project cascade deletion, and cross-account access to every resource route.

Frontend coverage includes authentication forms and errors, project/issue forms, filtering controls, CSRF request bootstrap, dashboard loading/empty/error states, and a mounted App performing login → dashboard → logout. It also covers returning an expired session to login and discarding private cached data.

## Real browser verification

The checked-in [browser smoke test](../scripts/browser-smoke.cjs) passed against the final Compose stack using Playwright 1.62.1 and headless Brave with fresh, separate browser contexts. See the README for portable installation/run instructions. In this environment, the bundled Playwright package and existing Brave executable were selected with `PLAYWRIGHT_MODULE` and `BROWSER_PATH` before `node scripts/browser-smoke.cjs`.

Observed and asserted:

1. Register through the UI, then log in and reach the dashboard.
2. Create a project and an issue, including description, priority, and due date.
3. Change status to done; combine title/status/priority filters; reload and preserve filter state in the URL. A nonmatching search displays the empty state.
4. Confirm dashboard counts match the stored project/issue and status.
5. Render at 1440 px and 390 px; the mobile dashboard has no horizontal overflow.
6. Register a second account in another browser context. Its lists/dashboard contain none of the first account's data. GET/PATCH/DELETE for the first account's project and issue return 404; nested issue list/create also return 404. A write without CSRF returns 403.
7. Edit project and issue fields; delete the issue and project through confirmation dialogs.
8. Log out through the UI; `/auth/me` returns 401. Zero uncaught browser JavaScript errors.

The first browser run exposed a real authentication-cache bug: login succeeded on the API but the mounted UI did not update. The fix preserves the observed account query while removing private queries; the mounted-App regression test and subsequent real browser run passed.

Screenshots were captured from the running application and visually inspected:

- [Desktop dashboard](screenshots/dashboard-desktop.png)
- [Mobile dashboard](screenshots/dashboard-mobile.png)
- [Project and combined issue filters](screenshots/project-desktop.png)

## Limitations and scope

- One upstream test warning remains: Starlette recommends using `httpx2` instead of `httpx` with TestClient. All tests pass; no runtime failure was observed.
- The initial npm installation automatically reported advisories for older pinned versions. Existing Python and JavaScript dependencies were updated to current compatible releases and all checks were rerun. Subsequent npm installs disable automatic audit queries; no security clearance or absence of vulnerabilities is claimed. Dedicated scans and CI belong to Phase 2.
- This is a local development/demo stack using Vite and explicitly non-Secure cookies for localhost HTTP. Backend cookies default to Secure outside that local override. No production deployment, cloud provisioning, CI integration, observability stack, or external scanning service was implemented.
- No cloud account, paid resource, or destructive external operation was used. No required local tool remains unavailable after installation and the Windows restart.
