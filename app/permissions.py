"""Reusable project access checks for this and future issue endpoints."""

from fastapi import Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models import Project, ProjectMember, User


def get_member_project(
    project_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = db.scalar(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(Project.id == project_id, ProjectMember.user_id == current_user.id)
    )
    if project is None:
        # Give the same answer for a nonexistent project and an inaccessible one.
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def require_project_owner(
    project: Project = Depends(get_member_project),
    current_user: User = Depends(get_current_user),
) -> Project:
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the project owner can perform this action")
    return project
