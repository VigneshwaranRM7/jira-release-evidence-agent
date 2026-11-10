# FastAPI Backend - Project Folder Structure & Scaffolding Guide

This document captures the exact directory and file structure of the FastAPI backend project. You can inject or use this document directly into another project, an AI agent, or run the included generator script to automatically scaffold the entire folder and file hierarchy.

---

## 1. Complete Directory Tree

```text
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── add_env_to_cloudrun.sh
├── conftest.py
├── db.py
├── definitions.py
├── docker.sh
├── docker_build.sh
├── main.py
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── scheduler.py
├── setup.py
├── setup.sh
├── start_server.sh
├── .github/
│   └── workflows/
│       └── deploy.yml
├── adhoc/
│   ├── __init__.py
│   ├── backfill_final_approver.py
│   ├── seed_master_data.py
│   └── tags.py
├── auth/
│   ├── jwt_handler.py
│   └── oauth_handler.py
├── controllers/
│   └── v1/
│       ├── analytics/
│       │   ├── __init__.py
│       │   ├── dashboard.py
│       │   ├── escalation.py
│       │   └── reporting.py
│       ├── cloudflare.py
│       ├── cloudinary_upload.py
│       ├── common/
│       │   ├── college_tags.py
│       │   ├── sql_helpers.py
│       │   ├── tags.py
│       │   ├── user.py
│       │   └── utils.py
│       ├── database.py
│       ├── esign/
│       │   ├── __init__.py
│       │   └── opensign.py
│       ├── jwt.py
│       ├── notification/
│       │   ├── __init__.py
│       │   └── notification.py
│       ├── organization/
│       │   ├── __init__.py
│       │   ├── categories.py
│       │   ├── logo.py
│       │   ├── master_request.py
│       │   ├── master_roles.py
│       │   ├── modes.py
│       │   ├── org_scope_lists.py
│       │   ├── request_types.py
│       │   ├── sub_categories.py
│       │   ├── types.py
│       │   ├── workflow_seed.py
│       │   └── workflows.py
│       ├── report/
│       │   ├── __init__.py
│       │   ├── report_pdf.py
│       │   └── templates/
│       │       ├── report.css
│       │       └── report.html
│       ├── repository/
│       │   ├── __init__.py
│       │   └── repository.py
│       ├── request/
│       │   ├── __init__.py
│       │   ├── chat.py
│       │   └── request.py
│       ├── scheduler/
│       │   ├── __init__.py
│       │   └── escalation.py
│       ├── simulation/
│       │   ├── __init__.py
│       │   └── simulation.py
│       ├── system/
│       │   ├── __init__.py
│       │   └── auth.py
│       └── user/
│           ├── auth.py
│           ├── onboarding.py
│           ├── profile.py
│           └── signature.py
├── docs/
│   └── signing-flow-changes.md
├── instruction/
│   ├── auto_esculate.md
│   ├── category.md
│   ├── chairman_override_action.md
│   ├── core_flow.md
│   ├── frontend_workflow_usage.md
│   ├── login.md
│   ├── login_plan.md
│   ├── mongodb-migration.md
│   ├── request.md
│   ├── request_plan.md
│   ├── role.md
│   └── workflow.md
├── manuals/
│   └── file-tracker-guide.pdf
├── models/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── mixins.py
│       ├── analytics/
│       │   ├── __init__.py
│       │   ├── dashboard.py
│       │   ├── escalation.py
│       │   └── reporting.py
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── role.py
│       │   └── user.py
│       ├── common/
│       │   ├── base.py
│       │   ├── college_tags.py
│       │   ├── media_uploader.py
│       │   └── tags.py
│       ├── notification/
│       │   ├── __init__.py
│       │   └── notification.py
│       ├── organization/
│       │   ├── __init__.py
│       │   ├── category.py
│       │   ├── master_roles.py
│       │   ├── mode.py
│       │   ├── org_scope_lists.py
│       │   ├── request_type.py
│       │   ├── sub_category.py
│       │   ├── type.py
│       │   └── workflow.py
│       ├── repository/
│       │   └── repository.py
│       ├── request/
│       │   ├── __init__.py
│       │   ├── chat.py
│       │   └── request.py
│       └── user/
│           ├── analytics.py
│           ├── auth.py
│           ├── onboarding.py
│           └── profile.py
├── request_tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_analytics_dashboard.py
│   ├── test_analytics_escalation.py
│   ├── test_analytics_reporting.py
│   ├── test_chain_completion.py
│   ├── test_chain_completion_e2e.py
│   ├── test_chain_debug.py
│   ├── test_chairman_executive_review.py
│   ├── test_chat_access.py
│   ├── test_escalation.py
│   ├── test_final_approvers.py
│   ├── test_notifications.py
│   ├── test_privileged_override.py
│   ├── test_recent_activity.py
│   ├── test_repository_audit.py
│   ├── test_repository_flow.py
│   ├── test_request_dashboard_stats.py
│   ├── test_request_flow.py
│   ├── test_workflow_bypass_initiators.py
│   ├── test_workflow_delete_guards.py
│   ├── test_workflow_initiators.py
│   └── test_workflow_versioning.py
├── routes/
│   └── v1/
│       ├── analytics/
│       │   ├── __init__.py
│       │   └── dashboard.py
│       ├── common/
│       │   ├── college_tags.py
│       │   ├── manuals.py
│       │   ├── media_uploader.py
│       │   ├── tags.py
│       │   └── user.py
│       ├── notification/
│       │   ├── __init__.py
│       │   └── notification.py
│       ├── organization/
│       │   ├── __init__.py
│       │   ├── logo.py
│       │   ├── master_management/
│       │   │   ├── __init__.py
│       │   │   ├── category.py
│       │   │   ├── mode.py
│       │   │   ├── request_type.py
│       │   │   ├── role.py
│       │   │   ├── sub_category.py
│       │   │   ├── type.py
│       │   └── settings.py
│       ├── repository/
│       │   ├── __init__.py
│       │   └── repository.py
│       ├── request/
│       │   ├── __init__.py
│       │   ├── attachments.py
│       │   ├── chat.py
│       │   ├── report.py
│       │   └── request.py
│       ├── simulation/
│       │   ├── __init__.py
│       │   └── simulation.py
│       ├── system/
│       │   ├── __init__.py
│       │   └── auth.py
│       └── user/
│           ├── auth.py
│           └── signature.py
├── scripts/
│   ├── _patch_chairman.py
│   ├── _test_patch_chairman.py
│   ├── _test_patch_user.py
│   ├── add_address_field.py
│   ├── add_college_level_to_roles.py
│   ├── add_college_logos.py
│   ├── add_logo_field.py
│   ├── add_profile_to_users.py
│   ├── add_signature_field.py
│   ├── clone_staging_to_local.py
│   ├── fix_org_vs_college_roles.py
│   ├── gen_example_pdf.py
│   ├── import_mock_requests.py
│   ├── migrate_approval_actions.py
│   ├── migrate_role_permissions.py
│   ├── seed_col002.py
│   ├── seed_mentor.py
│   ├── seed_real_user.py
│   ├── seed_users_excel.py
│   ├── seed_vice_chairman.py
│   ├── test_escalation_real.py
│   ├── verify_final.py
│   ├── verify_migration_data.py
│   ├── verify_migration_deep.py
│   ├── workflow_scripts.py
│   └── workflow_seed_excel.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── run_audit_test.py
│   ├── run_workflow_test.py
│   ├── test_auth_api.py
│   ├── test_jwt.py
│   ├── test_role_checker.py
│   ├── test_roles_api.py
│   ├── test_sub_categories.py
│   └── test_workflow_flow.py
└── utils/
    ├── __init__.py
    ├── context.py
    ├── email.py
    ├── maileroo.py
    └── permission.py
```

---

## 2. Architecture & Layer Responsibilities

| Directory | Layer / Responsibility |
| :--- | :--- |
| `main.py` | FastAPI application factory, CORS middleware, global error handlers, route registration. |
| `db.py` | Database connection client (MongoDB Motor / PyMongo or SQL engine / session pool). |
| `scheduler.py` | Background tasks / cron jobs (APScheduler / Celery / custom scheduler). |
| `definitions.py` | Global constants, path definitions, and system-wide enumerations. |
| `routes/v1/` | **Presentation Layer**: FastAPI APIRouter endpoints defining HTTP methods, query params, request bodies, and status codes. |
| `controllers/v1/` | **Business Logic Layer**: Core domain services, business rules, multi-step transactions, and data processing. |
| `models/v1/` | **Data Layer**: Pydantic schemas (request/response validation) and database document/table entities. |
| `auth/` | Authentication helpers (OAuth2 flows, JWT decoding and verification). |
| `utils/` | Shared utilities (email delivery, RBAC permissions, execution context, third-party integrations). |
| `scripts/` | Migration scripts, master data seeding, backfills, and database repair jobs. |
| `adhoc/` | One-off administrative and patch execution utilities. |
| `tests/` & `request_tests/` | Pytest suites: unit tests, API integration tests, and end-to-end request lifecycle tests. |

---

## 3. Flat Relative Paths List

This list can be ingested directly by shell scripts, CI/CD runners, or AI tools to recreate every directory and file:

```text
.env.example
.github/workflows/deploy.yml
.gitignore
Dockerfile
README.md
add_env_to_cloudrun.sh
adhoc/__init__.py
adhoc/backfill_final_approver.py
adhoc/seed_master_data.py
adhoc/tags.py
auth/jwt_handler.py
auth/oauth_handler.py
conftest.py
controllers/v1/analytics/__init__.py
controllers/v1/analytics/dashboard.py
controllers/v1/analytics/escalation.py
controllers/v1/analytics/reporting.py
controllers/v1/cloudflare.py
controllers/v1/cloudinary_upload.py
controllers/v1/common/college_tags.py
controllers/v1/common/sql_helpers.py
controllers/v1/common/tags.py
controllers/v1/common/user.py
controllers/v1/common/utils.py
controllers/v1/database.py
controllers/v1/esign/__init__.py
controllers/v1/esign/opensign.py
controllers/v1/jwt.py
controllers/v1/notification/__init__.py
controllers/v1/notification/notification.py
controllers/v1/organization/__init__.py
controllers/v1/organization/categories.py
controllers/v1/organization/logo.py
controllers/v1/organization/master_request.py
controllers/v1/organization/master_roles.py
controllers/v1/organization/modes.py
controllers/v1/organization/org_scope_lists.py
controllers/v1/organization/request_types.py
controllers/v1/organization/sub_categories.py
controllers/v1/organization/types.py
controllers/v1/organization/workflow_seed.py
controllers/v1/organization/workflows.py
controllers/v1/report/__init__.py
controllers/v1/report/report_pdf.py
controllers/v1/report/templates/report.css
controllers/v1/report/templates/report.html
controllers/v1/repository/__init__.py
controllers/v1/repository/repository.py
controllers/v1/request/__init__.py
controllers/v1/request/chat.py
controllers/v1/request/request.py
controllers/v1/scheduler/__init__.py
controllers/v1/scheduler/escalation.py
controllers/v1/simulation/__init__.py
controllers/v1/simulation/simulation.py
controllers/v1/system/__init__.py
controllers/v1/system/auth.py
controllers/v1/user/auth.py
controllers/v1/user/onboarding.py
controllers/v1/user/profile.py
controllers/v1/user/signature.py
db.py
definitions.py
docker.sh
docker_build.sh
docs/signing-flow-changes.md
instruction/auto_esculate.md
instruction/category.md
instruction/chairman_override_action.md
instruction/core_flow.md
instruction/frontend_workflow_usage.md
instruction/login.md
instruction/login_plan.md
instruction/mongodb-migration.md
instruction/request.md
instruction/request_plan.md
instruction/role.md
instruction/workflow.md
main.py
models/v1/__init__.py
models/v1/analytics/__init__.py
models/v1/analytics/dashboard.py
models/v1/analytics/escalation.py
models/v1/analytics/reporting.py
models/v1/auth/__init__.py
models/v1/auth/role.py
models/v1/auth/user.py
models/v1/common/base.py
models/v1/common/college_tags.py
models/v1/common/media_uploader.py
models/v1/common/tags.py
models/v1/mixins.py
models/v1/notification/__init__.py
models/v1/notification/notification.py
models/v1/organization/__init__.py
models/v1/organization/category.py
models/v1/organization/master_roles.py
models/v1/organization/mode.py
models/v1/organization/org_scope_lists.py
models/v1/organization/request_type.py
models/v1/organization/sub_category.py
models/v1/organization/type.py
models/v1/organization/workflow.py
models/v1/repository/repository.py
models/v1/request/__init__.py
models/v1/request/chat.py
models/v1/request/request.py
models/v1/user/analytics.py
models/v1/user/auth.py
models/v1/user/onboarding.py
models/v1/user/profile.py
pyproject.toml
pytest.ini
request_tests/__init__.py
request_tests/conftest.py
request_tests/test_analytics_dashboard.py
request_tests/test_analytics_escalation.py
request_tests/test_analytics_reporting.py
request_tests/test_chain_completion.py
request_tests/test_chain_completion_e2e.py
request_tests/test_chain_debug.py
request_tests/test_chairman_executive_review.py
request_tests/test_chat_access.py
request_tests/test_escalation.py
request_tests/test_final_approvers.py
request_tests/test_notifications.py
request_tests/test_privileged_override.py
request_tests/test_recent_activity.py
request_tests/test_repository_audit.py
request_tests/test_repository_flow.py
request_tests/test_request_dashboard_stats.py
request_tests/test_request_flow.py
request_tests/test_workflow_bypass_initiators.py
request_tests/test_workflow_delete_guards.py
request_tests/test_workflow_initiators.py
request_tests/test_workflow_versioning.py
requirements.txt
routes/v1/analytics/__init__.py
routes/v1/analytics/dashboard.py
routes/v1/common/college_tags.py
routes/v1/common/manuals.py
routes/v1/common/media_uploader.py
routes/v1/common/tags.py
routes/v1/common/user.py
routes/v1/notification/__init__.py
routes/v1/notification/notification.py
routes/v1/organization/__init__.py
routes/v1/organization/logo.py
routes/v1/organization/master_management/__init__.py
routes/v1/organization/master_management/category.py
routes/v1/organization/master_management/mode.py
routes/v1/organization/master_management/request_type.py
routes/v1/organization/master_management/role.py
routes/v1/organization/master_management/sub_category.py
routes/v1/organization/master_management/type.py
routes/v1/organization/settings.py
routes/v1/repository/__init__.py
routes/v1/repository/repository.py
routes/v1/request/__init__.py
routes/v1/request/attachments.py
routes/v1/request/chat.py
routes/v1/request/report.py
routes/v1/request/request.py
routes/v1/simulation/__init__.py
routes/v1/simulation/simulation.py
routes/v1/system/__init__.py
routes/v1/system/auth.py
routes/v1/user/auth.py
routes/v1/user/signature.py
scheduler.py
scripts/_patch_chairman.py
scripts/_test_patch_chairman.py
scripts/_test_patch_user.py
scripts/add_address_field.py
scripts/add_college_level_to_roles.py
scripts/add_college_logos.py
scripts/add_logo_field.py
scripts/add_profile_to_users.py
scripts/add_signature_field.py
scripts/clone_staging_to_local.py
scripts/fix_org_vs_college_roles.py
scripts/gen_example_pdf.py
scripts/import_mock_requests.py
scripts/migrate_approval_actions.py
scripts/migrate_role_permissions.py
scripts/seed_col002.py
scripts/seed_mentor.py
scripts/seed_real_user.py
scripts/seed_users_excel.py
scripts/seed_vice_chairman.py
scripts/test_escalation_real.py
scripts/verify_final.py
scripts/verify_migration_data.py
scripts/verify_migration_deep.py
scripts/workflow_scripts.py
scripts/workflow_seed_excel.py
setup.py
setup.sh
start_server.sh
tests/__init__.py
tests/conftest.py
tests/run_audit_test.py
tests/run_workflow_test.py
tests/test_auth_api.py
tests/test_jwt.py
tests/test_role_checker.py
tests/test_roles_api.py
tests/test_sub_categories.py
tests/test_workflow_flow.py
utils/__init__.py
utils/context.py
utils/email.py
utils/maileroo.py
utils/permission.py
```

---

## 4. Automatic Scaffolding Script (Python)

Copy and execute this Python script in any empty target directory to automatically recreate all folders and files:

```python
import os
from pathlib import Path

STRUCTURE = [
    ".env.example",
    ".github/workflows/deploy.yml",
    ".gitignore",
    "Dockerfile",
    "README.md",
    "add_env_to_cloudrun.sh",
    "adhoc/__init__.py",
    "adhoc/backfill_final_approver.py",
    "adhoc/seed_master_data.py",
    "adhoc/tags.py",
    "auth/jwt_handler.py",
    "auth/oauth_handler.py",
    "conftest.py",
    "controllers/v1/analytics/__init__.py",
    "controllers/v1/analytics/dashboard.py",
    "controllers/v1/analytics/escalation.py",
    "controllers/v1/analytics/reporting.py",
    "controllers/v1/cloudflare.py",
    "controllers/v1/cloudinary_upload.py",
    "controllers/v1/common/college_tags.py",
    "controllers/v1/common/sql_helpers.py",
    "controllers/v1/common/tags.py",
    "controllers/v1/common/user.py",
    "controllers/v1/common/utils.py",
    "controllers/v1/database.py",
    "controllers/v1/esign/__init__.py",
    "controllers/v1/esign/opensign.py",
    "controllers/v1/jwt.py",
    "controllers/v1/notification/__init__.py",
    "controllers/v1/notification/notification.py",
    "controllers/v1/organization/__init__.py",
    "controllers/v1/organization/categories.py",
    "controllers/v1/organization/logo.py",
    "controllers/v1/organization/master_request.py",
    "controllers/v1/organization/master_roles.py",
    "controllers/v1/organization/modes.py",
    "controllers/v1/organization/org_scope_lists.py",
    "controllers/v1/organization/request_types.py",
    "controllers/v1/organization/sub_categories.py",
    "controllers/v1/organization/types.py",
    "controllers/v1/organization/workflow_seed.py",
    "controllers/v1/organization/workflows.py",
    "controllers/v1/report/__init__.py",
    "controllers/v1/report/report_pdf.py",
    "controllers/v1/report/templates/report.css",
    "controllers/v1/report/templates/report.html",
    "controllers/v1/repository/__init__.py",
    "controllers/v1/repository/repository.py",
    "controllers/v1/request/__init__.py",
    "controllers/v1/request/chat.py",
    "controllers/v1/request/request.py",
    "controllers/v1/scheduler/__init__.py",
    "controllers/v1/scheduler/escalation.py",
    "controllers/v1/simulation/__init__.py",
    "controllers/v1/simulation/simulation.py",
    "controllers/v1/system/__init__.py",
    "controllers/v1/system/auth.py",
    "controllers/v1/user/auth.py",
    "controllers/v1/user/onboarding.py",
    "controllers/v1/user/profile.py",
    "controllers/v1/user/signature.py",
    "db.py",
    "definitions.py",
    "docker.sh",
    "docker_build.sh",
    "docs/signing-flow-changes.md",
    "instruction/auto_esculate.md",
    "instruction/category.md",
    "instruction/chairman_override_action.md",
    "instruction/core_flow.md",
    "instruction/frontend_workflow_usage.md",
    "instruction/login.md",
    "instruction/login_plan.md",
    "instruction/mongodb-migration.md",
    "instruction/request.md",
    "instruction/request_plan.md",
    "instruction/role.md",
    "instruction/workflow.md",
    "main.py",
    "models/v1/__init__.py",
    "models/v1/analytics/__init__.py",
    "models/v1/analytics/dashboard.py",
    "models/v1/analytics/escalation.py",
    "models/v1/analytics/reporting.py",
    "models/v1/auth/__init__.py",
    "models/v1/auth/role.py",
    "models/v1/auth/user.py",
    "models/v1/common/base.py",
    "models/v1/common/college_tags.py",
    "models/v1/common/media_uploader.py",
    "models/v1/common/tags.py",
    "models/v1/mixins.py",
    "models/v1/notification/__init__.py",
    "models/v1/notification/notification.py",
    "models/v1/organization/__init__.py",
    "models/v1/organization/category.py",
    "models/v1/organization/master_roles.py",
    "models/v1/organization/mode.py",
    "models/v1/organization/org_scope_lists.py",
    "models/v1/organization/request_type.py",
    "models/v1/organization/sub_category.py",
    "models/v1/organization/type.py",
    "models/v1/organization/workflow.py",
    "models/v1/repository/repository.py",
    "models/v1/request/__init__.py",
    "models/v1/request/chat.py",
    "models/v1/request/request.py",
    "models/v1/user/analytics.py",
    "models/v1/user/auth.py",
    "models/v1/user/onboarding.py",
    "models/v1/user/profile.py",
    "pyproject.toml",
    "pytest.ini",
    "request_tests/__init__.py",
    "request_tests/conftest.py",
    "request_tests/test_analytics_dashboard.py",
    "request_tests/test_analytics_escalation.py",
    "request_tests/test_analytics_reporting.py",
    "request_tests/test_chain_completion.py",
    "request_tests/test_chain_completion_e2e.py",
    "request_tests/test_chain_debug.py",
    "request_tests/test_chairman_executive_review.py",
    "request_tests/test_chat_access.py",
    "request_tests/test_escalation.py",
    "request_tests/test_final_approvers.py",
    "request_tests/test_notifications.py",
    "request_tests/test_privileged_override.py",
    "request_tests/test_recent_activity.py",
    "request_tests/test_repository_audit.py",
    "request_tests/test_repository_flow.py",
    "request_tests/test_request_dashboard_stats.py",
    "request_tests/test_request_flow.py",
    "request_tests/test_workflow_bypass_initiators.py",
    "request_tests/test_workflow_delete_guards.py",
    "request_tests/test_workflow_initiators.py",
    "request_tests/test_workflow_versioning.py",
    "requirements.txt",
    "routes/v1/analytics/__init__.py",
    "routes/v1/analytics/dashboard.py",
    "routes/v1/common/college_tags.py",
    "routes/v1/common/manuals.py",
    "routes/v1/common/media_uploader.py",
    "routes/v1/common/tags.py",
    "routes/v1/common/user.py",
    "routes/v1/notification/__init__.py",
    "routes/v1/notification/notification.py",
    "routes/v1/organization/__init__.py",
    "routes/v1/organization/logo.py",
    "routes/v1/organization/master_management/__init__.py",
    "routes/v1/organization/master_management/category.py",
    "routes/v1/organization/master_management/mode.py",
    "routes/v1/organization/master_management/request_type.py",
    "routes/v1/organization/master_management/role.py",
    "routes/v1/organization/master_management/sub_category.py",
    "routes/v1/organization/master_management/type.py",
    "routes/v1/organization/settings.py",
    "routes/v1/repository/__init__.py",
    "routes/v1/repository/repository.py",
    "routes/v1/request/__init__.py",
    "routes/v1/request/attachments.py",
    "routes/v1/request/chat.py",
    "routes/v1/request/report.py",
    "routes/v1/request/request.py",
    "routes/v1/simulation/__init__.py",
    "routes/v1/simulation/simulation.py",
    "routes/v1/system/__init__.py",
    "routes/v1/system/auth.py",
    "routes/v1/user/auth.py",
    "routes/v1/user/signature.py",
    "scheduler.py",
    "scripts/_patch_chairman.py",
    "scripts/_test_patch_chairman.py",
    "scripts/_test_patch_user.py",
    "scripts/add_address_field.py",
    "scripts/add_college_level_to_roles.py",
    "scripts/add_college_logos.py",
    "scripts/add_logo_field.py",
    "scripts/add_profile_to_users.py",
    "scripts/add_signature_field.py",
    "scripts/clone_staging_to_local.py",
    "scripts/fix_org_vs_college_roles.py",
    "scripts/gen_example_pdf.py",
    "scripts/import_mock_requests.py",
    "scripts/migrate_approval_actions.py",
    "scripts/migrate_role_permissions.py",
    "scripts/seed_col002.py",
    "scripts/seed_mentor.py",
    "scripts/seed_real_user.py",
    "scripts/seed_users_excel.py",
    "scripts/seed_vice_chairman.py",
    "scripts/test_escalation_real.py",
    "scripts/verify_final.py",
    "scripts/verify_migration_data.py",
    "scripts/verify_migration_deep.py",
    "scripts/workflow_scripts.py",
    "scripts/workflow_seed_excel.py",
    "setup.py",
    "setup.sh",
    "start_server.sh",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/run_audit_test.py",
    "tests/run_workflow_test.py",
    "tests/test_auth_api.py",
    "tests/test_jwt.py",
    "tests/test_role_checker.py",
    "tests/test_roles_api.py",
    "tests/test_sub_categories.py",
    "tests/test_workflow_flow.py",
    "utils/__init__.py",
    "utils/context.py",
    "utils/email.py",
    "utils/maileroo.py",
    "utils/permission.py"
]

def scaffold(base_dir="."):
    base = Path(base_dir)
    print(f"Scaffolding project structure in '{base.resolve()}'...")
    created_dirs = set()
    created_files = 0

    for relative_path in STRUCTURE:
        target_path = base / relative_path
        parent = target_path.parent
        if parent not in created_dirs:
            parent.mkdir(parents=True, exist_ok=True)
            created_dirs.add(parent)
        if not target_path.exists():
            target_path.touch()
            created_files += 1

    print(f"Scaffolding completed! Created {created_files} files across {len(created_dirs)} directories.")

if __name__ == "__main__":
    scaffold()
```

---

## 5. Modular Clean FastAPI Boilerplate Template

If starting a brand-new service and you want this exact clean **Routes -> Controllers -> Models** pattern without the specific business entities:

```text
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── conftest.py
├── db.py
├── definitions.py
├── main.py
├── pyproject.toml
├── requirements.txt
├── scheduler.py
├── auth/
│   ├── __init__.py
│   ├── jwt_handler.py
│   └── oauth_handler.py
├── controllers/
│   └── v1/
│       ├── __init__.py
│       ├── auth.py
│       └── example_service.py
├── models/
│   └── v1/
│       ├── __init__.py
│       ├── mixins.py
│       └── example_model.py
├── routes/
│   └── v1/
│       ├── __init__.py
│       ├── auth.py
│       └── example_router.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_example.py
└── utils/
    ├── __init__.py
    ├── context.py
    └── permission.py
```

