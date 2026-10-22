# Milestone 3: projects, membership, and authorization

Authentication identifies the user. Authorization decides whether that user
may perform this particular action on this particular project.

## What you can do now

| Request | Owner | Other project member | Outsider |
| --- | --- | --- | --- |
| View project details | Allowed | Allowed | 404 |
| View member list | Allowed | Allowed | 404 |
| Edit project name/description | Allowed | 403 | 404 |
| Add a registered user | Allowed | 403 | 404 |
| Remove a member | Allowed, with restrictions | 403 | 404 |

Every request requires a valid access token. The project list contains only
projects with a membership record for the current user. An inaccessible project
and a nonexistent project both return `404`, so these endpoints do not disclose
private project details to outsiders.

## Create a project and automatically join it

In `/docs`, log in, authorize, and submit this to `POST /api/projects`:

```json
{
  "name": "College Website",
  "description": "Track bugs in our college website"
}
```

The server takes the owner ID from your verified token. You cannot nominate
another owner by adding `owner_id` to the request body; extra fields are rejected.

In `projects.py`, creating the project involves two writes:

```text
add Project -> flush to obtain its ID
    -> add ProjectMember for the owner
    -> commit both records together
```

`flush()` sends pending writes to the database but does not make the transaction
permanent. `commit()` completes it. If saving the membership fails, `rollback()`
undoes the project too. The tests simulate that failure to check this guarantee.

## Add a teammate and check the difference in access

1. Register `asha@example.com` with a name and a password of at least 12 characters.
2. Log in as the project owner and authorize with the owner's token.
3. Submit `{"email": "asha@example.com"}` to
   `POST /api/projects/{project_id}/members` using your project's returned ID.
4. Log in as Asha, replace the authorized token, and execute
   `GET /api/projects/{project_id}`. It succeeds.
5. As Asha, try `PATCH /api/projects/{project_id}` with
   `{"description": "Trying a member edit"}`. It returns `403`.
6. As the owner, execute that same update. It succeeds.

Adding an account grants membership immediately. It is a local application
operation, with no email delivery or acceptance step. The account must already
exist, and duplicate membership returns `409`.

## Read the access check

In `permissions.py`, `get_member_project` joins `projects` to `project_members`
and filters by both the requested project ID and the current user's ID. A token
for a different project member cannot bypass this query by changing the URL.

`require_project_owner` first uses that membership check, then compares the
project's stored `owner_id` to the current user. Project endpoints declare the
appropriate check with `Depends(...)`; FastAPI runs it before the operation.

We do not put a list of project memberships in the token. Each request checks
current database records, so removing a member revokes project access even if
they still have a valid login token. Their account and access to `/api/me` remain.

## Removing members safely

The owner may call `DELETE /api/projects/{project_id}/members/{user_id}`.
The owner cannot be removed. A member linked to existing issues also cannot be
removed, because those issues reference their membership. That request returns
`409`; the transaction rolls back and the member retains access. Reassigning an
issue can remove an assignment dependency, while a reporter dependency remains
until the associated issue is removed. We will revisit account deactivation and
history preservation before offering a more flexible removal policy.

## Your interview explanation

Practise explaining three choices while pointing to the code:

- Why the owner ID comes from the authenticated user rather than the request body.
- Why project creation and owner membership must be saved in one transaction.
- Why an existing login token does not grant access after membership is removed.

Next: issue creation, assignment, status changes, and permissions for each action.

References: [SQLAlchemy transactions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
and [FastAPI routers and dependencies](https://fastapi.tiangolo.com/tutorial/bigger-applications/).
