"""Exercise production images over local TLS only, without AWS or public certificate issuance."""

import argparse
import http.cookiejar
import json
import secrets
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

CERT_TOOL_IMAGE = (
    "alpine:3.24@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf"
)
REPOSITORY = Path(__file__).resolve().parents[1]


def command(arguments: list[str], *, required: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, capture_output=True, text=True, check=False)
    if required and result.returncode:
        # Never echo argv: environment assignments can include the disposable DB password.
        raise RuntimeError(
            f"Local test command failed ({result.returncode}): {result.stderr[-4000:]}"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", default="docker")
    parser.add_argument("--backend-image", default="forgeboard-backend:production")
    parser.add_argument("--frontend-image", default="forgeboard-frontend:production")
    parser.add_argument("--database-image", default="forgeboard-database:local")
    parser.add_argument("--https-port", type=int, default=18443)
    parser.add_argument("--http-port", type=int, default=18080)
    args = parser.parse_args()
    project = "forgeboard-production-smoke-" + uuid.uuid4().hex[:8]
    origin = f"https://localhost:{args.https_port}"
    local = REPOSITORY / ".local"
    local.mkdir(exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix="production-smoke-", dir=local)
    work = Path(temporary.name).resolve()
    assert work.is_relative_to(local.resolve())
    docker = [args.docker]
    compose = [
        *docker,
        "compose",
        "-p",
        project,
        "--env-file",
        str(work / "release.env"),
        "-f",
        str(REPOSITORY / "compose.production.yaml"),
        "-f",
        str(work / "override.yaml"),
    ]
    password = secrets.token_urlsafe(24)
    database_url = (
        f"postgresql+psycopg://forgeboard_test:{password}@database:5432/forgeboard_runtime_test"
        "?sslmode=verify-full&sslrootcert=/run/certs/rds-global-bundle.pem"
    )
    try:
        command([*docker, "network", "create", project])
        command(
            [
                *docker,
                "run",
                "--rm",
                "--mount",
                f"type=bind,source={work},target=/out",
                CERT_TOOL_IMAGE,
                "sh",
                "-c",
                "apk add --no-cache openssl >/dev/null && "
                "openssl req -x509 -newkey rsa:2048 -nodes -keyout /out/server.key "
                "-out /out/server.crt -days 2 -subj /CN=database "
                "-addext subjectAltName=DNS:database 2>/dev/null",
            ]
        )
        command(
            [
                *docker,
                "run",
                "--detach",
                "--rm",
                "--name",
                project + "-database",
                "--network",
                project,
                "--network-alias",
                "database",
                "--network-alias",
                "wrong-database",
                "--env",
                "POSTGRES_USER=forgeboard_test",
                "--env",
                "POSTGRES_PASSWORD=" + password,
                "--env",
                "POSTGRES_DB=forgeboard_runtime_test",
                "--mount",
                f"type=bind,source={work},target=/test-certs,readonly",
                "--entrypoint",
                "/bin/sh",
                args.database_image,
                "-c",
                "mkdir -p /tls && cp /test-certs/server.crt /tls/server.crt && "
                "cp /test-certs/server.key /tls/server.key && chown -R postgres:postgres /tls && "
                "chmod 600 /tls/server.key && exec docker-entrypoint.sh postgres -c ssl=on "
                "-c ssl_cert_file=/tls/server.crt -c ssl_key_file=/tls/server.key",
            ]
        )
        (work / "backend.env").write_text("DATABASE_URL=" + database_url + "\n", encoding="utf-8")
        (work / "release.env").write_text(
            "\n".join(
                [
                    "BACKEND_IMAGE=" + args.backend_image,
                    "FRONTEND_IMAGE=" + args.frontend_image,
                    "APP_DOMAIN=localhost",
                    "ACME_EMAIL=local@example.com",
                    "RUNTIME_ENV_FILE=" + str(work / "backend.env"),
                    "RDS_CA_BUNDLE=" + str(work / "server.crt"),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (work / "override.yaml").write_text(
            f"""services:
  backend:
    environment:
      APP_ORIGIN: {origin}
  migrate:
    environment:
      APP_ORIGIN: {origin}
  frontend:
    environment:
      APP_ORIGIN: {origin}
      TLS_MODE: internal
    ports: !override
      - "127.0.0.1:{args.http_port}:8080"
      - "127.0.0.1:{args.https_port}:8443"
networks:
  default:
    external: true
    name: {project}
""",
            encoding="utf-8",
        )
        command([*compose, "config", "--quiet"])
        for _ in range(30):
            ready = command(
                [*docker, "exec", project + "-database", "pg_isready", "-U", "forgeboard_test"],
                required=False,
            )
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Disposable PostgreSQL did not become ready")
        wrong_host = command(
            [
                *compose,
                "--profile",
                "ops",
                "run",
                "--rm",
                "--env",
                "DATABASE_URL=" + database_url.replace("@database:", "@wrong-database:"),
                "migrate",
            ],
            required=False,
        )
        assert wrong_host.returncode != 0 and "does not match host name" in wrong_host.stderr, (
            "PostgreSQL TLS did not reject a hostname missing from the trusted certificate"
        )
        command([*compose, "--profile", "ops", "run", "--rm", "migrate"])
        command([*compose, "up", "-d", "backend", "frontend"])
        for _ in range(45):
            health = command(
                [
                    *docker,
                    "inspect",
                    "--format",
                    "{{.State.Health.Status}}",
                    project + "-frontend-1",
                ],
                required=False,
            )
            if health.returncode == 0 and health.stdout.strip() == "healthy":
                break
            time.sleep(2)
        else:
            raise RuntimeError("Production frontend did not become healthy")
        command(
            [
                *compose,
                "cp",
                "frontend:/data/caddy/pki/authorities/local/root.crt",
                str(work / "browser-ca.crt"),
            ]
        )
        context = ssl.create_default_context(cafile=str(work / "browser-ca.crt"))

        def client() -> urllib.request.OpenerDirector:
            return urllib.request.build_opener(
                urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(context=context),
                urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
            )

        def request(
            opener: urllib.request.OpenerDirector,
            path: str,
            method: str = "GET",
            body: dict[str, str] | None = None,
            token: str | None = None,
        ) -> tuple[int, object, object]:
            headers = {"Origin": origin}
            if body is not None:
                headers["Content-Type"] = "application/json"
            if token:
                headers["X-CSRF-Token"] = token
            request_body = None if body is None else json.dumps(body).encode()
            req = urllib.request.Request(
                origin + path, data=request_body, headers=headers, method=method
            )
            try:
                response = opener.open(req, timeout=15)
            except urllib.error.HTTPError as error:
                response = error
            content = response.read()
            parsed = (
                json.loads(content)
                if content and "application/json" in response.headers.get("Content-Type", "")
                else content
            )
            return response.status, parsed, response.headers

        first = client()
        status, page, headers = request(first, "/projects")
        assert status == 200 and b"/assets/" in page
        assert headers.get("Content-Security-Policy") and headers.get("Strict-Transport-Security")
        for path in ("/docs", "/redoc", "/openapi.json", "/health/ready"):
            assert request(first, path)[0] == 404, path
        assert request(first, "/health/live")[0] == 200

        def sign_in(opener: urllib.request.OpenerDirector, email: str) -> str:
            credentials = {"email": email, "password": secrets.token_urlsafe(24)}
            assert request(opener, "/api/v1/auth/register", "POST", credentials)[0] == 201
            status, _, response_headers = request(opener, "/api/v1/auth/login", "POST", credentials)
            assert status == 200
            cookie = response_headers.get("Set-Cookie", "").lower()
            assert "secure" in cookie and "httponly" in cookie and "samesite=lax" in cookie
            status, payload, _ = request(opener, "/api/v1/auth/csrf")
            assert status == 200
            return payload["csrf_token"]

        token = sign_in(first, "first-" + uuid.uuid4().hex + "@example.com")
        assert request(first, "/api/v1/projects", "POST", {"name": "Denied"})[0] == 403
        status, resource, _ = request(
            first, "/api/v1/projects", "POST", {"name": "Production smoke"}, token
        )
        assert status == 201
        path = "/api/v1/projects/" + resource["id"]
        assert (
            request(
                first,
                "/api/v1/projects",
                "POST",
                {"name": "too large", "description": "x" * 70000},
                token,
            )[0]
            == 413
        )
        second = client()
        second_token = sign_in(second, "second-" + uuid.uuid4().hex + "@example.com")
        assert request(second, path)[0] == 404
        assert request(second, path, "PATCH", {"name": "Denied"}, second_token)[0] == 404
        assert request(second, path, "DELETE", token=second_token)[0] == 404
        assert request(first, path)[0] == 200
        assert request(first, "/api/v1/auth/logout", "POST", token=token)[0] == 204
        assert request(first, "/api/v1/auth/me")[0] == 401
        print(
            "PASS: production static SPA, trusted local HTTPS, verified PostgreSQL TLS, "
            "Secure cookies, CSRF, isolation, logout, hidden schema, and request limits"
        )
    finally:
        command(
            [*compose, "--profile", "ops", "down", "--volumes", "--remove-orphans"], required=False
        )
        command([*docker, "stop", project + "-database"], required=False)
        command([*docker, "network", "rm", project], required=False)
        assert work.is_relative_to(local.resolve())
        temporary.cleanup()


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, RuntimeError, OSError) as error:
        raise SystemExit(f"FAIL: {error}") from None
