from unittest.mock import Mock

from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from app.database import get_db


def test_startup_creates_the_four_tables(client, database_engine):
    assert set(inspect(database_engine).get_table_names()) == {
        "users", "projects", "project_members", "issues"
    }
    assert client.get("/").json()["docs"] == "/docs"


def test_health_checks_a_real_database_connection(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_health_returns_503_when_the_database_is_unavailable(client):
    broken_session = Mock()
    broken_session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("offline"))
    client.app.dependency_overrides[get_db] = lambda: broken_session
    response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
