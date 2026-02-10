import os
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv


def _is_wsl() -> bool:
    try:
        with open("/proc/version", "r", encoding="utf-8") as version_file:
            return "microsoft" in version_file.read().lower()
    except OSError:
        return False


def _resolve_env_path(base_dir: Path, env_mode: str) -> Path:
    explicit_env = os.getenv("ENV_FILE")
    if explicit_env:
        explicit_path = Path(explicit_env)
        return (
            explicit_path if explicit_path.is_absolute() else base_dir / explicit_path
        )

    if env_mode == "production":
        candidates = [base_dir / ".env.production", base_dir / ".env"]
    else:
        if _is_wsl():
            candidates = [base_dir / ".env", base_dir / ".env.development"]
        else:
            candidates = [base_dir / ".env.development", base_dir / ".env"]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def load_environment(
    base_dir: Optional[Path] = None,
    env_mode: Optional[str] = None,
) -> Tuple[Path, bool, bool]:
    resolved_base = base_dir or Path(__file__).resolve().parent
    mode = env_mode or os.environ.get("FLASK_ENV", "development")
    env_path = _resolve_env_path(resolved_base, mode)

    env_marker = os.environ.get("ENV_FILE_LOADED")
    if env_marker:
        try:
            if Path(env_marker).resolve() == env_path.resolve():
                return env_path, False, _is_wsl()
        except OSError:
            pass

    loaded = False
    if env_path.exists():
        load_dotenv(env_path)
        os.environ["ENV_FILE_LOADED"] = str(env_path)
        loaded = True

    return env_path, loaded, _is_wsl()
