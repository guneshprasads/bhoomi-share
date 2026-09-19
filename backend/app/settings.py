"""Configuration, read from the environment once."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BACKEND_DIR / "templates"
STATIC_DIR = BACKEND_DIR / "static"
PROJECT_DIR = BACKEND_DIR.parent


def _flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    db_path: Path
    admin_token: str | None
    ip_salt: str
    secret_key: str
    secret_key_is_ephemeral: bool
    allowed_origins: tuple[str, ...]
    rate_limit_per_hour: int
    cookie_secure: bool
    seed_demo: bool

    templates_dir: Path = TEMPLATES_DIR
    static_dir: Path = STATIC_DIR


@lru_cache
def get_settings() -> Settings:
    db = Path(os.environ.get("BHOOMI_DB", "bhoomi.sqlite3"))
    if not db.is_absolute():
        db = BACKEND_DIR / db

    secret = (os.environ.get("BHOOMI_SECRET_KEY") or "").strip()
    ephemeral = not secret
    if ephemeral:
        # Fine for `uvicorn --reload` on a laptop; every restart logs everyone
        # out. Set BHOOMI_SECRET_KEY before deploying.
        secret = secrets.token_urlsafe(32)

    try:
        rate_limit = int(os.environ.get("BHOOMI_RATE_LIMIT", "8"))
    except ValueError:
        rate_limit = 8

    return Settings(
        db_path=db,
        admin_token=(os.environ.get("BHOOMI_ADMIN_TOKEN") or "").strip() or None,
        ip_salt=os.environ.get("BHOOMI_IP_SALT", "change-me"),
        secret_key=secret,
        secret_key_is_ephemeral=ephemeral,
        allowed_origins=tuple(
            o.strip() for o in (os.environ.get("BHOOMI_ALLOWED_ORIGINS") or "").split(",")
            if o.strip()
        ),
        rate_limit_per_hour=max(1, rate_limit),
        cookie_secure=_flag("BHOOMI_COOKIE_SECURE", False),
        seed_demo=_flag("BHOOMI_SEED_DEMO", True),
    )
