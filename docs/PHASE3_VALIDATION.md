# Phase 3 validation evidence

Validated on November 13, 2026, under the user's **R$0** scope. AWS is a reference architecture. No AWS account, credentials, real provider plan, remote backend initialization, apply, destroy, public application deployment or paid subscription was used. Downloads of public tools, packages and price lists are distinct from cloud provisioning.

## Local results

| Check | Observed result |
| --- | --- |
| `docker compose up --build -d` | Completed; PostgreSQL, API and frontend healthy; existing development data retained |
| Backend Ruff / format / mypy | Passed; 15 Python files formatted, 9 application modules type-checked |
| Backend SQLite integration suite | 17 passed, including production configuration rejection tests |
| Backend PostgreSQL integration suite | 17 passed against the dedicated `forgeboard_test` database |
| `alembic check` | No new upgrade operations detected |
| Frontend ESLint / Prettier / TypeScript / build | Passed in the development container |
| Vitest | 14 tests passed across 5 files |
| Security-report gate regressions | 21 tests passed; driver/extension SARIF references, missing/malformed reports and blocking findings fail closed |
| Smoke credential regressions | 2 tests passed; fixture secrets stay out of generated files/argv and are redacted from diagnostics before truncation |
| Validation helper Ruff / format | Passed for the report gate, production smoke helper and gate tests |
| actionlint 1.7.12 | All four GitHub Actions workflows passed |
| Terraform 1.17.2 `fmt` / provider init / validate | Both root modules passed; `init -backend=false -lockfile=readonly` used |
| Terraform mocked plan tests | Bootstrap: 2 passed; application: 6 passed; zero failures; every run uses `command = plan` and a mocked AWS provider |
| Browser smoke against localhost:5173 | Registration/login, project/issue CRUD, filters/reload, dashboard, mobile layout, two-account isolation, CSRF and logout passed; zero uncaught browser errors |
| Production image builds | Backend and static frontend built locally; no images published |
| Local production HTTPS / PostgreSQL TLS smoke | Passed using trusted local test CAs and isolated disposable Docker resources |

Backend tests currently emit one Starlette TestClient deprecation warning about its httpx integration. The tests pass; this warning is retained rather than suppressed.

## Image security results

Trivy 0.76.2 used a real downloaded advisory database and the built image archives. Scans ran sequentially against a shared local scanner cache. The unchanged report gate passed both final production images:

| Production image | HIGH / CRITICAL | Other findings |
| --- | --- | --- |
| Backend | 0 / 0 | 5 MEDIUM, 1 LOW |
| Frontend | 0 / 0 | None reported |

The original upstream Caddy executable produced two HIGH findings and failed the gate. A locked source build removed its JOSE v3 dependency and updated x/net; a stable x/crypto update then removed an intermediate UNKNOWN OpenPGP advisory. [PHASE3_SECURITY.md](PHASE3_SECURITY.md) records the upstream sources and maintenance trade-off. No CVE ignore list, lower threshold or disabled scanner was used.

[phase3-security-scan-summary.json](phase3-security-scan-summary.json) records the exact scanned image IDs, timestamps, severities, report SHA-256 hashes and source-file hashes. Raw reports, image archives, temporary certificates and caches remain ignored under `.local/`. Scanner findings can change with future advisory data; these are dated results, not a permanent clearance. Remaining backend medium/low findings remain visible in reports and the [Phase 2 findings record](SECURITY_FINDINGS.md).

## Production TLS and authorization evidence

`scripts/production_smoke.py` uses the delivered production Compose file with generated local-only overrides. It creates a random project/network and disposable database, applies real Alembic migrations, and cleans its own fixtures. It neither uses the development database nor modifies the host certificate trust store. Public ACME issuance and AWS APIs are not invoked.

The helper verifies:

- PostgreSQL `sslmode=verify-full`: migration using the deliberately incorrect `wrong-database` hostname is rejected with a certificate mismatch; migration through the matching `database` name succeeds.
- HTTPS requests trust the test Caddy CA explicitly, with certificate verification enabled.
- Static SPA routes load; security headers are present; public OpenAPI/docs and database readiness paths return 404; liveness remains available.
- A body larger than the proxy's 64 KB limit is rejected with 413.
- Login sets a Secure, HttpOnly, SameSite session cookie; missing CSRF is rejected with 403.
- A second account cannot read or modify the first account's project ID (404); logout revokes authentication (401).

The ordinary browser smoke separately exercises the complete UI and all GET/PATCH/DELETE/nested ownership boundaries. The screenshots in this repository are actual local captures, not a cloud deployment.

## Reproduce

Install Docker/Compose, Python 3.12+ and Terraform 1.17.2; the [Terraform guide](../infra/terraform/README.md) documents checksum-verified tool setup. First downloads need Internet, but no AWS account or credentials are needed. From the repository root:

```powershell
# First clone only; preserve an existing .env.
Copy-Item .env.example .env
docker compose up --build -d
docker compose exec -T backend python -m pytest -q
docker compose exec -T backend alembic check
docker compose exec -T frontend npm test
python -m unittest discover -s scripts/tests -v

terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/terraform/bootstrap validate
terraform -chdir=infra/terraform/bootstrap test
terraform -chdir=infra/terraform/app init -backend=false -input=false -lockfile=readonly
terraform -chdir=infra/terraform/app validate
terraform -chdir=infra/terraform/app test

docker build -f backend/Dockerfile.production -t forgeboard-backend:production backend
docker build -f frontend/Dockerfile.production -t forgeboard-frontend:production .
docker build -t forgeboard-database:local infra/postgres
python scripts/production_smoke.py
```

On Linux/macOS use `cp` for the example environment file. The README contains all lint/type/build, PostgreSQL test-database creation and optional browser-tool installation commands. `CLOUD_RUNBOOK.md` explains the production runtime contract; the example production environment deliberately cannot deploy as-is. Local execution used Docker Desktop with Linux containers on Windows, the backend virtual environment, and bundled Playwright/Brave for the optional browser check. No personal browser profile was opened.

## Hosted execution and failure evidence

[PR #5](https://github.com/ehoguts/ForgeBoard/pull/5) is the review surface. On its first revision, `0db486a`, hosted [CI](https://github.com/ehoguts/ForgeBoard/actions/runs/43378611186), [Security](https://github.com/ehoguts/ForgeBoard/actions/runs/43378611121) and [Infrastructure reference](https://github.com/ehoguts/ForgeBoard/actions/runs/43378611262) all passed. This includes all five image scans, both database test suites, eight mocked Terraform plans and the production HTTPS smoke on Ubuntu; Linux execution is verified in addition to the Windows host checks.

The first [CodeQL run](https://github.com/ehoguts/ForgeBoard/actions/runs/43378611341) failed closed in the Python SARIF gate: `SARIF result references an unknown rule`. The real report stored its rule descriptors under `tool.extensions`, referenced by `result.rule.toolComponent`, while the original validator read only driver rules. The report also identified `py/clear-text-storage-sensitive-data` (security severity 7.5) in the smoke helper's generated temporary database connection file. This is actual failure evidence, not an intentionally weakened scanner or a skipped analysis.

The corrected parser resolves descriptors within the selected driver/extension and validates ID, index and GUID aliases against the [SARIF 2.1.0 specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html). It rejects contradictory, missing, ambiguous and out-of-range references. Running it against the original hosted report returns exit 1 and explicitly blocks the severity-7.5 finding; compatibility support does not lower the threshold.

The helper now supplies disposable database credentials through child-process environments, keeps its placeholder `backend.env` empty, and redacts sensitive diagnostics before truncation. The negative-hostname subprocess has its own environment, then correct migrations use the original value. New regressions reproduced the previous file/argv exposure and pass after the fix; all 23 validation-tool tests passed. A fresh independent review found no concrete bypass/regression. The complete local production smoke passed again with the corrected helper, and inspection confirmed the generated fixture configuration contained no password/connection URL. Docker daemon operators remain trusted and can inspect container environment metadata. The production runtime's separately documented protected host environment-file contract is unchanged.

The public repository's `main` protection was read back with 18 required GitHub Actions checks, strict up-to-date checks, administrator enforcement, linear history and conversation resolution. PRs are required with zero approving reviews for a single-maintainer portfolio; force pushes and branch deletion are disabled. Private vulnerability reporting is enabled. These settings were restored after the user explicitly requested public visibility again; private visibility had removed the earlier protection.

## Deliberate limits

Mock plans assert intended configuration, not real AWS behavior. AMI/engine regional availability, quotas, AWS IAM execution, Session Manager, RDS secret bootstrap, public DNS/ACME, remote state locking, cloud deployment/rollback/restore and theoretical prices are not validated by these tests. There is no deployed cloud environment or measured cloud recovery time. See the [reference runbook](CLOUD_RUNBOOK.md), [cost estimate](CLOUD_COSTS.md) and [roadmap](ROADMAP.md).

The original Phase 3 real-deployment gate was explicitly replaced at the user's direction with local validation and reference IaC. Phase 4 observability is separate work and has not been implemented.
