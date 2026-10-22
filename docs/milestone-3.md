# Projects and access control

Project access is determined by current database membership. An authenticated
account can create its own projects; it cannot access arbitrary existing projects.

## Project creation

`POST /api/projects` accepts a name and optional description. The server derives
the owner ID from the authenticated account. It saves the project and the owner's
membership in one transaction, so a failed membership insert also rolls back the
new project. The request cannot nominate or change an owner through `owner_id`.

`GET /api/projects` lists only projects the current account belongs to. Project
names need not be unique; use the ID returned by creation or listing.

## Permissions

| Operation | Owner | Other member | Outsider |
| --- | --- | --- | --- |
| View project details | Allowed | Allowed | 404 |
| View member list | Allowed | Allowed | 404 |
| Edit project name or description | Allowed | 403 | 404 |
| Add a registered user | Allowed | 403 | 404 |
| Remove an eligible member | Allowed | 403 | 404 |

All operations require a valid token. The application gives outsiders the same
`404 Project not found` response for absent and inaccessible projects. Members
attempting an owner-only operation receive `403`.

`get_member_project` joins `projects` to `project_members` and filters by the
requested project ID and the current user ID. `require_project_owner` first
requires membership, then checks `owner_id`. Routes declare the appropriate
dependency before reading or changing project data.

## Membership management

The owner adds a member through `POST /api/projects/{project_id}/members`, with
the registered account's email in the body. Adding a membership grants access
immediately; there is no invitation or acceptance workflow. A missing account
returns `404`, and a duplicate membership returns `409`.

`GET /api/projects/{project_id}/members` exposes account ID, name, email, derived
owner/member role, and join time. Related account data is eagerly loaded to avoid
a separate user query for every membership.

The owner can remove an eligible member through
`DELETE /api/projects/{project_id}/members/{user_id}`. An owner cannot be removed.
An issue's reporter or assignee membership cannot be removed while referenced by
that issue. These conflicts return `409`; a successful removal returns `204`.

Membership is checked on each request. A removed member's existing token remains
an account credential but no longer grants access to that project. Access to
`/api/me` and other projects is unaffected.

## Database integrity and limits

The membership table uses `(project_id, user_id)` as its primary key. Composite
foreign keys on issues ensure their reporter and assignee belong to the same
project. Project creation handles owner membership atomically, but direct database
maintenance must also preserve that invariant.

Ownership transfer, project deletion, flexible member deactivation, and list
pagination are not implemented. Issue APIs remain planned. Tests cover access
for owners, members, and outsiders, membership revocation, duplicate handling,
linked-issue conflicts, and project-creation rollback.
