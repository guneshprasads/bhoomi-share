"""The pages that are only words: home, how it works, the fine print."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request

from .. import db
from ..deps import conn_dep
from ..security import current_user
from ..templating import render

router = APIRouter()


@router.get("/")
def home(request: Request, conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user)):
    return render(
        request,
        "home.html",
        user=user,
        open_seasons=db.search_seasons(conn, status="open", limit=3),
        recent_listings=db.search_listings(conn, status="open", limit=3),
    )


@router.get("/how-it-works")
def how_it_works(request: Request, user=Depends(current_user)):
    return render(request, "how_it_works.html", user=user)


@router.get("/fine-print")
def fine_print(request: Request, user=Depends(current_user)):
    return render(request, "fine_print.html", user=user)
