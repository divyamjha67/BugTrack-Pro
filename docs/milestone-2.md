# Milestone 2: understanding registration and login

The goal is to identify the person making a request. Deciding which projects
they may access comes in the next milestone.

## 1. Registration creates an account

```text
POST /api/auth/register
    -> schemas.py checks and normalizes the input
    -> auth.py checks whether the email already exists
    -> security.py hashes the password with Argon2id
    -> auth.py saves a User and commits the transaction
    -> UserRead returns only id, name, and email
```

`models.py` describes the stored row, including `password_hash`. `schemas.py`
describes the public response, which deliberately has no password field.
Separating them prevents internal fields from appearing accidentally in API
responses.

The database unique constraint is still necessary even though registration
checks the email first. Two requests can check at the same time. If both try to
insert, only one may succeed. The failed request rolls back its transaction.

## 2. Login checks a password and issues a token

The server finds the account and asks the hashing library whether the submitted
password matches the stored hash. It does not decrypt the hash. The library
stores a salt and algorithm parameters with each hash, so two accounts with the
same password still have different stored hashes.

On success, the server signs a JWT containing:

| Claim | Meaning |
| --- | --- |
| `sub` | User ID, represented as a string |
| `iat` | When the token was issued |
| `exp` | When the token expires |
| `iss` | The application that issued it |

The signature helps detect changes to the claims. A JWT is not encrypted: its
payload can be read, so it must not contain passwords or other secrets.

## 3. A protected endpoint checks the token

```text
GET /api/me + Authorization: Bearer <token>
    -> get_current_user reads the token
    -> checks the signature, algorithm, issuer, and expiry
    -> loads the user from the database
    -> the endpoint returns UserRead
```

`Depends(get_current_user)` means FastAPI runs this check before the endpoint.
We will reuse that dependency on project and issue endpoints. Those endpoints
will also check ownership or membership; having a valid token alone will not
grant access to every project.

## Try these three checks yourself

1. Register and log in through `/docs`, then authorize and call `/api/me`.
2. Log out of the explorer and call `/api/me` again. Explain why it returns `401`.
3. Try registering the same email using capital letters. Explain why it returns
   `409` instead of creating another account.

For interviews, practise answering: why hash instead of encrypt passwords, why
use a unique database constraint after checking the email, and how authentication
differs from authorization. Follow the code while explaining each answer.

References: [FastAPI's hashing and JWT guide](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
and [OWASP password storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
