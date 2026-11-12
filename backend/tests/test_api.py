from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import AuthSession, Issue, User, now
from app.services import hash_token

PASSWORD = "Correct horse battery 42!"
API = "/api/v1"


def sign_in(client: TestClient, email: str = "alice@example.com") -> dict[str, str]:
    registered = client.post(f"{API}/auth/register", json={"email": email, "password": PASSWORD})
    assert registered.status_code == 201
    assert "password_hash" not in registered.json()
    response = client.post(f"{API}/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    token = client.get(f"{API}/auth/csrf").json()["csrf_token"]
    return {"X-CSRF-Token": token}


def project(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(f"{API}/projects", headers=headers, json={"name": "Launch"})
    assert response.status_code == 201
    return response.json()


def test_authentication_and_logout(client: TestClient) -> None:
    assert client.get(f"{API}/auth/me").status_code == 401
    assert client.get(f"{API}/auth/csrf").status_code == 401
    headers = sign_in(client)
    cookie = client.cookies.get(settings.cookie_name)
    assert cookie
    assert client.get(f"{API}/auth/me").json()["email"] == "alice@example.com"
    with SessionLocal() as db:
        session = db.scalar(select(AuthSession))
        user = db.scalar(select(User))
        assert session.token_hash == hash_token(cookie)
        assert session.token_hash != cookie
        assert user.password_hash.startswith("$argon2id$")
        assert PASSWORD not in user.password_hash
    assert client.post(f"{API}/auth/logout").status_code == 403
    assert client.post(f"{API}/auth/logout", headers=headers).status_code == 204
    assert client.get(f"{API}/auth/me").status_code == 401
    client.cookies.set(settings.cookie_name, cookie)
    assert client.get(f"{API}/auth/me").status_code == 401


def test_invalid_login_duplicate_and_cookie_flags(client: TestClient) -> None:
    sign_in(client)
    response = client.post(
        f"{API}/auth/register", json={"email": "ALICE@example.com", "password": PASSWORD}
    )
    assert response.status_code == 409
    for email, password in [
        ("alice@example.com", "Incorrect password!"),
        ("unknown@example.com", PASSWORD),
    ]:
        result = client.post(f"{API}/auth/login", json={"email": email, "password": password})
        assert result.status_code == 401
        assert result.json() == {"detail": "Invalid email or password"}
    response = client.post(
        f"{API}/auth/login", json={"email": "alice@example.com", "password": PASSWORD}
    )
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert response.headers["cache-control"] == "no-store"


def test_expiry_and_rotation(client: TestClient) -> None:
    headers = sign_in(client)
    old_cookie = client.cookies.get(settings.cookie_name)
    client.post(f"{API}/auth/login", json={"email": "alice@example.com", "password": PASSWORD})
    assert client.cookies.get(settings.cookie_name) != old_cookie
    assert (
        client.post(f"{API}/projects", headers=headers, json={"name": "Bad token"}).status_code
        == 403
    )
    with SessionLocal.begin() as db:
        current = db.scalar(select(AuthSession).where(AuthSession.revoked_at.is_(None)))
        current.expires_at = now() - timedelta(seconds=1)
    assert client.get(f"{API}/auth/me").status_code == 401


@pytest.mark.parametrize("endpoint", ["register", "login"])
def test_auth_origin_checks(client: TestClient, endpoint: str) -> None:
    response = client.post(
        f"{API}/auth/{endpoint}",
        headers={"Origin": "https://attacker.example"},
        json={"email": "alice@example.com", "password": PASSWORD},
    )
    assert response.status_code == 403
    response = client.post(
        f"{API}/auth/{endpoint}",
        headers={"Sec-Fetch-Site": "cross-site"},
        json={"email": "alice@example.com", "password": PASSWORD},
    )
    assert response.status_code == 403


def test_csrf_required_and_session_bound(client: TestClient) -> None:
    headers = sign_in(client)
    assert (
        client.post(
            f"{API}/projects", headers={"X-CSRF-Token": b"\xff" * 64}, json={"name": "Denied"}
        ).status_code
        == 403
    )
    for unsafe_headers in [{}, {"X-CSRF-Token": "bad"}, {**headers, "Origin": "null"}]:
        response = client.post(f"{API}/projects", headers=unsafe_headers, json={"name": "Denied"})
        assert response.status_code == 403
    other = TestClient(app)
    other_headers = sign_in(other, "bob@example.com")
    assert (
        client.post(f"{API}/projects", headers=other_headers, json={"name": "Denied"}).status_code
        == 403
    )
    assert (
        client.post(
            f"{API}/projects",
            headers={**headers, "Origin": "http://localhost:5173"},
            json={"name": "Allowed"},
        ).status_code
        == 201
    )


def test_project_issue_crud_dashboard_and_cascade(client: TestClient) -> None:
    headers = sign_in(client)
    resource = project(client, headers)
    path = f"{API}/projects/{resource['id']}"
    assert client.get(path).json()["name"] == "Launch"
    updated = client.patch(
        path, headers=headers, json={"name": "Renamed", "description": "Details"}
    )
    assert updated.json()["name"] == "Renamed"
    created = client.post(
        path + "/issues",
        headers=headers,
        json={
            "title": "Ship app",
            "description": "Use a checklist",
            "priority": "high",
            "due_date": "2026-12-01",
        },
    )
    assert created.status_code == 201
    issue_path = f"{API}/issues/{created.json()['id']}"
    assert client.get(issue_path).json()["status"] == "todo"
    updated = client.patch(
        issue_path, headers=headers, json={"status": "done", "due_date": None, "description": None}
    )
    assert updated.status_code == 200
    assert updated.json()["due_date"] is None
    summary = client.get(f"{API}/dashboard/summary").json()
    assert summary == {
        "project_count": 1,
        "total_issues": 1,
        "todo": 0,
        "in_progress": 0,
        "done": 1,
    }
    assert client.delete(issue_path, headers=headers).status_code == 204
    assert client.get(issue_path).status_code == 404
    assert (
        client.post(path + "/issues", headers=headers, json={"title": "Cascade"}).status_code == 201
    )
    assert client.delete(path, headers=headers).status_code == 204
    assert client.get(path).status_code == 404
    with SessionLocal() as db:
        assert db.scalar(select(Issue)) is None


def test_account_isolation_all_resource_routes(client: TestClient) -> None:
    alice_headers = sign_in(client)
    resource = project(client, alice_headers)
    path = f"{API}/projects/{resource['id']}"
    issue = client.post(path + "/issues", headers=alice_headers, json={"title": "Private"}).json()
    bob = TestClient(app)
    bob_headers = sign_in(bob, "bob@example.com")
    assert bob.get(f"{API}/projects").json()["total"] == 0
    assert bob.get(f"{API}/dashboard/summary").json() == {
        "project_count": 0,
        "total_issues": 0,
        "todo": 0,
        "in_progress": 0,
        "done": 0,
    }
    for target, changes in [
        (path, {"name": "Stolen"}),
        (f"{API}/issues/{issue['id']}", {"title": "Stolen"}),
    ]:
        assert bob.get(target).status_code == 404
        assert bob.patch(target, headers=bob_headers, json=changes).status_code == 404
        assert bob.delete(target, headers=bob_headers).status_code == 404
    assert bob.get(path + "/issues").status_code == 404
    assert (
        bob.post(path + "/issues", headers=bob_headers, json={"title": "Injected"}).status_code
        == 404
    )
    assert client.get(path).json()["name"] == "Launch"
    assert client.get(f"{API}/issues/{issue['id']}").json()["title"] == "Private"


def test_filters_pagination_and_literal_search(client: TestClient) -> None:
    headers = sign_in(client)
    resource = project(client, headers)
    path = f"{API}/projects/{resource['id']}/issues"
    identifiers = []
    for title, status, priority in [
        ("Alpha 100%", "todo", "high"),
        ("Beta", "in_progress", "low"),
        ("Alpha", "done", "high"),
    ]:
        response = client.post(
            path, headers=headers, json={"title": title, "status": status, "priority": priority}
        )
        identifiers.append(response.json()["id"])
    assert client.get(path, params={"search": "ALPHA", "priority": "high"}).json()["total"] == 2
    assert client.get(path, params={"status": "in_progress"}).json()["items"][0]["title"] == "Beta"
    assert client.get(path, params={"search": "%"}).json()["total"] == 1
    first = client.get(path, params={"limit": 2}).json()
    second = client.get(path, params={"limit": 2, "offset": 2}).json()
    assert [item["id"] for item in first["items"] + second["items"]] == identifiers[::-1]
    assert first["total"] == second["total"] == 3
    assert client.get(path, params={"offset": 99}).json()["items"] == []


@pytest.mark.parametrize(
    "body",
    [
        {"name": ""},
        {"name": " "},
        {"name": "a" * 121},
        {"name": "Test", "owner_id": str(uuid4())},
    ],
)
def test_project_input_validation(client: TestClient, body: dict[str, str]) -> None:
    headers = sign_in(client)
    assert client.post(f"{API}/projects", headers=headers, json=body).status_code == 422


def test_issue_and_filter_validation(client: TestClient) -> None:
    headers = sign_in(client)
    resource = project(client, headers)
    path = f"{API}/projects/{resource['id']}/issues"
    for changes in [
        {"title": " "},
        {"status": "invalid"},
        {"priority": "urgent"},
        {"due_date": "yesterday"},
        {"title": "x" * 201},
    ]:
        assert (
            client.post(path, headers=headers, json={"title": "Issue", **changes}).status_code
            == 422
        )
    for filters in [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"status": "invalid"},
        {"priority": "urgent"},
    ]:
        assert client.get(path, params=filters).status_code == 422
    assert (
        client.patch(
            f"{API}/projects/{resource['id']}", headers=headers, json={"name": None}
        ).status_code
        == 422
    )
    issue = client.post(path, headers=headers, json={"title": "Test"}).json()
    for field in ["title", "status", "priority"]:
        assert (
            client.patch(
                f"{API}/issues/{issue['id']}", headers=headers, json={field: None}
            ).status_code
            == 422
        )
    assert client.get(f"{API}/issues/{uuid4()}").status_code == 404
    assert client.get(f"{API}/projects/not-a-uuid").status_code == 422


def test_unauthenticated_mutations_and_health(client: TestClient) -> None:
    assert client.post(f"{API}/projects", json={"name": "Denied"}).status_code == 401
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200
    assert (
        client.post(
            f"{API}/auth/register", json={"email": "invalid", "password": "short"}
        ).status_code
        == 422
    )
