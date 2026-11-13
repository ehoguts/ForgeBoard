# Production runtime dependency maintenance

ForgeBoard builds the Caddy production executable from a locked Go module in
`infra/runtime/caddy/`. The build imports Caddy's standard modules, retaining the
public ACME issuer, internal certificate authority, reverse proxy, and static file
server. The runtime contains the compiled executable and CA certificates; the Go
compiler and module cache remain in a separate build stage.

## Why the standard image was replaced

The production frontend image scan on November 13, 2026 identified two high
severity advisories in the Caddy executable. Neither finding is suppressed:

| Advisory | Original dependency | Resolution |
| --- | --- | --- |
| [CVE-2026-116587](https://github.com/go-jose/go-jose/security/advisories/GHSA-mgcc-cww5-fp2q) | `github.com/go-jose/go-jose/v3 v3.0.5` | Remove the v3 dependency through Smallstep's upstream migration to JOSE v4; the resolved module is `github.com/go-jose/go-jose/v4 v4.1.9`. |
| [CVE-2026-78661](https://pkg.go.dev/vuln/GO-2026-6860) | `golang.org/x/net v0.60.0` | Require `golang.org/x/net v0.62.0`, the fixed version recorded by the Go vulnerability database. |

The JOSE maintainers list no patched v3 release. Caddy's latest stable release,
[v2.11.9](https://github.com/caddyserver/caddy/releases/tag/v2.11.9), still declared
the affected dependencies in its [module manifest](https://github.com/caddyserver/caddy/blob/v2.11.9/go.mod).
Replacing the image tag alone therefore did not resolve both findings.

The build keeps Caddy v2.11.9 and pins Smallstep's
[merged migration to JOSE v4](https://github.com/smallstep/certificates/commit/6d5a251fbe01)
as `v0.30.3-0.20261105213751-6d5a251fbe01`, the same dependency revision adopted by
Caddy's upstream development branch. This is an unreleased upstream dependency,
not a local cryptographic patch. It should be replaced by a stable Caddy release
that includes the migration once that release has passed the image gate and local
smoke test. No additional third-party Caddy plugins are enabled.

An intermediate scan also reported
[GO-2026-5932](https://pkg.go.dev/vuln/GO-2026-5932) with severity `UNKNOWN` for
`golang.org/x/crypto v0.58.0`: its legacy OpenPGP package is unmaintained and unsafe.
The final lock uses stable `golang.org/x/crypto v0.59.0`, rather than suppressing
that advisory or treating an unknown severity as proof of safety.

## Reproduce the checks

The production Dockerfile pins the Go 1.27.4 builder and Alpine runtime by digest.
`go.mod` and `go.sum` lock the dependency graph, `go mod verify` checks downloaded
modules, and `go build -mod=readonly` rejects changes to that graph during a build.
The small entrypoint follows Caddy's
[documented custom-build pattern](https://github.com/caddyserver/caddy/blob/v2.11.9/cmd/caddy/main.go).

From the repository root:

```sh
docker build -f backend/Dockerfile.production -t forgeboard-backend:production backend
docker build -f frontend/Dockerfile.production -t forgeboard-frontend:production .
docker build -t forgeboard-database:local infra/postgres
python scripts/production_smoke.py
```

The smoke test uses disposable containers and a private Docker network. It applies
migrations to PostgreSQL over TLS with certificate and hostname verification,
checks that an incorrect hostname is rejected, and exercises the frontend/API
over HTTPS using an explicitly trusted temporary Caddy CA. It does not disable TLS
verification, install a CA in the host trust store, contact AWS, or request public
certificates. Its containers, volumes, network, credentials, and temporary keys
are removed after completion. The existing development stack is left running.

The security workflow also builds this production image and scans the resulting
filesystem with the pinned Trivy version. `scripts/security_gate.py` rejects high
and critical findings, including findings without a published fix. The build and
scan stages run locally or on free standard GitHub-hosted Linux runners for this
public repository; they publish no application or cloud infrastructure.

## Validation on November 13, 2026

- Production frontend build completed with Go module verification and the locked
  dependency graph.
- Trivy 0.76.2 reported zero vulnerabilities in the final image, including zero
  high, critical, or unknown findings. The report gate passed. This is a dated
  scanner result, not a guarantee against undisclosed vulnerabilities.
- The complete local production smoke passed with the final image, including the
  negative PostgreSQL certificate hostname test, authentication, CSRF, account
  isolation, logout, SPA routes, and request limits.
- The public-issuer Caddy configuration adapted successfully with container
  networking disabled; an ACME issuer was present. Actual public certificate
  issuance and AWS deployment were deliberately not performed.
- Temporary smoke resources were removed and the existing development stack
  remained healthy.
