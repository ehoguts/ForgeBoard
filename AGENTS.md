# ForgeBoard — repository-wide Codex instructions

## Mission
Build ForgeBoard, a small but credible issue-tracking web application that doubles as a public Software Engineering, DevOps, and AppSec portfolio project. Prefer a working, tested vertical slice over an elaborate architecture.

## Source of truth
- Read `docs/PROJECT_SPEC.md` before implementing features.
- Follow the milestones and boundaries in `docs/ROADMAP.md`.
- This file applies throughout the repository. Additional `AGENTS.md` files inside `backend/`, `frontend/`, and `infra/` add scoped instructions.
- If a task conflicts with the spec, explain the trade-off in the final summary; do not silently redefine the product.

## Working approach
1. Inspect the existing repository and relevant instructions before changing code.
2. Make a short implementation plan for multi-file work; then implement, don't stop at the plan.
3. Work in small, end-to-end increments that are runnable and testable.
4. Add or update automated tests for behavior changes, especially authorization and security boundaries.
5. Run relevant formatting, linting, type checking, and tests; report precisely what ran and what could not run.
6. Update README and architecture notes when commands, environment variables, or structure change.
7. Do not claim a feature or test passed unless it was actually verified.

## Repository conventions
- Backend: Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pytest.
- Frontend: React, TypeScript, Vite, React Router, TanStack Query, Vitest.
- Local infrastructure: Docker Compose; cloud infrastructure only in later milestones.
- Use descriptive English identifiers, English user-facing UI text, and English technical documentation.
- Keep the API under `/api/v1`; define stable request/response schemas.
- Prefer simplicity. No premature microservices, Kubernetes, event buses, or abstractions for imagined requirements.
- Use environment variables for configuration; include `.env.example`, never real credentials.
- Treat all client input and external content as untrusted; never log secrets or passwords.
- Avoid unrelated refactors and gratuitous dependencies.

## Safety and boundaries
- Work only with local, test, or explicitly authorized resources.
- Never run paid cloud provisioning, deploy publicly, create billable infrastructure, or execute destructive external operations without explicit approval.
- Never commit secrets, tokens, production data, or dependency/cache artifacts.
- Do not implement roadmap milestones beyond the current requested milestone without approval.

## Required delivery checklist
- Fresh clone can be started using the commands documented in README.
- Core user flows work end-to-end.
- Automated tests cover critical behavior and account-level data isolation.
- Local development does not require cloud accounts or paid services.
- Final response contains: what changed, commands executed, validation results, limitations, and next milestone.
