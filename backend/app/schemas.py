from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Name = Annotated[str, Field(min_length=1, max_length=120)]
Title = Annotated[str, Field(min_length=1, max_length=200)]
Description = Annotated[str, Field(max_length=10000)]
Status = Literal["todo", "in_progress", "done"]
Priority = Literal["low", "medium", "high"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Credentials(Input):
    email: Annotated[EmailStr, Field(max_length=254)]
    password: Annotated[str, Field(min_length=12, max_length=128)]

    @field_validator("password", mode="before")
    @classmethod
    def preserve_password(cls, value: str) -> str:
        return value

    # Password whitespace is significant; email is normalized explicitly by the service.
    model_config = ConfigDict(extra="forbid")


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(Output):
    id: UUID
    email: str
    created_at: datetime


class CsrfOut(BaseModel):
    csrf_token: str


class ProjectCreate(Input):
    name: Name
    description: Description | None = None


class ProjectPatch(Input):
    name: Name | None = None
    description: Description | None = None

    @field_validator("name")
    @classmethod
    def name_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Name cannot be null")
        return value


class ProjectOut(Output):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class IssueCreate(Input):
    title: Title
    description: Description | None = None
    status: Status = "todo"
    priority: Priority = "medium"
    due_date: date | None = None


class IssuePatch(Input):
    title: Title | None = None
    description: Description | None = None
    status: Status | None = None
    priority: Priority | None = None
    due_date: date | None = None

    @field_validator("title", "status", "priority")
    @classmethod
    def required_not_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class IssueOut(Output):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: Status
    priority: Priority
    due_date: date | None
    created_at: datetime
    updated_at: datetime


class Page[T](BaseModel):
    items: list[T]
    total: int
    offset: int
    limit: int


class DashboardOut(BaseModel):
    project_count: int
    total_issues: int
    todo: int
    in_progress: int
    done: int
