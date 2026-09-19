"""The signed-in home page: your land, your plans, and who is asking."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from .. import db
from ..deps import conn_dep, require_user
from ..templating import flash, render

router = APIRouter()


@router.get("/dashboard")
def dashboard(
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    user_id = int(user["id"])
    pledges = db.pledges_by_investor(conn, user_id)
    return render(
        request,
        "dashboard.html",
        user=user,
        listings=db.listings_for_owner(conn, user_id),
        inquiries=db.inquiries_for_owner(conn, user_id),
        seasons=db.seasons_for_grower(conn, user_id),
        pledges=pledges,
        pledged_total=sum(p["amount"] for p in pledges),
        sent_inquiries=db.inquiries_by_sender(conn, user_id),
    )


@router.post("/dashboard/inquiries/{inquiry_id}/close")
def close_inquiry(
    inquiry_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    if db.set_inquiry_status(conn, inquiry_id, int(user["id"]), "closed"):
        conn.commit()
        flash(request, "Marked handled.")
    else:
        flash(request, "That message is not on one of your parcels.", "bad")
    return RedirectResponse("/dashboard", status_code=303)
