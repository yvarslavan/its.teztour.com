# SSL Verification Remediation

## Scope
- `redmine.py`
- `redmine_api.py`

## What was fixed
1. Removed insecure SSL warning suppression:
   - deleted `urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)`.
2. Removed all insecure TLS settings:
   - `session.verify = False` -> secure setting.
   - `verify: False` in Redmine requests config -> secure setting.
3. Added centralized SSL verify resolver in both files:
   - `_get_requests_verify_setting()`
   - behavior:
     - default: `True` (strict verification),
     - if provided: uses `REQUESTS_CA_BUNDLE` or `SSL_CA_BUNDLE` path (for self-signed/internal CA).

## Self-signed certificates
- Set one of:
  - `REQUESTS_CA_BUNDLE=/path/to/ca_bundle.pem`
  - `SSL_CA_BUNDLE=/path/to/ca_bundle.pem`
- Do not disable verification.

## Validation
- Static scan confirms no insecure markers remain:
  - no `verify=False`
  - no `disable_warnings(...)`
- Syntax check:
  - `python -m py_compile redmine.py redmine_api.py`
