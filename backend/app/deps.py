"""Shared dependencies for the HTML pages."""

from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Depends, Request

from . import db
from .security import current_user, settings_dep
from .settings import Settings


class LoginRequired(Exception):
    """Raised by page routes that need an account; handled as a redirect."""

    def __init__(self, next_url: str) -> None:
        self.next_url = next_url


class Forbidden(Exception):
    def __init__(self, message: str = "That is not yours to open.") -> None:
        self.message = message


class NotFound(Exception):
    def __init__(self, message: str = "We could not find that.") -> None:
        self.message = message


def conn_dep(settings: Settings = Depends(settings_dep)) -> Iterator[sqlite3.Connection]:
    with db.closing_conn(settings.db_path) as conn:
        yield conn


def require_user(request: Request, user=Depends(current_user)):
    if user is None:
        raise LoginRequired(request.url.path)
    return user


def require_admin_user(user=Depends(require_user)):
    if not user["is_admin"]:
        raise Forbidden("That part of the site is for the people running the pilot.")
    return user
