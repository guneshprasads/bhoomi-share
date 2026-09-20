"""The signed-in home page: your land, your plans, and who is asking."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse

from .. import db, tour
from ..deps import conn_dep, require_user
from ..templating import current_lang, flash, render

router = APIRouter()


@router.get("/dashboard")
def dashboard(
    request: Request,
    tour_replay: int = Query(default=0, alias="tour"),
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    user_id = int(user["id"])
    pledges = db.pledges_by_investor(conn, user_id)
    show_tour = bool(tour_replay) or not user["tour_done"]
    return render(
        request,
        "dashboard.html",
        user=user,
        listings=db.listings_for_owner(conn, user_id),
        inquiries=db.inquiries_for_owner(conn, user_id),
        projects=db.projects_for_owner(conn, user_id),
        pledges=pledges,
        pledged_total=sum(p["amount"] for p in pledges),
        sent_inquiries=db.inquiries_by_sender(conn, user_id),
        show_tour=show_tour,
        tour=tour.payload(current_lang(request)),
    )


@router.post("/dashboard/tour/done")
def finish_tour(
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    """Called by the tour when it is finished or skipped.

    On the user row rather than in the browser, so it does not come back on a
    second device and does not vanish when someone clears their browser.
    """
    db.mark_tour_done(conn, int(user["id"]))
    conn.commit()
    return {"ok": True}


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
