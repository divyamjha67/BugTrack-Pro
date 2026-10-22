# BugTrack Pro source definition index

Version 0.3.0 | Verified 22 October 2026

Line numbers refer to this packaged source snapshot. Later edits may move definitions.

The complete explanation is in INTERVIEW_GUIDE.md. This index helps locate the corresponding code.

## app/__init__.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| Module documentation only | module | 1 |

## app/auth.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `unauthorized` | function or method | 29 |
| `get_current_user` | function or method | 37 |
| `register` | function or method | 52 |
| `login` | function or method | 75 |
| `me` | function or method | 97 |

## app/database.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `Base` | class | 12 |
| `create_database_engine` | function or method | 21 |
| `create_database_engine.enable_foreign_keys` | function or method | 26 |
| `initialize_database` | function or method | 38 |
| `get_db` | function or method | 45 |

## app/main.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `create_app` | function or method | 18 |
| `create_app.lifespan` | async function | 20 |
| `create_app.validation_error` | async function | 36 |
| `create_app.root` | function or method | 46 |
| `create_app.health` | function or method | 54 |

## app/models.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `utc_now` | function or method | 21 |
| `IssueStatus` | class | 26 |
| `IssuePriority` | class | 32 |
| `enum_column` | function or method | 39 |
| `User` | class | 50 |
| `Project` | class | 63 |
| `ProjectMember` | class | 80 |
| `Issue` | class | 92 |

## app/permissions.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `get_member_project` | function or method | 12 |
| `require_project_owner` | function or method | 28 |

## app/projects.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `read_member` | function or method | 25 |
| `create_project` | function or method | 34 |
| `list_projects` | function or method | 53 |
| `get_project` | function or method | 67 |
| `update_project` | function or method | 72 |
| `list_members` | function or method | 85 |
| `add_member` | function or method | 99 |
| `remove_member` | function or method | 124 |

## app/schemas.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `LoginRequest` | class | 9 |
| `LoginRequest.normalize_email` | function or method | 17 |
| `RegisterRequest` | class | 22 |
| `RegisterRequest.trim_name` | function or method | 28 |
| `UserRead` | class | 32 |
| `TokenResponse` | class | 40 |
| `ProjectCreate` | class | 47 |
| `ProjectCreate.trim_name` | function or method | 55 |
| `ProjectUpdate` | class | 59 |
| `ProjectUpdate.trim_name` | function or method | 67 |
| `ProjectUpdate.require_non_null_changes` | function or method | 71 |
| `ProjectRead` | class | 79 |
| `ProjectMemberCreate` | class | 89 |
| `ProjectMemberCreate.normalize_email` | function or method | 96 |
| `ProjectMemberRead` | class | 100 |

## app/security.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `hash_password` | function or method | 21 |
| `verify_password` | function or method | 25 |
| `create_access_token` | function or method | 32 |
| `decode_access_token` | function or method | 43 |

## app/settings.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `AuthSettings` | class | 11 |
| `AuthSettings.__post_init__` | function or method | 15 |
| `AuthSettings.from_environment` | function or method | 22 |
| `get_auth_settings` | function or method | 29 |

## tests/conftest.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `database_engine` | function or method | 11 |
| `db` | function or method | 18 |
| `auth_settings` | function or method | 25 |
| `client` | function or method | 30 |

## tests/test_auth.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `registered_user` | function or method | 20 |
| `login` | function or method | 26 |
| `test_registration_normalizes_identity_and_stores_only_a_hash` | function or method | 31 |
| `test_same_password_gets_different_salted_hashes` | function or method | 45 |
| `test_duplicate_email_is_rejected_case_insensitively` | function or method | 53 |
| `test_invalid_registration_is_rejected_without_echoing_passwords` | function or method | 68 |
| `test_login_then_access_current_user` | function or method | 76 |
| `test_wrong_password_and_unknown_email_return_the_same_error` | function or method | 95 |
| `test_me_requires_a_valid_bearer_token` | function or method | 106 |
| `test_invalid_token_claims_are_rejected` | function or method | 116 |
| `test_password_whitespace_is_preserved` | function or method | 145 |

## tests/test_health.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `test_startup_creates_the_four_tables` | function or method | 9 |
| `test_health_checks_a_real_database_connection` | function or method | 16 |
| `test_health_returns_503_when_the_database_is_unavailable` | function or method | 22 |

## tests/test_models.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `make_project` | function or method | 8 |
| `test_members_can_report_and_receive_an_issue` | function or method | 25 |
| `test_an_issue_can_be_unassigned` | function or method | 40 |
| `test_duplicate_emails_are_rejected` | function or method | 48 |
| `test_duplicate_memberships_are_rejected` | function or method | 56 |
| `test_membership_in_another_project_does_not_grant_access` | function or method | 64 |
| `test_invalid_issue_values_are_rejected_by_the_database` | function or method | 87 |

## tests/test_projects.py

| Symbol | Kind | Definition line |
| --- | --- | --- |
| `actors` | function or method | 11 |
| `create_project` | function or method | 27 |
| `team_project` | function or method | 36 |
| `test_create_project_uses_current_user_and_adds_owner_membership` | function or method | 44 |
| `test_list_projects_returns_only_memberships` | function or method | 55 |
| `test_members_can_read_project_and_members` | function or method | 64 |
| `test_all_project_routes_require_authentication` | function or method | 81 |
| `test_outsiders_cannot_access_project_routes` | function or method | 92 |
| `test_members_cannot_manage_project_or_members` | function or method | 105 |
| `test_owner_can_update_project` | function or method | 112 |
| `test_invalid_project_creation_is_rejected` | function or method | 125 |
| `test_invalid_updates_do_not_change_project` | function or method | 132 |
| `test_add_member_normalizes_email_and_rejects_duplicates` | function or method | 139 |
| `test_adding_a_member_requires_an_existing_account` | function or method | 151 |
| `test_removal_revokes_access_immediately_for_an_existing_token` | function or method | 159 |
| `test_owner_cannot_be_removed_and_unknown_members_return_404` | function or method | 170 |
| `test_member_linked_to_issues_cannot_be_removed` | function or method | 178 |
| `test_creating_a_project_rolls_back_if_owner_membership_fails` | function or method | 192 |
| `test_nonexistent_project_and_inaccessible_project_look_the_same` | function or method | 205 |
