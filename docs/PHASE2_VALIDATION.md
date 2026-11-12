# Phase 2 validation evidence

Implemented for the [public ForgeBoard repository](https://github.com/ehoguts/ForgeBoard), with [PR #1](https://github.com/ehoguts/ForgeBoard/pull/1) as the review surface. The latest commit's hosted status is visible on the PR's Checks tab; this document does not substitute a locally passed check for a hosted run.

## Real failure and correction

Commit [924d96f](https://github.com/ehoguts/ForgeBoard/commit/924d96f0fa2175a18b80a5f14d196d59e857ed69) intentionally expected a successful exit for a synthetic HIGH Trivy report. The gate correctly returned 1. The hosted [Security run 43328672866](https://github.com/ehoguts/ForgeBoard/actions/runs/43328672866) failed its gate-test job with `AssertionError: 1 != 0`; dependent security jobs were skipped, rather than falsely reported clean. No vulnerable package was installed and application code was not weakened.

The corrected test expects exit 1 for this blocked report and exit 2 for a missing report. All 11 report-gate tests passed locally after that correction. The remediation also fixes the actual blocking image findings described in [SECURITY_FINDINGS.md](SECURITY_FINDINGS.md). Their initial failures were not silenced by changing thresholds.

Hosted execution also exposed a scanner portability issue: owner-only image archives could not be read by a container running with all capabilities dropped under a different UID. The workflow now uses the runner's UID/GID and a temporary HOME, retaining the read-only archive/root filesystem, no Docker socket, and dropped capabilities. Scanner stderr is printed even on failure, so diagnostics remain available for PR runs without publishing artifacts.

The earlier hosted [CI run](https://github.com/ehoguts/ForgeBoard/actions/runs/43328672068) passed backend/frontend quality and both container builds, and the [CodeQL run](https://github.com/ehoguts/ForgeBoard/actions/runs/43328672052) passed Python/JavaScript analysis and the explicit SARIF gates. Those links identify the demonstrated revision; final review must also inspect the current PR check suite after the corrected image definitions.

## Local executions after image remediation

| Check | Actual result |
| --- | --- |
| actionlint 1.7.12, official binary with verified checksum | All three workflows passed |
| Security gate unittest suite | 11 passed, including malformed/error reports and threshold boundaries |
| Ruff lint/format of gate code/tests | Passed |
| Backend Alpine container | Ruff/format/mypy passed; 15 SQLite integration tests passed |
| Backend + patched PostgreSQL 16.16 | 15 integration tests passed after a fresh DB initialization; all account-isolation routes included |
| Frontend Node 24.22.1/npm 12.2.2 container | Lint/format/typecheck, 14 Vitest tests, and production build passed |
| pip-audit 2.10.1 | No known vulnerabilities in the resolved constrained requirements |
| npm audit | 10 moderate entries; zero high/critical; gate passed |
| Trivy 0.76.2 backend image | 0 high/critical; 5 medium and 1 low |
| Trivy 0.76.2 frontend image | 0 high/critical; 3 medium |
| Trivy 0.76.2 database image | No vulnerabilities reported |
| Compose rebuild/restart | All three services healthy; existing named database volume preserved |
| Full browser smoke test on the rebuilt stack | Passed register/login, project/issue CRUD, URL filters/reload, dashboard, mobile width, two-account 404 boundaries, CSRF 403, and logout; no uncaught JavaScript errors |

The database was queried for aggregate row counts before and after the image restart; counts were unchanged. Disposable browser accounts created by the smoke test are local only. No real account data or secrets were included in reports.

## Reproduce the checks

The [delivery guide](DELIVERY.md) contains portable tool setup and scanner commands. Reproduce the application checks with these commands; during implementation, equivalent checks also ran in disposable `docker run` containers before replacing the live local stack:

```powershell
docker compose up --build -d
docker compose config --quiet
docker compose ps
docker compose exec -T backend ruff check .
docker compose exec -T backend ruff format --check .
docker compose exec -T backend mypy app
docker compose exec -T backend python -m pytest -q
docker compose exec -T -e TEST_DATABASE_URL=postgresql+psycopg://forgeboard:forgeboard_local_only@database:5432/forgeboard_test backend python -m pytest -q
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run format:check
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run build
python -m unittest discover -s scripts/tests -v
node scripts/browser-smoke.cjs
```

The explicit PostgreSQL URL assumes the disposable example credentials and a previously created `forgeboard_test` database. In addition, the changed PostgreSQL initialization helper was tested using an isolated `forgeboard_phase2_test` database in a disposable container. Browser tooling used the existing bundled Playwright/Brave through the documented environment overrides. Trivy consumed image archives and a real downloaded advisory database; local scans ran sequentially because its shared cache uses an exclusive lock. The workflow gives each runner its own cache, so jobs can run independently.

[security-scan-summary.json](security-scan-summary.json) records the scanned image IDs, OS metadata, severity counts, and SHA-256 digests of the raw local reports. The raw reports and image archives remain in the ignored local tooling directory; future default-branch workflow runs retain reports as short-lived artifacts.

## Boundaries and limitations

The GitHub API readback confirmed that `main` requires PRs and all 12 quality/build/security checks from the GitHub Actions application (ID 15368), with strict up-to-date checks and administrator enforcement. Force pushes and branch deletion are disabled; linear history and conversation resolution are required. Approving review count is zero to support a single-maintainer portfolio; required checks still apply to the maintainer. Private vulnerability reporting is enabled. These are actual repository settings, not merely suggested workflow configuration. The PR remains the review/merge boundary; no automatic merge was configured.

- Scanner databases change. These results describe the scanned image/dependency versions at execution time, not a permanent security clearance. No ignored CVEs or exceptions were added.
- Remaining moderate/low findings, ownership, and a review date are listed in SECURITY_FINDINGS.md. They do not meet the configured blocking thresholds.
- Starlette emits a TestClient deprecation warning recommending httpx2. Tests pass; no runtime failure was observed.
- Actions uploads are restricted to the default branch; untrusted PRs do not publish report artifacts. CodeQL uploads its analysis with the narrow security-events permission allowed by GitHub.
- Image bases are digest-pinned and Python/npm versions constrained, while system packages receive available security patches during builds. Byte-identical future images and hashed Python wheel inputs are not claimed.
- No image publication, application public deployment, cloud provisioning, Kubernetes, or observability stack was performed. The public resource created here is the source repository and its CI checks.
