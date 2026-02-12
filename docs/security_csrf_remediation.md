# CSRF Security Remediation

## Scope
- `blog/__init__.py`
- `blog/templates/chat_with_assistant.html`
- `tests/test_secret_key_security.py` (security guardrail extension)

## Changes made
1. CSRF is now forced ON in all environments:
   - `app.config["WTF_CSRF_ENABLED"] = True` is set unconditionally.
2. Removed environment-specific CSRF toggles from app init:
   - debug branch no longer disables CSRF.
   - production branch no longer redefines `WTF_CSRF_ENABLED`.
3. Added missing CSRF token to POST form:
   - `blog/templates/chat_with_assistant.html` now includes hidden `csrf_token`.
4. Added automated regression check:
   - test fails if code contains explicit CSRF disable markers like `WTF_CSRF_ENABLED=False`.

## `@csrf.exempt` policy
- Existing `@csrf.exempt` decorators were kept where they appear to be JSON/API endpoints.
- Recommended follow-up:
  - review each exempt route and keep only API/machine-to-machine endpoints exempted.

## Validation performed
- Security tests:
  - `python -m unittest tests.test_secret_key_security -v`
  - result: `OK`

## Notes
- Enabling CSRF globally may reject POSTs from templates/scripts that do not send token.
- Include token in forms (`hidden_tag()` or explicit hidden `csrf_token`) and headers for AJAX requests.
