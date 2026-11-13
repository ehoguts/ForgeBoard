# Phase 2 delivery and security

ForgeBoard's [public GitHub repository](https://github.com/ehoguts/ForgeBoard) uses standard Linux GitHub-hosted runners. There is no cloud account, deployment job, image publication, or paid GitHub security entitlement enabled by these workflows. CodeQL requires a public repository or an existing explicitly enabled entitlement; the eligibility check fails with instructions instead of pretending skipped analysis passed.

## Checks

| Workflow | Required behavior |
| --- | --- |
| `ci.yml` | Backend lint/format/mypy; SQLite and PostgreSQL integration tests with Alembic; migration drift check; frontend lint/format/types/Vitest/build; development and production Docker builds |
| `codeql.yml` | Python and JavaScript/TypeScript, security-extended queries, SARIF upload, explicit security-severity gate |
| `security.yml` | Report-validator regression tests; Python and npm audits; Trivy scans of development backend/frontend, production backend/frontend, and database images |
| `infra.yml` | Checksum-verified Terraform CLI, formatting/validation and eight mocked plan runs without AWS; production-container HTTPS/PostgreSQL TLS smoke using disposable local fixtures |

PRs and pushes to `main`/`master` trigger checks. CodeQL and security scans also run weekly and support manual dispatch. Required jobs have timeouts; new commits cancel superseded runs. The demo input is a boolean, never interpolated into a shell command.

Third-party actions use verified full commit SHAs. Base application images, PostgreSQL, and Trivy use digests. Dependabot proposes weekly updates for actions, Python, npm, Docker, Compose, Terraform providers and the production Caddy Go module; it does not automatically merge them. Update `backend/constraints.txt` with Python dependency changes and rerun installation, audits, tests, and image scans. Constraints currently describe resolved Linux/Python 3.12 versions and do not provide Python wheel hashes. System package security updates are intentionally refreshed at build time. [PHASE3_SECURITY.md](PHASE3_SECURITY.md) records why the production web server uses a locked source build.

## Blocking thresholds and failures

| Input | Gate |
| --- | --- |
| CodeQL SARIF | Block `security-severity >= 7.0` (high/critical), plus quality errors; missing security-rule metadata is an error |
| Trivy | Block every HIGH or CRITICAL occurrence, including findings with no listed fix |
| npm audit | Block HIGH or CRITICAL; retain and assess lower findings |
| pip-audit | Block any known vulnerability; this report format has no dependable unified severity field |
| Tool/report availability | Nonzero scanner errors, missing reports, malformed/unsupported JSON or SARIF, and inconsistent counts fail closed |

`scripts/security_gate.py` returns 0 for an accepted report, 1 for blocking findings, and 2 for an invalid/unavailable report. The gate does not contain an ignore list. `SECURITY.md` describes review requirements for any future narrowly scoped exception; no exception is automatically granted. A successful CodeQL upload alone is insufficient: the explicit SARIF gate must pass.

The jobs have `contents: read`; only CodeQL receives `security-events: write` for analysis upload. Checkout never retains Git credentials. There is no `pull_request_target`, deployment secret, package-write token, cloud credential, or publication step. Fork PRs retain GitHub's restricted token behavior. Reports are uploaded only from the trusted default branch, with a seven-day retention; PR results remain available in job logs. The upload paths exclude database files, `.env`, image tar archives, and dependency trees.

Trivy receives an image archive mounted read-only and a separate writable report directory. It receives no Docker socket. In CI it runs as the runner's UID/GID so it can read owner-only Docker archives without relying on root capabilities. The scanner's root filesystem is read-only, capabilities are dropped, HOME and temporary/cache writes use a private tmpfs. Scanning does not start the application image.

## Local reproduction

Run the application checks from the README. Validate the security gates with Python 3.12+:

```powershell
python -m unittest discover -s scripts/tests -v
python -m venv .local/security-venv
.local/security-venv/Scripts/python.exe -m pip install -r infra/security-requirements.txt
.local/security-venv/Scripts/python.exe -m pip_audit -r backend/requirements-dev.txt --format json --output .local/pip-audit.json
python scripts/security_gate.py pip-audit .local/pip-audit.json
npm --prefix frontend ci --no-audit --no-fund
npm --prefix frontend audit --json --audit-level=high > .local/npm-audit.json
python scripts/security_gate.py npm .local/npm-audit.json
```

In Windows PowerShell 5, use `Set-Content -Encoding utf8` instead of native stdout redirection for JSON, or run the npm command inside the Linux container as shown below. Python's report loader also accepts a UTF-8 BOM. On Linux/macOS, the security virtual environment executable is `.local/security-venv/bin/python`.

The image-scan workflow contains the exact Linux build/save/scan commands and verified scanner digest. For a local Windows scan after `docker compose build`, for example:

```powershell
New-Item -ItemType Directory -Force .local/security-input/frontend, .local/security | Out-Null
docker image save --output .local/security-input/frontend/image.tar forgeboard-frontend:latest
docker run --rm --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev --cap-drop ALL --security-opt no-new-privileges --mount "type=bind,source=$((Resolve-Path .local/security-input/frontend).Path),target=/input,readonly" --mount "type=bind,source=$((Resolve-Path .local/security).Path),target=/reports" aquasec/trivy:0.76.2@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb image --cache-dir /tmp/trivy-cache --scanners vuln --format json --output /reports/trivy-frontend.json --input /input/image.tar --exit-code 0 --no-progress
python scripts/security_gate.py trivy .local/security/trivy-frontend.json
```

The first scan downloads the advisory database. A network failure is a failed/incomplete check, not a clean scan. Rebuild and rescan each changed image. To audit the running frontend without host npm:

```powershell
docker compose exec -T frontend sh -c 'npm audit --json --audit-level=high > /tmp/npm-audit.json'
docker compose cp frontend:/tmp/npm-audit.json .local/npm-audit.json
python scripts/security_gate.py npm .local/npm-audit.json
```

## Demonstrate a red gate and remediation

Locally, this harmless synthetic report intentionally exits 1:

```powershell
python scripts/security_gate.py demo --report .local/demo-high.json
```

It does not install vulnerable software or alter application code. The regression test verifies that exit code 1 is correct. To exercise the same gate after the workflow is on the default branch, manually run **Security** with `exercise_gate_failure=true`; the gate job fails and downstream scans do not run. Rerun with `false` to restore normal validation. A demonstrated hosted failure and its corrected commit are linked in [PHASE2_VALIDATION.md](PHASE2_VALIDATION.md).

## Repository settings and review

Before merging, require the CI, CodeQL, Security and Infrastructure reference checks shown on the PR, including all four container builds and all five image scans. Use GitHub **Settings → Branches/Rules → main** to require PRs and passing checks. Keep direct/force pushes and branch deletion restricted; do not give untrusted PR jobs secrets. Check names and actual enforced settings are recorded in the validation document, rather than inferred from the workflow files.

The public source repository is not a public application deployment. Phase 3 delivers reference IaC and local runtime checks under a R$0 budget. Its workflows have no AWS credentials, OIDC role, remote backend or provisioning/deployment steps. Any future real deployment is separate work; see [CLOUD_RUNBOOK.md](CLOUD_RUNBOOK.md).

Sources: [GitHub workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions), [CodeQL availability](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning), [Trivy image archives](https://trivy.dev/docs/latest/guide/target/container_image/), [pip-audit](https://github.com/pypa/pip-audit).
