from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from app.security import JWT_ALGORITHM, JWT_ISSUER, password_hasher


ACCOUNT = {
    "name": "Divyam Jha",
    "email": "divyam@example.com",
    "password": "LearningBugTrack2026!",
}


@pytest.fixture
def registered_user(client):
    response = client.post("/api/auth/register", json=ACCOUNT)
    assert response.status_code == 201
    return response.json()


def login(client, **changes):
    credentials = {"email": ACCOUNT["email"], "password": ACCOUNT["password"]}
    return client.post("/api/auth/login", json=credentials | changes)


def test_registration_normalizes_identity_and_stores_only_a_hash(client, database_engine):
    response = client.post("/api/auth/register", json=ACCOUNT | {
        "name": "  Divyam Jha  ", "email": "  DIVYAM@EXAMPLE.COM  ",
    })
    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Divyam Jha", "email": "divyam@example.com"}
    assert ACCOUNT["password"] not in response.text
    with Session(database_engine) as db:
        user = db.get(User, 1)
        assert user.password_hash.startswith("$argon2id$")
        assert user.password_hash != ACCOUNT["password"]
        assert password_hasher.verify(ACCOUNT["password"], user.password_hash)


def test_same_password_gets_different_salted_hashes(client, database_engine, registered_user):
    response = client.post("/api/auth/register", json=ACCOUNT | {"email": "asha@example.com"})
    assert response.status_code == 201
    with Session(database_engine) as db:
        hashes = db.scalars(select(User.password_hash)).all()
    assert len(set(hashes)) == 2


def test_duplicate_email_is_rejected_case_insensitively(client, registered_user, database_engine):
    response = client.post("/api/auth/register", json=ACCOUNT | {"email": "DIVYAM@EXAMPLE.COM"})
    assert response.status_code == 409
    with Session(database_engine) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1
    assert login(client).status_code == 200


@pytest.mark.parametrize("changes", [
    {"email": "not-an-email"},
    {"name": "   "},
    {"password": "abc123"},
    {"password": "x" * 129},
    {"is_admin": True},
])
def test_invalid_registration_is_rejected_without_echoing_passwords(client, changes):
    payload = ACCOUNT | changes
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert payload["password"] not in response.text
    assert all("input" not in detail for detail in response.json()["detail"])


def test_login_then_access_current_user(client, registered_user, auth_settings):
    response = login(client, email=" DIVYAM@EXAMPLE.COM ")
    assert response.status_code == 200
    token = response.json()
    assert token["token_type"] == "bearer"
    assert token["expires_in"] == 1800
    assert token["user"] == registered_user
    assert response.headers["cache-control"] == "no-store"
    claims = jwt.decode(token["access_token"], auth_settings.secret_key,
                        algorithms=[JWT_ALGORITHM], issuer=JWT_ISSUER)
    assert claims["sub"] == str(registered_user["id"])
    assert claims["exp"] - claims["iat"] == 1800
    assert "password" not in claims
    current = client.get("/api/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert current.status_code == 200
    assert current.json() == registered_user
    assert "password_hash" not in current.json()


def test_wrong_password_and_unknown_email_return_the_same_error(client, registered_user):
    wrong_password = login(client, password="WrongPassword2026!")
    unknown_email = login(client, email="missing@example.com")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json() == {"detail": "Invalid email or password"}
    assert wrong_password.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("headers", [
    {}, {"Authorization": "Bearer garbage"}, {"Authorization": "Basic abc123"},
])
def test_me_requires_a_valid_bearer_token(client, headers):
    response = client.get("/api/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("scenario", [
    "expired", "different_key", "different_algorithm", "different_issuer",
    "missing_expiry", "unknown_user", "invalid_subject", "future_issued",
])
def test_invalid_token_claims_are_rejected(client, registered_user, auth_settings, scenario):
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(registered_user["id"]), "iat": now,
        "exp": now + timedelta(minutes=30), "iss": JWT_ISSUER,
    }
    signing_key = auth_settings.secret_key
    algorithm = JWT_ALGORITHM
    if scenario == "expired":
        claims.update(iat=now - timedelta(hours=1), exp=now - timedelta(minutes=1))
    elif scenario == "different_key":
        signing_key = "another-test-key-which-is-at-least-32-bytes"
    elif scenario == "different_algorithm":
        algorithm = "HS512"
    elif scenario == "different_issuer":
        claims["iss"] = "another-app"
    elif scenario == "missing_expiry":
        del claims["exp"]
    elif scenario == "unknown_user":
        claims["sub"] = "99999"
    elif scenario == "invalid_subject":
        claims["sub"] = "not-an-id"
    elif scenario == "future_issued":
        claims["iat"] = now + timedelta(hours=1)
    token = jwt.encode(claims, signing_key, algorithm=algorithm)
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_password_whitespace_is_preserved(client):
    password = "  Deliberate spaces  "
    response = client.post("/api/auth/register", json=ACCOUNT | {"password": password})
    assert response.status_code == 201
    assert login(client, password=password).status_code == 200
    assert login(client, password=password.strip()).status_code == 401
