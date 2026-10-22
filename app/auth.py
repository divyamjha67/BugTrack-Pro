"""Registration, login, and the dependency that identifies a signed-in user."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead
from .security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from .settings import AuthSettings, get_auth_settings


router = APIRouter(prefix="/api", tags=["Authentication"])
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Paste the access_token returned by POST /api/auth/login.",
)


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: AuthSettings = Depends(get_auth_settings),
) -> User:
    if credentials is None:
        raise unauthorized("Authentication required")
    user_id = decode_access_token(credentials.credentials, settings)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise unauthorized("Invalid or expired access token")
    return user


@router.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    if db.scalar(select(User).where(User.email == str(payload.email))) is not None:
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(
        name=payload.name,
        email=str(payload.email),
        password_hash=hash_password(payload.password.get_secret_value()),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two requests can pass the initial check simultaneously; the unique
        # database constraint is the final authority. Always roll back on error.
        db.rollback()
        if db.scalar(select(User).where(User.email == str(payload.email))) is not None:
            raise HTTPException(status_code=409, detail="An account with that email already exists") from None
        raise
    db.refresh(user)
    return UserRead.model_validate(user)


@router.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: AuthSettings = Depends(get_auth_settings),
) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email)))
    stored_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    valid_password = verify_password(payload.password.get_secret_value(), stored_hash)
    if user is None or not valid_password:
        # Keep the same response for an unknown email and a wrong password.
        raise unauthorized("Invalid email or password")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return TokenResponse(
        access_token=create_access_token(user.id, settings),
        expires_in=settings.access_token_minutes * 60,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
