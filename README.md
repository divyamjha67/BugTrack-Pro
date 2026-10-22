# BugTrack Pro: rebuild

We are building a team issue tracker in small milestones so you can understand
and explain every feature in an interview.

## Interview documentation

Read the [complete interview handbook](docs/INTERVIEW_GUIDE.md) for the architecture,
data dictionary, API contracts, security model, tests, troubleshooting, tradeoffs,
demo sequence, and 50 interview questions. The printable version is
[available as a PDF](docs/BugTrack_Pro_Interview_Handbook.pdf). The
[source index](docs/SOURCE_MAP.md) identifies code definitions by line number,
and [OpenAPI snapshot](docs/openapi.json) provides machine-readable API contracts.

## Completed: milestones 1, 2, and 3

The app creates four SQLite tables and supports registration, login, and viewing
your own account. Passwords are stored using Argon2id hashes. A successful login
returns a signed access token that expires after 30 minutes.

Users can create projects, view the projects they belong to, and inspect their
members. Only a project's owner can edit its details or add and remove members.
Database constraints protect membership and assignment integrity. Issue endpoints
and a frontend are later milestones.

## Run on Windows

Open PowerShell in this folder. With `uv` installed:

```powershell
uv sync --extra dev --locked
uv run uvicorn app.main:app --reload --port 8001
```

Open http://127.0.0.1:8001/docs and try `GET /api/health`. The response should be:

```json
{"status": "ok", "database": "connected"}
```

The first startup creates `bugtrack.db` in this folder. Stop the server with
Ctrl+C. The database is local and is excluded from Git.

If you prefer standard Python tools, use Python 3.12 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

## Run the checks

```powershell
uv run --extra dev pytest -q
```

Or, after installing requirements.txt:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use their own temporary databases. They do not change your app's database.

## Try registration and login

In http://127.0.0.1:8001/docs:

1. Expand `POST /api/auth/register`, click **Try it out**, and submit:

   ```json
   {
     "name": "Divyam Jha",
     "email": "divyam@example.com",
     "password": "LearningBugTrack2026!"
   }
   ```

2. Expect `201` and your user ID, name, and email. Registering the same email
   again returns `409`. This example password is only for local practice.
3. Try `POST /api/auth/login` with:

   ```json
   {
     "email": "divyam@example.com",
     "password": "LearningBugTrack2026!"
   }
   ```

4. Copy only the returned `access_token` value, without quotes. Click
   **Authorize** near the top of the page and paste it. The API explorer adds
   the `Bearer` prefix for you.
5. Execute `GET /api/me`. It should return your account details. Click
   **Authorize**, then **Logout**, and try `/api/me` again: it should return
   `401` because you are no longer sending a token.

For a request outside the explorer, the header format is:

```text
Authorization: Bearer <access_token>
```

Registration accepts names of 2-100 characters after trimming, a valid email
address, and passwords of 12-128 characters. Email addresses are normalized to
lowercase; password whitespace is preserved. Responses never include the
password or its hash, and validation errors do not echo submitted input values.

### Development token signing key

By default, each app start generates a new random signing key. This is convenient
for local practice, but restarting the server invalidates existing tokens: log
in again. To keep tokens valid across restarts, set `BUGTRACK_SECRET_KEY` to the
same securely generated value before starting the app. It must contain at least
32 bytes. For example, generate a new key for this PowerShell session with:

```powershell
$env:BUGTRACK_SECRET_KEY = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
uv run uvicorn app.main:app --reload --port 8001
```

Do not put a real signing key in source code or commit it to Git. Multiple server
processes must share the same configured key. No `.env` file is loaded
automatically. Email verification, password reset, token revocation, and login
throttling are not implemented yet. Public deployment will require HTTPS and
login abuse protection. Logging out in the explorer only removes its saved
token; a copied token remains valid until it expires or the signing key changes.

## Read the code in this order

1. `app/main.py`: FastAPI receives an HTTP request and chooses an endpoint.
2. `app/database.py`: the engine connects to SQLite; a session handles one unit of work.
3. `app/models.py`: Python classes describe tables, columns, and relationships.
4. `app/schemas.py`: validates request fields and chooses which response fields to expose.
5. `app/security.py`: hashes passwords and creates/verifies access tokens.
6. `app/auth.py`: puts validation, database access, and authentication together.
7. `app/permissions.py`: checks project membership and ownership.
8. `app/projects.py`: creates projects and manages members using those checks.
9. `tests/`: examples of allowed and rejected requests, database rules, and failure recovery.

For the registration/login walkthrough and interview questions, read
[Milestone 2](docs/milestone-2.md).

For project creation, adding a teammate, and testing access rules, read
[Milestone 3](docs/milestone-3.md).

## Try projects and membership

Log in and authorize in `/docs`. If the server restarted, log in again because
the development signing key changes on restart unless you configured a stable key.

1. Execute `POST /api/projects` with:

   ```json
   {"name": "College Website", "description": "Track bugs in our college website"}
   ```

2. Save the returned project ID. `GET /api/projects` should now show it.
3. Execute `GET /api/projects/{project_id}/members`. You are already listed as
   the owner: project creation saves your membership automatically.
4. Register a second local practice account, for example `asha@example.com`,
   with its own name and a password of at least 12 characters.
5. While authorized as the owner, execute
   `POST /api/projects/{project_id}/members` with:

   ```json
   {"email": "asha@example.com"}
   ```

6. Log in as Asha and replace the authorized token. She can now read the project
   and its member list. Trying to edit the project or add another member returns
   `403`. A registered user outside the project gets `404` when requesting its
   details, and does not see it in their project list.

Adding a member grants access immediately and requires that person's account to
exist. The owner can remove a member with
`DELETE /api/projects/{project_id}/members/{user_id}`. An owner cannot remove
themselves. Members referenced as an issue's reporter or assignee cannot be
removed: the request returns `409` and their membership remains intact. This
protects existing issue relationships. Project ownership transfer and project
deletion are not part of this milestone.

A primary key identifies a row. A foreign key points to an existing row in
another table. `project_members` uses `(project_id, user_id)` as its primary key,
which means the same person cannot join one project twice.

```text
users ----< project_members >---- projects
  |                                  |
  +-- reporter / assignee ---- issues-+
```

An issue's `(project_id, assignee_id)` must match a membership row. This is a
composite foreign key: a user belonging to a different project cannot be
assigned this project's issue. The same rule applies to its reporter. An issue
can have no assignee. Project creation adds the owner as a member in the same
transaction, so a membership failure also rolls back the new project.

An enum limits a field to known values. Status is `open`, `in_progress`, or
`resolved`; priority is `low`, `medium`, `high`, or `critical`. The database
also checks these values, even when an update bypasses the API.

## Next milestones

4. Issue endpoints and permission checks for viewing, editing, assignment, and deletion.
5. Comments, change history, filters, and pagination.
6. Frontend, deployment, and interview walkthrough.

For now, `create_all()` creates missing tables on startup. It cannot migrate
existing tables after a model changes; introduce migrations before changing a
schema that contains data worth keeping. This milestone uses SQLite only;
PostgreSQL configuration and verification come later.

## Useful references

- FastAPI database dependencies: https://fastapi.tiangolo.com/tutorial/sql-databases/
- SQLAlchemy model declarations: https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- SQLite foreign key support: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support
- FastAPI password hashing and JWTs: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
