"""Use established libraries for password hashing and signed access tokens."""

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from .settings import AuthSettings


JWT_ALGORITHM = "HS256"
JWT_ISSUER = "bugtrack-pro"
password_hasher = PasswordHash.recommended()
# Unknown accounts still incur a password verification, like known accounts.
DUMMY_PASSWORD_HASH = password_hasher.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return password_hasher.verify(password, stored_hash)
    except UnknownHashError:
        return False


def create_access_token(user_id: int, settings: AuthSettings) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "iss": JWT_ISSUER,
    }
    return jwt.encode(claims, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, settings: AuthSettings) -> int | None:
    try:
        claims = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["sub", "iat", "exp", "iss"]},
        )
        user_id = int(claims["sub"])
        return user_id if user_id > 0 else None
    except (InvalidTokenError, ValueError, TypeError):
        return None
