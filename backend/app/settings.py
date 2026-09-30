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
UPLOADS_DIR = BACKEND_DIR / "uploads"
PROJECT_DIR = BACKEND_DIR.parent


def _flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _database_url() -> str | None:
    """DATABASE_URL (the name hosts like Render and Neon hand out) or BHOOMI_DATABASE_URL."""
    raw = (os.environ.get("BHOOMI_DATABASE_URL") or os.environ.get("DATABASE_URL") or "").strip()
    return raw or None


@dataclass(frozen=True)
class Settings:
    db_path: Path
    database_url: str | None
    admin_token: str | None
    ip_salt: str
    secret_key: str
    secret_key_is_ephemeral: bool
    allowed_origins: tuple[str, ...]
    rate_limit_per_hour: int
    cookie_secure: bool
    seed_demo: bool
    tile_url: str
    login_limit_per_hour: int
    frame_ancestors: tuple[str, ...]
    photos_in_db: bool
    site_url: str
    tile_attribution: str

    uploads_dir: Path
    templates_dir: Path = TEMPLATES_DIR
    static_dir: Path = STATIC_DIR

    @property
    def db_target(self):
        """What to hand to db.closing_conn: the Postgres URL if set, else the SQLite file."""
        return self.database_url or self.db_path


@lru_cache
def get_settings() -> Settings:
    db = Path(os.environ.get("BHOOMI_DB", "bhoomi.sqlite3"))
    if not db.is_absolute():
        db = BACKEND_DIR / db

    uploads = Path(os.environ.get("BHOOMI_UPLOADS", UPLOADS_DIR))
    if not uploads.is_absolute():
        uploads = BACKEND_DIR / uploads

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
        database_url=_database_url(),
        uploads_dir=uploads,
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
        # Map background. The default is the public OpenStreetMap tile server, which
        # is fine for a pilot but asks heavy sites to use their own provider; point
        # this at MapTiler, Stadia, Mapbox or a self-hosted tile server to scale up.
        site_url=(os.environ.get("BHOOMI_SITE_URL") or "").strip().rstrip("/"),
        # Hosts like Render's free tier wipe the disk on every deploy, so with a hosted
        # database the photographs live in the database too (the disk is a cache).
        photos_in_db=_flag("BHOOMI_PHOTOS_IN_DB", bool(_database_url())),
        login_limit_per_hour=max(3, int(os.environ.get("BHOOMI_LOGIN_LIMIT", "10") or 10)),
        # Sites allowed to embed this one in an iframe (e.g. https://*.streamlit.app).
        # Empty, the default, means nobody: the site cannot be framed.
        frame_ancestors=tuple(o.strip() for o in (os.environ.get("BHOOMI_FRAME_ANCESTORS") or "").split() if o.strip()),
        tile_url=os.environ.get("BHOOMI_TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
        tile_attribution=os.environ.get(
            "BHOOMI_TILE_ATTRIBUTION",
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'),
    )
