"""Users, projects, memberships, and issues with database integrity constraints."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as DatabaseEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    # SQLite stores naive datetimes; our convention is that all stored times are UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class IssuePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def enum_column(enum_class: type[Enum], name: str) -> DatabaseEnum:
    return DatabaseEnum(
        enum_class,
        name=name,
        values_callable=lambda members: [member.value for member in members],
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("length(trim(name)) >= 2", name="user_name_not_blank"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (CheckConstraint("length(trim(name)) >= 2", name="project_name_not_blank"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    owner: Mapped[User] = relationship()
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project")
    issues: Mapped[list["Issue"]] = relationship(
        back_populates="project", foreign_keys="Issue.project_id"
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    # A pair is the primary key: a user cannot join the same project twice.
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        CheckConstraint("length(trim(title)) >= 3", name="issue_title_not_blank"),
        # Both parts must match ONE membership row, so membership in another
        # project does not qualify a user to report or receive this issue.
        ForeignKeyConstraint(
            ["project_id", "reporter_id"],
            ["project_members.project_id", "project_members.user_id"],
            name="issue_reporter_is_project_member",
        ),
        ForeignKeyConstraint(
            ["project_id", "assignee_id"],
            ["project_members.project_id", "project_members.user_id"],
            name="issue_assignee_is_project_member",
        ),
        Index("ix_issues_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[IssueStatus] = mapped_column(
        enum_column(IssueStatus, "issue_status"), default=IssueStatus.OPEN
    )
    priority: Mapped[IssuePriority] = mapped_column(
        enum_column(IssuePriority, "issue_priority"), default=IssuePriority.MEDIUM
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    project: Mapped[Project] = relationship(back_populates="issues", foreign_keys=[project_id])
    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id])
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id])
