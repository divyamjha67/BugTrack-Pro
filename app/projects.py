"""Project operations use membership and ownership dependencies before accessing data."""

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from .auth import get_current_user
from .database import get_db
from .models import Project, ProjectMember, User
from .permissions import get_member_project, require_project_owner
from .schemas import (
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectRead,
    ProjectUpdate,
    UserRead,
)


router = APIRouter(prefix="/api/projects", tags=["Projects"])


def read_member(membership: ProjectMember, owner_id: int) -> ProjectMemberRead:
    return ProjectMemberRead(
        user=UserRead.model_validate(membership.user),
        role="owner" if membership.user_id == owner_id else "member",
        joined_at=membership.joined_at,
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    project = Project(name=payload.name, description=payload.description, owner_id=current_user.id)
    try:
        db.add(project)
        db.flush()  # Get the new ID, without committing either record yet.
        db.add(ProjectMember(project_id=project.id, user_id=current_user.id))
        db.commit()  # Project and owner membership succeed or fail together.
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectRead]:
    projects = db.scalars(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == current_user.id)
        .order_by(Project.created_at.desc(), Project.id.desc())
    ).all()
    return [ProjectRead.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project: Project = Depends(get_member_project)) -> ProjectRead:
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    payload: ProjectUpdate,
    project: Project = Depends(require_project_owner),
    db: Session = Depends(get_db),
) -> ProjectRead:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
def list_members(
    project: Project = Depends(get_member_project),
    db: Session = Depends(get_db),
) -> list[ProjectMemberRead]:
    memberships = db.scalars(
        select(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .where(ProjectMember.project_id == project.id)
        .order_by(ProjectMember.joined_at, ProjectMember.user_id)
    ).all()
    return [read_member(membership, project.owner_id) for membership in memberships]


@router.post("/{project_id}/members", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    payload: ProjectMemberCreate,
    project: Project = Depends(require_project_owner),
    db: Session = Depends(get_db),
) -> ProjectMemberRead:
    user = db.scalar(select(User).where(User.email == str(payload.email)))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found; ask them to register first")
    membership_key = (project.id, user.id)
    if db.get(ProjectMember, membership_key) is not None:
        raise HTTPException(status_code=409, detail="User is already a project member")
    membership = ProjectMember(project_id=project.id, user_id=user.id)
    db.add(membership)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.get(ProjectMember, membership_key) is not None:
            raise HTTPException(status_code=409, detail="User is already a project member") from None
        raise
    db.refresh(membership)
    return read_member(membership, project.owner_id)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    user_id: int = Path(gt=0),
    project: Project = Depends(require_project_owner),
    db: Session = Depends(get_db),
) -> Response:
    if user_id == project.owner_id:
        raise HTTPException(status_code=409, detail="The project owner cannot be removed")
    membership = db.get(ProjectMember, (project.id, user_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="Project member not found")
    db.delete(membership)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Issues reference the reporter's and assignee's membership records.
        # Keep those records so issue assignment and reporting remain valid.
        raise HTTPException(
            status_code=409,
            detail="Member is linked to project issues and cannot be removed",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
