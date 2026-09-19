"""Admin pages for whoever is running the pilot."""

from __future__ import annotations

import csv
import io
import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response

from .. import db
from ..deps import conn_dep, require_admin_user
from ..templating import flash, render

router = APIRouter()

COUNT_LABELS = {
    "user": "accounts",
    "listing": "parcels listed",
    "season": "season plans",
    "pledge": "interests registered",
    "inquiry": "messages sent",
    "waitlist": "on the waitlist",
}


@router.get("/admin")
def admin_home(
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_admin_user),
):
    counts = {COUNT_LABELS[k]: v for k, v in db.site_counts(conn).items()}
    return render(
        request,
        "admin.html",
        user=user,
        counts=counts,
        waitlist=db.list_waitlist(conn, limit=200),
        users=db.all_rows(conn, "SELECT * FROM user ORDER BY created_at DESC LIMIT 200"),
        seasons=db.search_seasons(conn, status="", limit=200),
        listings=db.search_listings(conn, status="", limit=200),
    )


@router.post("/admin/waitlist/{entry_id}/delete")
def delete_waitlist_entry(
    entry_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_admin_user),
):
    db.delete_waitlist_entry(conn, entry_id)
    conn.commit()
    flash(request, "Deleted. Nothing of theirs is kept.")
    return RedirectResponse("/admin", status_code=303)


@router.get("/admin/waitlist.csv")
def waitlist_csv(
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_admin_user),
) -> Response:
    rows = db.list_waitlist(conn, limit=10000)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["name", "phone", "role", "district_state", "created_at", "updated_at"])
    for r in rows:
        writer.writerow([r["name"], r["phone"], r["role"], r["place"],
                         r["created_at"], r["updated_at"]])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="bhoomi-waitlist.csv"'},
    )
