# ForgeBoard roadmap

## Phase 1 — working product (COMPLETE)
- Repository scaffold, API, Postgres migrations, secure session auth, user-scoped projects/issues CRUD.
- React UI, dashboard, filtering, basic tests, Docker Compose, README.
- Completion gate: working end-to-end local demo + tests and documented setup.

## Phase 2 — software delivery and DevSecOps (COMPLETE)
- GitHub Actions: backend/frontend tests, lint, type checks, container builds.
- Security scanning: CodeQL, dependency analysis, and Trivy image scanning.
- Document threat model and fix high-impact findings before continuing.
- Completion gate: green pipeline on PR; documented intentionally triggered failure and remediation.

## Phase 3 — cloud reference and Infrastructure as Code (COMPLETE)
- Budget constraint: **R$0**. AWS is an architectural reference, not a running deployment.
- Terraform reference with private PostgreSQL, least-privilege IAM, encrypted remote-state design, and no secrets in state inputs.
- Local production packaging with HTTPS/TLS tests, security scans, diagrams, cost estimates, and future deployment/rollback/teardown instructions.
- Do not execute `terraform apply`, create cloud resources, deploy publicly, or activate paid services. No AWS account, credentials, or domain is required to evaluate this portfolio.
- Completion gate: reproducible local Docker Compose application; offline Terraform formatting/validation and mocked plan tests; free CI/security checks; documented AWS architecture, theoretical costs, screenshots, and explicit limitations.
- This replaces the original real deployment/teardown completion gate at the user's explicit zero-budget direction. A future deployment would be separate work with new authorization.

## Phase 4 — observability and reliability
- Metrics, structured logs, tracing where useful, Grafana/Prometheus/OpenTelemetry.
- Define simple SLIs/SLOs, alerts, failure injection and incident write-up.
- Completion gate: demonstrated detection and diagnosis of a controlled incident.

## Phase 5 — optional application security / product expansion
- Threat modeling, OWASP-focused regression tests, advanced auth/rate limiting.
- Optional organizations/workspaces and role-based access control if useful.
- Completion gate: documented security design and reproducible, authorized tests.

Complete phases in order unless the user explicitly changes priorities. Do not implement future phases by default.
