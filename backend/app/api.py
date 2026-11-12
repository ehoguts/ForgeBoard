from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import schemas
from app.core.config import settings
from app.db import get_db
from app.models import AuthSession, Issue, Project, User, now
from app.services import (
    create_session,
    csrf_token,
    dummy_hash,
    owned_issue,
    owned_project,
    password_hasher,
    require_session,
    verify_password,
)

router = APIRouter(prefix="/api/v1")
Db = Annotated[Session, Depends(get_db)]


def current_session(request: Request, db: Db) -> AuthSession:
    return require_session(request, db)


CurrentSession = Annotated[AuthSession, Depends(current_session)]


def current_user(session: CurrentSession, db: Db) -> User:
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(401, "Authentication required")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=1000000)]


@router.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(data: schemas.Credentials, db: Db) -> User:
    user = User(email=data.email.lower(), password_hash=password_hasher.hash(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email is already registered") from None
    return user


@router.post("/auth/login", response_model=schemas.UserOut)
def login(data: schemas.Credentials, response: Response, request: Request, db: Db) -> User:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    valid_password = verify_password(data.password, user.password_hash if user else dummy_hash)
    if user is None or not valid_password:
        raise HTTPException(401, "Invalid email or password")
    create_session(db, user, response, request)
    return user


@router.get("/auth/me", response_model=schemas.UserOut)
def me(user: CurrentUser) -> User:
    return user


@router.get("/auth/csrf", response_model=schemas.CsrfOut)
def csrf(request: Request, session: CurrentSession) -> schemas.CsrfOut:
    return schemas.CsrfOut(csrf_token=csrf_token(request.cookies[settings.cookie_name]))


@router.post("/auth/logout", status_code=204)
def logout(response: Response, session: CurrentSession, db: Db) -> None:
    session.revoked_at = now()
    db.commit()
    response.delete_cookie(
        settings.cookie_name, path="/", secure=settings.cookie_secure, httponly=True, samesite="lax"
    )


@router.get("/projects", response_model=schemas.Page[schemas.ProjectOut])
def projects(user: CurrentUser, db: Db, offset: Offset = 0, limit: Limit = 20) -> dict[str, object]:
    scope = select(Project).where(Project.owner_id == user.id)
    return {
        "items": list(
            db.scalars(
                scope.order_by(Project.created_at.desc(), Project.id.desc())
                .offset(offset)
                .limit(limit)
            )
        ),
        "total": db.scalar(select(func.count()).select_from(scope.subquery())) or 0,
        "offset": offset,
        "limit": limit,
    }


@router.post("/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(data: schemas.ProjectCreate, user: CurrentUser, db: Db) -> Project:
    project = Project(owner_id=user.id, **data.model_dump())
    db.add(project)
    db.commit()
    return project


@router.get("/projects/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: UUID, user: CurrentUser, db: Db) -> Project:
    return owned_project(db, user.id, project_id)


@router.patch("/projects/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: UUID, data: schemas.ProjectPatch, user: CurrentUser, db: Db
) -> Project:
    project = owned_project(db, user.id, project_id)
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(project, name, value)
    db.commit()
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: UUID, user: CurrentUser, db: Db) -> None:
    db.delete(owned_project(db, user.id, project_id))
    db.commit()


@router.get("/projects/{project_id}/issues", response_model=schemas.Page[schemas.IssueOut])
def issues(
    project_id: UUID,
    user: CurrentUser,
    db: Db,
    status: schemas.Status | None = None,
    priority: schemas.Priority | None = None,
    search: Annotated[str, Query(max_length=200)] = "",
    offset: Offset = 0,
    limit: Limit = 20,
) -> dict[str, object]:
    owned_project(db, user.id, project_id)
    scope = select(Issue).where(Issue.project_id == project_id)
    if status:
        scope = scope.where(Issue.status == status)
    if priority:
        scope = scope.where(Issue.priority == priority)
    if search.strip():
        # Escape LIKE metacharacters so title search is literal and predictable.
        escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        scope = scope.where(Issue.title.ilike(f"%{escaped}%", escape="\\"))
    return {
        "items": list(
            db.scalars(
                scope.order_by(Issue.created_at.desc(), Issue.id.desc()).offset(offset).limit(limit)
            )
        ),
        "total": db.scalar(select(func.count()).select_from(scope.subquery())) or 0,
        "offset": offset,
        "limit": limit,
    }


@router.post("/projects/{project_id}/issues", response_model=schemas.IssueOut, status_code=201)
def create_issue(
    project_id: UUID,
    data: schemas.IssueCreate,
    user: CurrentUser,
    db: Db,
) -> Issue:
    owned_project(db, user.id, project_id)
    issue = Issue(project_id=project_id, **data.model_dump())
    db.add(issue)
    db.commit()
    return issue


@router.get("/issues/{issue_id}", response_model=schemas.IssueOut)
def get_issue(issue_id: UUID, user: CurrentUser, db: Db) -> Issue:
    return owned_issue(db, user.id, issue_id)


@router.patch("/issues/{issue_id}", response_model=schemas.IssueOut)
def update_issue(issue_id: UUID, data: schemas.IssuePatch, user: CurrentUser, db: Db) -> Issue:
    issue = owned_issue(db, user.id, issue_id)
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(issue, name, value)
    db.commit()
    return issue


@router.delete("/issues/{issue_id}", status_code=204)
def delete_issue(issue_id: UUID, user: CurrentUser, db: Db) -> None:
    db.delete(owned_issue(db, user.id, issue_id))
    db.commit()


@router.get("/dashboard/summary", response_model=schemas.DashboardOut)
def dashboard(user: CurrentUser, db: Db) -> schemas.DashboardOut:
    project_count = (
        db.scalar(select(func.count(Project.id)).where(Project.owner_id == user.id)) or 0
    )
    rows = db.execute(
        select(Issue.status, func.count(Issue.id))
        .join(Project)
        .where(Project.owner_id == user.id)
        .group_by(Issue.status)
    ).all()
    counts = {status: count for status, count in rows}
    return schemas.DashboardOut(
        project_count=project_count,
        total_issues=sum(counts.values()),
        todo=counts.get("todo", 0),
        in_progress=counts.get("in_progress", 0),
        done=counts.get("done", 0),
    )
