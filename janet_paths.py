import os
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent


def base_dir() -> Path:
    override = os.environ.get("HISTORICAL_JANET_BASE_PATH")
    root = Path(override).expanduser() if override else PACKAGE_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_path(path: str | Path) -> Path:
    p = Path(path).expanduser()
    return p if p.is_absolute() else base_dir() / p


def ensure_runtime_dirs() -> None:
    for rel in ("memory", "logs/sessions", "reports"):
        resolve_path(rel).mkdir(parents=True, exist_ok=True)
