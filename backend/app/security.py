"""Passwords and sessions.

scrypt from the standard library, so there is nothing to compile and no extra
dependency to keep patched. Sessions are a signed cookie holding a user id.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from typing import Any

from fastapi import Depends, Request

from . import db
from .settings import Settings, get_settings

SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
SESSION_KEY = "uid"

ROLES = ("investor", "grower", "landowner", "farmer")
ROLE_LABELS = {
    "investor": "Investor",
    "grower": "Grower",
    "landowner": "Landowner",
    "farmer": "Farmer",
}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, key_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        key = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(key.hex(), key_hex)


def settings_dep() -> Settings:
    return get_settings()


def login_session(request: Request, user_id: int) -> None:
    request.session[SESSION_KEY] = user_id


def logout_session(request: Request) -> None:
    request.session.clear()


def current_user(
    request: Request, settings: Settings = Depends(settings_dep)
) -> sqlite3.Row | None:
    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        return None
    with db.closing_conn(settings.db_path) as conn:
        user = db.user_by_id(conn, int(user_id))
    if user is None:
        request.session.clear()
    return user


def has_role(user: Any, role: str) -> bool:
    if user is None:
        return False
    return role in {r.strip() for r in (user["roles"] or "").split(",") if r.strip()}


def role_list(user: Any) -> list[str]:
    if user is None:
        return []
    return [r.strip() for r in (user["roles"] or "").split(",") if r.strip()]
