import pytest
from sqlalchemy import insert, text
from sqlalchemy.exc import IntegrityError

from app.models import Issue, IssuePriority, IssueStatus, Project, ProjectMember, User


def make_project(db):
    owner = User(name="Divyam", email="divyam@example.test", password_hash="test-only-hash")
    member = User(name="Asha", email="asha@example.test", password_hash="test-only-hash")
    outsider = User(name="Sam", email="sam@example.test", password_hash="test-only-hash")
    db.add_all([owner, member, outsider])
    db.flush()
    project = Project(name="College Website", owner_id=owner.id)
    db.add(project)
    db.flush()
    db.add_all([
        ProjectMember(project_id=project.id, user_id=owner.id),
        ProjectMember(project_id=project.id, user_id=member.id),
    ])
    db.commit()
    return project, owner, member, outsider


def test_members_can_report_and_receive_an_issue(db):
    project, owner, member, _ = make_project(db)
    issue = Issue(
        project_id=project.id, reporter_id=owner.id,
        assignee_id=member.id, title="Login button fails",
    )
    db.add(issue)
    db.commit()
    assert issue.project.name == "College Website"
    assert issue.reporter.name == "Divyam"
    assert issue.assignee.name == "Asha"
    assert issue.status == IssueStatus.OPEN
    assert issue.priority == IssuePriority.MEDIUM


def test_an_issue_can_be_unassigned(db):
    project, owner, _, _ = make_project(db)
    issue = Issue(project_id=project.id, reporter_id=owner.id, title="Search is broken")
    db.add(issue)
    db.commit()
    assert issue.assignee_id is None


def test_duplicate_emails_are_rejected(db):
    make_project(db)
    db.add(User(name="Another Divyam", email="divyam@example.test", password_hash="test-only-hash"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_duplicate_memberships_are_rejected(db):
    project, owner, _, _ = make_project(db)
    with pytest.raises(IntegrityError):
        db.execute(insert(ProjectMember).values(project_id=project.id, user_id=owner.id))
    db.rollback()


@pytest.mark.parametrize("role", ["assignee", "reporter"])
def test_membership_in_another_project_does_not_grant_access(db, role):
    project, owner, member, outsider = make_project(db)
    other_project = Project(name="Other Project", owner_id=outsider.id)
    db.add(other_project)
    db.flush()
    db.add(ProjectMember(project_id=other_project.id, user_id=outsider.id))
    db.commit()
    issue = Issue(
        project_id=project.id,
        reporter_id=outsider.id if role == "reporter" else owner.id,
        assignee_id=outsider.id if role == "assignee" else member.id,
        title="Cross-project assignment",
    )
    db.add(issue)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


@pytest.mark.parametrize(
    ("field", "value"),
    [("status", "unknown"), ("priority", "urgent-ish"), ("title", "   ")],
)
def test_invalid_issue_values_are_rejected_by_the_database(db, field, value):
    project, owner, _, _ = make_project(db)
    issue = Issue(project_id=project.id, reporter_id=owner.id, title="Valid issue")
    db.add(issue)
    db.commit()
    # Field names come only from the fixed test cases, never from user input.
    with pytest.raises(IntegrityError):
        db.execute(text(f"UPDATE issues SET {field} = :value WHERE id = :id"),
                   {"value": value, "id": issue.id})
    db.rollback()
