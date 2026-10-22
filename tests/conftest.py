import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import create_database_engine, initialize_database
from app.main import create_app
from app.settings import AuthSettings


@pytest.fixture
def database_engine(tmp_path):
    engine = create_database_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    yield engine
    engine.dispose()


@pytest.fixture
def db(database_engine):
    initialize_database(database_engine)
    with Session(database_engine) as session:
        yield session


@pytest.fixture
def auth_settings():
    return AuthSettings(secret_key="test-only-secret-key-for-tests-with-at-least-64-bytes-and-no-real-secrets")


@pytest.fixture
def client(database_engine, auth_settings):
    application = create_app(database_engine, auth_settings)
    with TestClient(application) as test_client:
        yield test_client
