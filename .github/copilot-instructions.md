# Copilot instructions for contributors (concise)

These instructions tell AI coding assistants the exact, repository-specific knowledge they need to be productive in this Flask Helpdesk codebase.

Be concise: prefer small, backwards-compatible edits and reference files so reviewers can validate changes quickly.

What this project is
- Flask-based Helpdesk / Kanban system. Core application lives in `blog/` (blueprints: `main`, `tasks`, `user`, `call`, `finesse`, `post`, `netmonitor`).
- Integrations: Redmine (REST + MySQL), ERP/Oracle (authentication), Firebase (web-push), APScheduler (background jobs).

Top-level entry points and config
- Dev server: `python app.py` (or `wsgi.py` for WSGI). See `ai-docs/basic-structure.md` and `GEMINI.md` for details.
- Config: `config.py` and `config.ini`. Env-overrides expected (use `.env.development` / `.env.production` patterns described in `GEMINI.md`).
- Dependencies: `requirements.txt` (Python) and `package.json` (Node, Playwright/E2E).

Quick commands (dev/test/debug)
- Install Python deps: pip install -r requirements.txt
- Install Node deps for Playwright: npm install
- Run dev server: python app.py
- Run Python tests: pytest tests/
- Run E2E Playwright tests: npm test
- View Playwright report: npm run show-report

Project-specific conventions (important to follow)
- Blueprints per domain: add server endpoints in the blueprint's `routes.py` or `api_routes.py` (e.g. task actions go in `blog/tasks/api_routes.py` and UI pages in `blog/tasks/routes.py`).
- Data source for task UI: Kanban/table components rely on `GET /tasks/get-my-tasks-direct-sql` implemented in `blog/tasks/routes.py` — prefer using that when changing UI data flows.
- Localization of statuses/priorities: always source from Redmine's MySQL mapping tables (`u_statuses`, `u_Priority`). Look at `redmine.py` and `mysql_db.py` for SQL helpers and examples.
- Auth: ERP/Oracle integration is central. Authentication flows and session values live in `erp_oracle.py` and `blog/user/routes.py`. Avoid hard-coded credentials and use session-based logic when interacting with Finesse/ERP.
- Notifications: background tasks live in `blog/scheduler_tasks.py` and `blog/notification_service.py`; Firebase push logic is in `blog/firebase_push_service.py`.
- Templates/static: front-end code for tasks lives under `blog/static/js/pages/tasks/` and templates under `blog/templates/` (edit both when changing UI). Key files: `KanbanManager.js`, `TasksAPI.js`, `layout.html`, `my_tasks.html`.
- Global logger and cache: use `blog/utils/logger.py` and `blog/utils/cache_manager.py` to keep consistent behavior.

Examples (short, concrete)
- To add a new task API to change a custom field:
  1. server: add a `PUT /tasks/api/task/<id>/custom_field` handler in `blog/tasks/api_routes.py` that updates via Redmine connector or local DB and returns localized names.
  2. front: add a method in `blog/static/js/pages/tasks/services/TasksAPI.js` and call it from the relevant component under `components/`.

Files to read first (fast path for context)
- `blog/__init__.py` — app factory and blueprint wiring
- `blog/tasks/routes.py` and `blog/tasks/api_routes.py` — tasks data sources and APIs
- `redmine.py`, `mysql_db.py` — Redmine/MySQL mapping & helpers
- `erp_oracle.py` and `blog/user/routes.py` — authentication/session patterns
- `blog/firebase_push_service.py`, `blog/scheduler_tasks.py` — background jobs and push flow
- `blog/static/js/pages/tasks/components/KanbanManager.js` and `blog/static/js/pages/tasks/services/TasksAPI.js` — front-end DnD and API usage
- `docs/INDEX.md`, `ai-docs/basic-structure.md`, `GEMINI.md` — high-level project docs

What to avoid / common pitfalls
- Don't change localized status/priority strings in code; they come from MySQL/Redmine. Changing these requires DB mapping updates (`mysql_db.py`/`redmine.py`).
- Don't bypass session-based ERP credentials when calling Finesse or Oracle APIs — follow the patterns in `blog/finesse/routes.py` and `blog/user/routes.py`.
- Avoid adding new global APScheduler instances; use existing scheduler tasks in `blog/scheduler_tasks.py`.

Developer workflows & testing notes
- If you change front-end JS, run Playwright E2E tests (`npm test`) and inspect the report (`npm run show-report`). Playwright report is under `playwright-report/`.
- For DB-related changes, add Alembic migrations in `migrations/` and update `blog/migrations.py` helpers if needed.
- Logging: check `logs/` (or `app_err.log`) for runtime errors when debugging locally.

Merging and code style
- Python: follow PEP8. Repo uses Black/Flake8 norms (see `GEMINI.md`).
- Keep controllers thin: prefer moving business logic into `blog/utils/` or service modules.

If you need more context
- Search `memory-bank/` for design notes and `docs/` for feature READMEs.
- If a change touches Redmine or Oracle integrations, mention required environment variables from `config.py`/`config.ini` in the PR description.

If this file is out of date or incomplete, tell me which area (backend, front-end, Redmine, ERP, tests) needs more details and I'll update.
