import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Issue, Project, ProjectMember, User
from app.security import create_access_token


@pytest.fixture
def actors(client, database_engine, auth_settings):
    accounts = {}
    with Session(database_engine) as db:
        for name in ("owner", "member", "outsider"):
            user = User(name=name.title(), email=f"{name}@example.com", password_hash="unused-test-hash")
            db.add(user)
            db.flush()
            token = create_access_token(user.id, auth_settings)
            accounts[name] = {
                "id": user.id, "email": user.email,
                "headers": {"Authorization": f"Bearer {token}"},
            }
        db.commit()
    return accounts


def create_project(client, actors, actor="owner", **changes):
    response = client.post("/api/projects", headers=actors[actor]["headers"], json={
        "name": "College Website", "description": "Track website bugs",
    } | changes)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def team_project(client, actors):
    project = create_project(client, actors)
    response = client.post(f"/api/projects/{project['id']}/members",
                           headers=actors["owner"]["headers"], json={"email": actors["member"]["email"]})
    assert response.status_code == 201
    return project


def test_create_project_uses_current_user_and_adds_owner_membership(client, actors, database_engine):
    project = create_project(client, actors, name="  College Website  ")
    assert project["name"] == "College Website"
    assert project["owner_id"] == actors["owner"]["id"]
    with Session(database_engine) as db:
        assert db.get(ProjectMember, (project["id"], actors["owner"]["id"])) is not None
    response = client.get(f"/api/projects/{project['id']}/members", headers=actors["owner"]["headers"])
    assert response.json()[0]["role"] == "owner"
    assert "password_hash" not in response.text


def test_list_projects_returns_only_memberships(client, actors, team_project):
    private = create_project(client, actors, actor="outsider", name="Private Project")
    for actor in ("owner", "member"):
        response = client.get("/api/projects", headers=actors[actor]["headers"])
        assert [project["id"] for project in response.json()] == [team_project["id"]]
    response = client.get("/api/projects", headers=actors["outsider"]["headers"])
    assert [project["id"] for project in response.json()] == [private["id"]]


def test_members_can_read_project_and_members(client, actors, team_project):
    project_path = f"/api/projects/{team_project['id']}"
    headers = actors["member"]["headers"]
    assert client.get(project_path, headers=headers).json() == team_project
    response = client.get(project_path + "/members", headers=headers)
    assert response.status_code == 200
    assert [entry["role"] for entry in response.json()] == ["owner", "member"]
    assert {entry["user"]["id"] for entry in response.json()} == {
        actors["owner"]["id"], actors["member"]["id"]
    }


@pytest.mark.parametrize(("method", "suffix", "payload"), [
    ("GET", "", None), ("GET", "/1", None), ("GET", "/1/members", None),
    ("POST", "", {"name": "New Project"}), ("PATCH", "/1", {"name": "Changed"}),
    ("POST", "/1/members", {"email": "member@example.com"}), ("DELETE", "/1/members/2", None),
])
def test_all_project_routes_require_authentication(client, method, suffix, payload):
    response = client.request(method, "/api/projects" + suffix, json=payload)
    assert response.status_code == 401


@pytest.mark.parametrize(("method", "suffix", "payload"), [
    ("GET", "", None), ("GET", "/members", None),
    ("PATCH", "", {"name": "Changed"}),
    ("POST", "/members", {"email": "member@example.com"}),
    ("DELETE", "/members/2", None),
])
def test_outsiders_cannot_access_project_routes(client, actors, team_project, method, suffix, payload):
    response = client.request(method, f"/api/projects/{team_project['id']}" + suffix,
                              headers=actors["outsider"]["headers"], json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert client.get("/api/projects", headers=actors["outsider"]["headers"]).json() == []


@pytest.mark.parametrize(("method", "suffix", "payload"), [
    ("PATCH", "", {"name": "Changed"}),
    ("POST", "/members", {"email": "outsider@example.com"}),
    ("DELETE", "/members/2", None),
])
def test_members_cannot_manage_project_or_members(client, actors, team_project, method, suffix, payload):
    response = client.request(method, f"/api/projects/{team_project['id']}" + suffix,
                              headers=actors["member"]["headers"], json=payload)
    assert response.status_code == 403
    assert client.get(f"/api/projects/{team_project['id']}", headers=actors["owner"]["headers"]).json() == team_project


def test_owner_can_update_project(client, actors, team_project):
    response = client.patch(f"/api/projects/{team_project['id']}", headers=actors["owner"]["headers"],
                            json={"name": "  Updated Project  ", "description": ""})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project"
    assert response.json()["description"] == ""
    assert response.json()["owner_id"] == actors["owner"]["id"]


@pytest.mark.parametrize("payload", [
    {"name": "   "}, {"name": "x" * 101}, {"name": "Valid", "owner_id": 2},
    {"name": "Valid", "description": "x" * 10001},
])
def test_invalid_project_creation_is_rejected(client, actors, payload):
    response = client.post("/api/projects", headers=actors["owner"]["headers"], json=payload)
    assert response.status_code == 422
    assert client.get("/api/projects", headers=actors["owner"]["headers"]).json() == []


@pytest.mark.parametrize("payload", [{}, {"name": None}, {"name": "  "}, {"description": None}, {"owner_id": 2}])
def test_invalid_updates_do_not_change_project(client, actors, team_project, payload):
    path = f"/api/projects/{team_project['id']}"
    response = client.patch(path, headers=actors["owner"]["headers"], json=payload)
    assert response.status_code == 422
    assert client.get(path, headers=actors["owner"]["headers"]).json() == team_project


def test_add_member_normalizes_email_and_rejects_duplicates(client, actors):
    project = create_project(client, actors)
    path = f"/api/projects/{project['id']}/members"
    payload = {"email": "  MEMBER@EXAMPLE.COM  "}
    response = client.post(path, headers=actors["owner"]["headers"], json=payload)
    assert response.status_code == 201
    assert response.json()["role"] == "member"
    assert response.json()["user"]["id"] == actors["member"]["id"]
    assert client.post(path, headers=actors["owner"]["headers"], json=payload).status_code == 409
    assert len(client.get(path, headers=actors["owner"]["headers"]).json()) == 2


def test_adding_a_member_requires_an_existing_account(client, actors):
    project = create_project(client, actors)
    path = f"/api/projects/{project['id']}/members"
    response = client.post(path, headers=actors["owner"]["headers"], json={"email": "missing@example.com"})
    assert response.status_code == 404
    assert client.post(path, headers=actors["owner"]["headers"], json={"email": "invalid"}).status_code == 422


def test_removal_revokes_access_immediately_for_an_existing_token(client, actors, team_project):
    path = f"/api/projects/{team_project['id']}"
    response = client.delete(path + f"/members/{actors['member']['id']}", headers=actors["owner"]["headers"])
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(path, headers=actors["member"]["headers"]).status_code == 404
    assert client.get(path + "/members", headers=actors["member"]["headers"]).status_code == 404
    assert client.get("/api/projects", headers=actors["member"]["headers"]).json() == []
    assert client.get("/api/me", headers=actors["member"]["headers"]).status_code == 200


def test_owner_cannot_be_removed_and_unknown_members_return_404(client, actors, team_project):
    path = f"/api/projects/{team_project['id']}/members"
    assert client.delete(path + f"/{actors['owner']['id']}", headers=actors["owner"]["headers"]).status_code == 409
    assert client.delete(path + f"/{actors['outsider']['id']}", headers=actors["owner"]["headers"]).status_code == 404
    assert len(client.get(path, headers=actors["owner"]["headers"]).json()) == 2


@pytest.mark.parametrize("role", ["reporter", "assignee"])
def test_member_linked_to_issues_cannot_be_removed(client, actors, team_project, database_engine, role):
    with Session(database_engine) as db:
        db.add(Issue(
            project_id=team_project["id"], title="Login button fails",
            reporter_id=actors["member" if role == "reporter" else "owner"]["id"],
            assignee_id=actors["member"]["id"] if role == "assignee" else None,
        ))
        db.commit()
    path = f"/api/projects/{team_project['id']}"
    response = client.delete(path + f"/members/{actors['member']['id']}", headers=actors["owner"]["headers"])
    assert response.status_code == 409
    assert client.get(path, headers=actors["member"]["headers"]).status_code == 200


def test_creating_a_project_rolls_back_if_owner_membership_fails(client, actors, database_engine):
    with database_engine.begin() as connection:
        connection.execute(text("""
            CREATE TRIGGER reject_membership BEFORE INSERT ON project_members
            BEGIN SELECT RAISE(ABORT, 'Simulated membership failure'); END
        """))
    with pytest.raises(IntegrityError):
        client.post("/api/projects", headers=actors["owner"]["headers"], json={"name": "Atomic Project"})
    with Session(database_engine) as db:
        assert db.scalar(select(func.count()).select_from(Project)) == 0
        assert db.scalar(select(func.count()).select_from(ProjectMember)) == 0


def test_nonexistent_project_and_inaccessible_project_look_the_same(client, actors, team_project):
    headers = actors["outsider"]["headers"]
    inaccessible = client.get(f"/api/projects/{team_project['id']}", headers=headers)
    missing = client.get("/api/projects/99999", headers=headers)
    assert inaccessible.status_code == missing.status_code == 404
    assert inaccessible.json() == missing.json()
