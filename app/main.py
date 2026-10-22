"""Start with: uv run uvicorn app.main:app --reload"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import engine, get_db, initialize_database
from .auth import router as auth_router
from .projects import router as projects_router
from .settings import AuthSettings


def create_app(database_engine=engine, auth_settings: AuthSettings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        initialize_database(database_engine)
        yield

    application = FastAPI(
        title="BugTrack Pro",
        description="Milestone 3: projects, membership management, and access checks.",
        version="0.3.0",
        lifespan=lifespan,
    )
    application.state.database_engine = database_engine
    application.state.auth_settings = auth_settings or AuthSettings.from_environment()
    application.include_router(auth_router)
    application.include_router(projects_router)

    @application.exception_handler(RequestValidationError)
    async def validation_error(_request, error: RequestValidationError):
        # Validation should explain the problem without echoing passwords or
        # other submitted input values back into responses and copied logs.
        details = [
            {key: item[key] for key in ("loc", "msg", "type")}
            for item in error.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": details})

    @application.get("/")
    def root() -> dict[str, str]:
        return {
            "name": "BugTrack Pro",
            "milestone": "3 - Projects and membership",
            "docs": "/docs",
        }

    @application.get("/api/health", tags=["Health"])
    def health(db: Session = Depends(get_db)) -> dict[str, str]:
        try:
            db.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            raise HTTPException(status_code=503, detail="Database unavailable") from error
        return {"status": "ok", "database": "connected"}

    return application


app = create_app()
