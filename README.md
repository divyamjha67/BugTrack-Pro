# BugTrack Pro

A FastAPI backend for project-based issue tracking, with account authentication,
project ownership, and membership-based access control.

## Current status

Version 0.3.0 supports account registration, login, project management, and team
membership. The issue data model and its database constraints are implemented;
issue-management endpoints and the frontend are planned.

## Features

- Account registration with email validation and Argon2id password hashing.
- JWT bearer authentication with a 30-minute access-token lifetime.
- Project creation with automatic owner membership in a single transaction.
- Project lists and details restricted to the current user's memberships.
- Owner-only updates and membership management.
- Database constraints that prevent duplicate memberships and cross-project
  issue assignments.
- A database-backed health check, generated API documentation, and 70 automated
  test cases covering authentication, permissions, integrity, and rollback.

## Technology stack

Python 3.12 or newer, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic, pwdlib with
Argon2, and PyJWT. Tests use pytest and HTTPX2. Dependency versions are recorded
in `uv.lock`; `requirements.txt` provides a pinned export.

## Quick start

Open a terminal in the project directory. With [uv](https://docs.astral.sh/uv/)
installed:

```powershell
uv sync --extra dev --locked
uv run uvicorn app.main:app --reload --port 8001
```

Alternatively, use a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

Open the [API explorer](http://127.0.0.1:8001/docs). The first startup creates
`bugtrack.db` in the project directory. Stop the server with Ctrl+C.

## Usage

1. Register an account through `POST /api/auth/register` with `name`, `email`,
   and a password of 12-128 characters.
2. Log in through `POST /api/auth/login` with the same email and password.
3. Use the returned token in `Authorization: Bearer <access_token>`. In the API
   explorer, paste only the token value into **Authorize**.
4. Create a project through `POST /api/projects`:

   ```json
   {
     "name": "Website Maintenance",
     "description": "Track website issues and coordinate the team"
   }
   ```

5. Use the returned project ID to view its details and manage its members.
   Members must have a registered account before an owner can add them by email.

## Access rules

| Operation | Project owner | Other member | Outsider |
| --- | --- | --- | --- |
| View project and members | Allowed | Allowed | 404 |
| Edit project details | Allowed | 403 | 404 |
| Add or remove members | Allowed, with restrictions | 403 | 404 |

Every project operation requires authentication. Any authenticated account may
create a project. Project lists contain only that user's memberships. Removing
a member revokes project access on subsequent requests, even if their login
token is still valid. The owner cannot be removed, and memberships referenced
by existing issues are protected by foreign-key constraints.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Application information |
| GET | `/api/health` | Database connectivity check |
| POST | `/api/auth/register` | Register an account |
| POST | `/api/auth/login` | Obtain an access token |
| GET | `/api/me` | Read the authenticated account |
| POST | `/api/projects` | Create a project |
| GET | `/api/projects` | List accessible projects |
| GET | `/api/projects/{project_id}` | Read a project |
| PATCH | `/api/projects/{project_id}` | Update project details |
| GET | `/api/projects/{project_id}/members` | List project members |
| POST | `/api/projects/{project_id}/members` | Add a registered member |
| DELETE | `/api/projects/{project_id}/members/{user_id}` | Remove an eligible member |

## Configuration

| Variable | Behavior |
| --- | --- |
| `DATABASE_URL` | Optional SQLAlchemy connection URL; defaults to the local SQLite file |
| `BUGTRACK_SECRET_KEY` | JWT signing key of at least 32 UTF-8 bytes |

Without a configured signing key, each application start generates a new random
development key and invalidates previously issued tokens. Use the same securely
generated key across restarts or worker processes when token continuity is
required. The application does not automatically load `.env` files.

The current setup uses SQLite. PostgreSQL operation has not been verified and
requires a suitable driver and integration testing. Table creation uses
`create_all()`; schema migrations are not configured. Public deployment also
requires HTTPS, login abuse protection, and appropriate secret management.
Refresh tokens, password reset, email verification, and per-token revocation
are not implemented yet.

## Testing

```powershell
uv run --extra dev pytest -q
```

Or:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The current suite has 70 passing cases, including parametrized tests. Tests
use temporary databases and do not modify the application's saved data. This
count is not a code-coverage percentage or performance benchmark.

## Project structure

```text
app/
  main.py          Application factory, startup, and utility routes
  database.py      Engine configuration and request-scoped sessions
  models.py        Relational models and constraints
  schemas.py       Request validation and response models
  settings.py      Authentication configuration
  security.py      Password hashing and JWT handling
  auth.py          Registration, login, and current-user dependency
  permissions.py   Project membership and ownership checks
  projects.py      Project and membership routes
tests/             Authentication, API, and database tests
docs/              Technical documentation and OpenAPI snapshot
```

## Documentation

- [Authentication](docs/milestone-2.md)
- [Projects and access control](docs/milestone-3.md)
- [Source definition index](docs/SOURCE_MAP.md)
- [OpenAPI schema](docs/openapi.json)
- [Verification summary](docs/verification.json)

## Roadmap

- Issue creation, assignment, status changes, and action-specific permissions.
- Comments, activity history, and a member-deactivation policy.
- Database migrations, pagination, search, and filtering.
- A frontend, deployment packaging, and operational monitoring.
