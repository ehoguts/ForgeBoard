# Security policy

ForgeBoard is a local portfolio application. The supported environment is the documented Docker Compose stack or an equivalent loopback-only developer setup. It is not approved for public production exposure. Phase 2 adds delivery and security checks; it does not authorize a cloud deployment.

## Supported scope

Security review covers the FastAPI API, React client, session and CSRF handling, database models and migrations, dependency inputs, container definitions, and GitHub Actions workflows. The [threat model](docs/THREAT_MODEL.md) describes the actual trust boundaries and deployment assumptions.

The security properties that changes must preserve are:

- A session belongs to exactly one account. Session tokens are cryptographically random, stored only as hashes on the server, and delivered in HttpOnly cookies with expiry and logout revocation.
- Passwords are stored with Argon2id. Passwords, session tokens, password hashes, and real configuration secrets must not appear in logs, committed files, CI artifacts, or issue reports.
- Every project and issue operation, including lists, counts, nested creation, and dashboard summaries, is authorized on the backend for the authenticated owner. A foreign resource must not be distinguishable from an unknown resource through its response body or status.
- Authenticated state-changing requests require the session-bound CSRF token. Browser writes also enforce the configured Origin and reject cross-site Fetch Metadata. The frontend is not an authorization boundary.
- Untrusted project/issue text is rendered as text. Queries remain parameterized; client-supplied owner IDs are never authoritative.
- Compose publishes the UI/API only on loopback and does not publish PostgreSQL. `COOKIE_SECURE=false` is a deliberate localhost HTTP exception; HTTPS deployments must use Secure cookies.
- Untrusted pull-request code must not receive repository/deployment secrets or a write-capable checkout credential. Workflows must not execute pull-request content under `pull_request_target`.
- Third-party actions are pinned to immutable commit SHAs. Dependency versions and image inputs are reviewed and scanned; a successful build is not evidence that an image is secure.
- Test cleanup is limited to disposable resources. The API suite requires a dedicated database ending in `_test` when `TEST_DATABASE_URL` is set; it must never target the application's database.

## Findings and severity

Prioritize demonstrated account-isolation failures, authentication bypass, session disclosure/replay after revocation, exploitable injection, and CI privilege escalation. Include attacker capabilities, the violated boundary, the concrete impact, and the prerequisites for reaching it. Threat-model scenarios and scanner matches are investigation inputs, not automatically confirmed vulnerabilities.

Evaluate dependency and container findings against the installed version, the advisory, available fixes, and the actual runtime path. A transitive package in a build/test image still needs triage, but its presence alone does not prove a remotely exploitable application flaw. Do not suppress a finding merely to make CI green; any exception needs a narrow identifier, rationale, owner, and expiry in the repository's documented scan policy.

The MVP deliberately omits password reset/email verification, advanced rate limiting, organizations/RBAC, public TLS termination, and cloud operations. Their absence must not be presented as an unconditionally exploitable public-service flaw when public exposure has not been established. A change that makes the application public must revisit these assumptions before deployment.

## Reporting

If the repository offers GitHub private vulnerability reporting, use its **Security → Report a vulnerability** flow. Otherwise, ask the maintainer through their repository profile for a private reporting channel before sending exploit details. Do not post credentials, personal account data, session cookies, or a working exploit against another person's resources in a public issue.

Provide the affected revision, local reproduction steps, expected/observed behavior, impact, and relevant source/advisory references. Use disposable accounts and databases. Run tests only against local resources or systems for which you have explicit authorization.
