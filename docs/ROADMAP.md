# ForgeBoard roadmap

## Phase 1 — working product (CURRENT)
- Repository scaffold, API, Postgres migrations, secure session auth, user-scoped projects/issues CRUD.
- React UI, dashboard, filtering, basic tests, Docker Compose, README.
- Completion gate: working end-to-end local demo + tests and documented setup.

## Phase 2 — software delivery and DevSecOps
- GitHub Actions: backend/frontend tests, lint, type checks, container builds.
- Security scanning: CodeQL, dependency analysis, and Trivy image scanning.
- Document threat model and fix high-impact findings before continuing.
- Completion gate: green pipeline on PR; documented intentionally triggered failure and remediation.

## Phase 3 — cloud and Infrastructure as Code
- Terraform/OpenTofu design for a modest, clearly priced cloud deployment.
- Least-privilege IAM, secret management, managed database decision, HTTPS, and rollback.
- Only provision paid resources after explicit user approval.
- Completion gate: reproducible deployment and teardown with cost and security documented.

## Phase 4 — observability and reliability
- Metrics, structured logs, tracing where useful, Grafana/Prometheus/OpenTelemetry.
- Define simple SLIs/SLOs, alerts, failure injection and incident write-up.
- Completion gate: demonstrated detection and diagnosis of a controlled incident.

## Phase 5 — optional application security / product expansion
- Threat modeling, OWASP-focused regression tests, advanced auth/rate limiting.
- Optional organizations/workspaces and role-based access control if useful.
- Completion gate: documented security design and reproducible, authorized tests.

Complete phases in order unless the user explicitly changes priorities. Do not implement future phases by default.
