import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Match direct hardcoded secret assignments like:
# SECRET_KEY = "..."
# app.secret_key = '...'
HARDCODED_SECRET_PATTERNS = [
    re.compile(r"\bSECRET_KEY\s*=\s*['\"][^'\"]+['\"]"),
    re.compile(r"\bapp\.secret_key\s*=\s*['\"][^'\"]+['\"]"),
]

# Explicitly block previously compromised keys.
KNOWN_COMPROMISED_LITERALS = [
    "e6914948deb30b6ece648d7ac6c81bc1fa822008d425dc38",
    "dev-key-flask-helpdesk-2024-fixed",
]

CSRF_DISABLED_MARKERS = [
    "WTF_CSRF_ENABLED=False",
    '"WTF_CSRF_ENABLED": False',
    "'WTF_CSRF_ENABLED': False",
]


def _iter_python_files():
    for path in ROOT.rglob("*.py"):
        if any(part in {".venv", "venv", "__pycache__", ".git"} for part in path.parts):
            continue
        if path.name == "test_secret_key_security.py":
            continue
        yield path


class SecretKeySecurityTest(unittest.TestCase):
    def test_no_hardcoded_secret_key_assignments(self):
        offenders = []
        for path in _iter_python_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in HARDCODED_SECRET_PATTERNS:
                if pattern.search(text):
                    offenders.append(str(path.relative_to(ROOT)))
                    break

        self.assertFalse(offenders, f"Hardcoded SECRET_KEY assignment found in: {offenders}")

    def test_no_known_compromised_secret_literals(self):
        offenders = []
        for path in _iter_python_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(secret in text for secret in KNOWN_COMPROMISED_LITERALS):
                offenders.append(str(path.relative_to(ROOT)))

        self.assertFalse(offenders, f"Compromised secret literals found in: {offenders}")

    def test_csrf_is_not_explicitly_disabled_in_code(self):
        offenders = []
        for path in _iter_python_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(marker in text for marker in CSRF_DISABLED_MARKERS):
                offenders.append(str(path.relative_to(ROOT)))

        self.assertFalse(offenders, f"CSRF explicitly disabled in: {offenders}")
