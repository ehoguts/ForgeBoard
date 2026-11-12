import hashlib
import hmac
import secrets
from datetime import UTC, timedelta
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type
from fastapi import HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AuthSession, Issue, Project, User, now

password_hasher = PasswordHasher(type=Type.ID)
dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def csrf_token(token: str) -> str:
    return hash_token("csrf:" + token)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_session(db: Session, user: User, response: Response, request: Request) -> None:
    # Rotate any previous browser session to avoid accumulating a live session on re-login.
    old_token = request.cookies.get(settings.cookie_name)
    if old_token:
        old_session = db.scalar(
            select(AuthSession).where(AuthSession.token_hash == hash_token(old_token))
        )
        if old_session:
            old_session.revoked_at = now()
    token = secrets.token_urlsafe(32)
    ttl = timedelta(hours=settings.session_ttl_hours)
    db.add(AuthSession(user_id=user.id, token_hash=hash_token(token), expires_at=now() + ttl))
    db.commit()
    response.set_cookie(
        settings.cookie_name,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=int(ttl.total_seconds()),
        path="/",
    )


def require_session(request: Request, db: Session) -> AuthSession:
    token = request.cookies.get(settings.cookie_name, "")
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(token)))
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at.replace(tzinfo=UTC) <= now()
    ):
        raise HTTPException(401, "Authentication required")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        supplied = request.headers.get("x-csrf-token", "")
        if (
            len(supplied) != 64
            or not supplied.isascii()
            or not hmac.compare_digest(supplied, csrf_token(token))
        ):
            raise HTTPException(403, "Invalid CSRF token")
    return session


def owned_project(db: Session, user_id: UUID, project_id: UUID) -> Project:
    project = db.scalar(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    if project is None:
        raise HTTPException(404, "Project not found")
    return project


def owned_issue(db: Session, user_id: UUID, issue_id: UUID) -> Issue:
    issue = db.scalar(
        select(Issue).join(Project).where(Issue.id == issue_id, Project.owner_id == user_id)
    )
    if issue is None:
        raise HTTPException(404, "Issue not found")
    return issue
