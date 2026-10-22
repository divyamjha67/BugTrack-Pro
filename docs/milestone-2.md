# Authentication

BugTrack Pro uses account credentials to issue an expiring JWT. Protected
endpoints verify that token and load the corresponding user from the database.

## Registration

`POST /api/auth/register` accepts a name, email, and password. Names are trimmed
and must contain 2-100 characters. Emails are validated, trimmed, and lowercased.
Passwords must contain 12-128 characters; their whitespace is preserved.

The server stores an Argon2id password hash and returns only the account ID,
name, and email. Registration returns `201`; an existing email returns `409`.
A database uniqueness rule also handles simultaneous duplicate registrations.

## Login

`POST /api/auth/login` accepts email and password as JSON. Successful login
returns `access_token`, `token_type`, `expires_in`, and the public account profile.
Unknown accounts and incorrect passwords receive the same `401` credential error.
Unknown-account requests still perform password verification against a dummy hash.

Access tokens use HS256 and have a default lifetime of 30 minutes. Required claims
are the account ID in `sub`, issue time in `iat`, expiry in `exp`, and issuer in
`iss`. The expected issuer is `bugtrack-pro`. Tokens are signed, not encrypted,
and do not contain passwords or project membership lists.

## Protected requests

Send this header with protected HTTP requests:

```text
Authorization: Bearer <access_token>
```

In `/docs`, paste only the complete token value into **Authorize**. Confirm the
current account through `GET /api/me` before performing project operations.
Registration does not automatically replace a previously saved authorization.

`get_current_user` verifies the signature and claims and loads the account.
Missing, expired, malformed, or invalid tokens return `401`. Response schemas
exclude password hashes, and validation errors omit submitted input values.

## Configuration and limitations

Set `BUGTRACK_SECRET_KEY` to the same securely generated value across restarts
and workers. It must contain at least 32 UTF-8 bytes. Without it, the application
generates a development key and previously issued tokens fail after a restart.
No `.env` loader is configured.

The API explorer's Logout control clears its saved token; it does not revoke
copied tokens on the server. Refresh tokens, a password-reset flow, email
verification, per-token revocation, and login throttling are future work.

## Implementation

- `schemas.py`: credential validation and public response models.
- `security.py`: password hashing, verification, and JWT creation/verification.
- `auth.py`: registration and login routes and the current-user dependency.
- `settings.py`: signing key and token lifetime.
- `tests/test_auth.py`: positive and negative authentication behavior.
