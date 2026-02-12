# SECRET_KEY Security Remediation

## Scope
- `blog/__init__.py`
- `blog/settings.py`
- `tests/test_secret_key_security.py`

## What was changed
1. Removed hardcoded fallback secret values.
2. Enforced `SECRET_KEY` from environment only (fail-fast).
3. Added automated tests to detect:
   - hardcoded `SECRET_KEY`/`app.secret_key` assignments;
   - known compromised secret literals previously found in the codebase.

## Current behavior
- App startup now raises:
  - `RuntimeError("SECRET_KEY is required! Set it in environment variables.")`
  when `SECRET_KEY` is missing.

## Operational actions required
1. Generate a new strong random `SECRET_KEY` for each environment.
2. Set it via environment variables / secret manager.
3. Remove old values from:
   - `.env` files,
   - CI/CD variables history (if possible),
   - server configs and process managers.
4. Restart application instances after secret rotation.

## Key invalidation impact
- Rotating `SECRET_KEY` invalidates existing signed sessions/cookies.
- Users may need to log in again.

## Verification
- Run:
  - `pytest tests/test_secret_key_security.py`
