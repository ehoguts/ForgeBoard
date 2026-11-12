# Infrastructure-specific instructions

Scope: all files under `infra/`. Follow root `AGENTS.md` too.

## Milestone 1: local development only
- Use Docker Compose for local PostgreSQL, backend, and frontend. Root-level `compose.yaml` can hold service definitions.
- Bind database ports to localhost only if host access is necessary; never expose PostgreSQL to the public network.
- Include health checks and startup ordering where appropriate; do not treat `depends_on` alone as proof of database readiness.
- Use reproducible container builds, multi-stage builds where useful, non-root runtime users where practical, and `.dockerignore` files.
- No hardcoded production secrets or real cloud credentials. Put safe example values in `.env.example` and document local configuration.
- Provide a reliable local boot path and clear cleanup instructions that distinguish non-destructive stops from deleting volumes.

## Later milestones, only when explicitly requested
- Infrastructure as code: Terraform or OpenTofu with remote state, least-privilege IAM, constrained ingress, and explicit cost estimates.
- CI/CD: minimal GitHub Actions permissions, pinned third-party actions, protected secrets, reproducible builds.
- Observability: Prometheus/Grafana/OpenTelemetry with carefully chosen metrics and no sensitive-data leakage.
- Security scans: dependency, source, and container scanning, with actionable findings and documented thresholds.
- Never execute `terraform apply` or incur cloud costs without prior explicit user authorization.
