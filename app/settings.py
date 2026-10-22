"""Authentication settings; secrets never belong in committed source code."""

import os
import secrets
from dataclasses import dataclass, field

from fastapi import Request


@dataclass(frozen=True)
class AuthSettings:
    secret_key: str = field(repr=False)
    access_token_minutes: int = 30

    def __post_init__(self):
        if len(self.secret_key.encode("utf-8")) < 32:
            raise ValueError("BUGTRACK_SECRET_KEY must contain at least 32 bytes")
        if self.access_token_minutes < 1:
            raise ValueError("Access token lifetime must be positive")

    @classmethod
    def from_environment(cls) -> "AuthSettings":
        configured_secret = os.getenv("BUGTRACK_SECRET_KEY")
        # A fresh development key lets the app run locally without setup.
        # Without an environment key, restarting the app invalidates old tokens.
        return cls(secret_key=configured_secret if configured_secret is not None else secrets.token_urlsafe(32))


def get_auth_settings(request: Request) -> AuthSettings:
    return request.app.state.auth_settings
