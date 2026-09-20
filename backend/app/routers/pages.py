"""The pages that are mostly words: home, how it works, the fine print."""

from __future__ import annotations

import sqlite3
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from .. import db
from ..deps import conn_dep
from ..i18n import COOKIE, LANGS
from ..security import current_user
from ..templating import render

router = APIRouter()


@router.get("/")
def home(request: Request, conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user)):
    by_kind = {k: db.search_projects(conn, kind=k, status="open", limit=2) for k in db.KINDS}
    listings = db.search_listings(conn, status="open", limit=2)

    # One of each kind before a second of any, so a busy kind cannot crowd the
    # others off the front page.
    firsts = [rows[0] for rows in by_kind.values() if rows]
    seconds = [rows[1] for rows in by_kind.values() if len(rows) > 1]
    projects = (firsts + seconds)[:3]
    return render(
        request, "home.html", user=user,
        projects=projects,
        project_covers=db.cover_photos(conn, "project", [p["id"] for p in projects]),
        listings=listings,
        covers=db.cover_photos(conn, "listing", [l["id"] for l in listings]),
        counts={
            **{k: len(db.search_projects(conn, kind=k, status="open", limit=99))
               for k in db.KINDS},
            "land": len(db.search_listings(conn, status="open", limit=99)),
        },
    )


@router.get("/how-it-works")
def how_it_works(request: Request, user=Depends(current_user)):
    return render(request, "how_it_works.html", user=user)


@router.get("/fine-print")
def fine_print(request: Request, user=Depends(current_user)):
    return render(request, "fine_print.html", user=user)


@router.get("/lang/{code}")
def set_language(code: str, request: Request, next: str = "/"):
    """Remember a language choice and go back to the page they were reading."""
    target = next if next.startswith("/") and not next.startswith("//") else "/"
    # Drop any ?lang= already on that URL so the cookie is the single source.
    parsed = urlparse(target)
    query = "&".join(p for p in parsed.query.split("&") if p and not p.startswith("lang="))
    clean = parsed.path + (f"?{query}" if query else "")

    response = RedirectResponse(clean, status_code=303)
    if code in LANGS:
        response.set_cookie(
            COOKIE, code, max_age=60 * 60 * 24 * 365,
            samesite="lax", httponly=False, path="/",
        )
    return response
