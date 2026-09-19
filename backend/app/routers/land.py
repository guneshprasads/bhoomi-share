"""Land listings: browse, read, ask about, and manage your own."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from .. import db
from ..deps import Forbidden, NotFound, conn_dep, require_user
from ..security import current_user
from ..templating import flash, render

router = APIRouter()

STATUSES = [
    ("open", "Open — farmers can write to me"),
    ("matched", "Matched — in talks with someone"),
    ("draft", "Draft — not shown to anyone"),
    ("closed", "Closed for this year"),
]
STATUS_VALUES = {s for s, _ in STATUSES}


def _listing_form(data: dict) -> dict:
    """Shape a form post into the columns the table expects."""
    rent = (data.get("rent_per_acre") or "").strip()
    return {
        "title": (data.get("title") or "").strip(),
        "survey_no": (data.get("survey_no") or "").strip(),
        "district": (data.get("district") or "").strip(),
        "state": (data.get("state") or "").strip(),
        "acres": float(data.get("acres") or 0),
        "water_source": (data.get("water_source") or "").strip(),
        "water_hours": (data.get("water_hours") or "").strip(),
        "soil": (data.get("soil") or "").strip(),
        "road_access": (data.get("road_access") or "").strip(),
        "last_crop": (data.get("last_crop") or "").strip(),
        "term_months": int(data.get("term_months") or 11),
        "rent_per_acre": int(rent) if rent else None,
        "share_terms": (data.get("share_terms") or "").strip(),
        "notes": (data.get("notes") or "").strip(),
        "status": data.get("status") if data.get("status") in STATUS_VALUES else "open",
    }


EMPTY = {
    "title": "", "survey_no": "", "district": "", "state": "", "acres": "",
    "water_source": "", "water_hours": "", "soil": "", "road_access": "",
    "last_crop": "", "term_months": 11, "rent_per_acre": "", "share_terms": "",
    "notes": "", "status": "open",
}


# --------------------------------------------------------------------------- #
# public
# --------------------------------------------------------------------------- #

@router.get("/land")
def land_index(
    request: Request,
    district: str = "",
    min_acres: str = "",
    max_acres: str = "",
    water: str = "",
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(current_user),
):
    def num(value: str) -> float | None:
        try:
            return float(value) if value not in ("", None) else None
        except ValueError:
            return None

    q = {
        "district": district.strip(),
        "min_acres": num(min_acres),
        "max_acres": num(max_acres),
        "water": bool(water),
    }
    q["any"] = bool(q["district"] or q["min_acres"] or q["max_acres"] or q["water"])

    listings = db.search_listings(
        conn,
        district=q["district"],
        min_acres=q["min_acres"],
        max_acres=q["max_acres"],
        water_only=q["water"],
    )
    return render(request, "land.html", user=user, listings=listings, q=q)


@router.get("/land/{listing_id}")
def land_detail(
    listing_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(current_user),
):
    listing = db.listing_by_id(conn, listing_id)
    if listing is None or (listing["status"] == "draft" and
                           not (user and user["id"] == listing["owner_id"])):
        raise NotFound("That parcel is not listed here.")

    inquiry_count = len([
        i for i in db.inquiries_for_owner(conn, int(listing["owner_id"]))
        if i["listing_id"] == listing_id
    ])
    return render(request, "listing_detail.html", user=user, listing=listing,
                  inquiry_count=inquiry_count)


@router.post("/land/{listing_id}/inquire")
def inquire(
    listing_id: int,
    request: Request,
    message: str = Form(...),
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    listing = db.listing_by_id(conn, listing_id)
    if listing is None:
        raise NotFound("That parcel is not listed here.")
    if listing["owner_id"] == user["id"]:
        flash(request, "That is your own parcel.", "bad")
        return RedirectResponse(f"/land/{listing_id}", status_code=303)

    body = message.strip()
    if len(body) < 10:
        flash(request, "Write the owner a line or two about what you would do with it.", "bad")
        return RedirectResponse(f"/land/{listing_id}", status_code=303)

    db.create_inquiry(conn, listing_id, int(user["id"]), body)
    conn.commit()
    flash(request, "Sent. The owner has your name, district and phone number — nothing else.")
    return RedirectResponse(f"/land/{listing_id}", status_code=303)


# --------------------------------------------------------------------------- #
# owner
# --------------------------------------------------------------------------- #

@router.get("/dashboard/listings/new")
def new_listing_form(request: Request, user=Depends(require_user)):
    prefill = dict(EMPTY, district=user["district"], state=user["state"])
    return render(request, "listing_form.html", user=user, f=prefill, editing=False,
                  error=None, action="/dashboard/listings/new", statuses=STATUSES)


@router.post("/dashboard/listings/new")
async def create_listing(
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    raw = dict(await request.form())
    try:
        data = _listing_form(raw)
    except ValueError:
        return render(request, "listing_form.html", user=user, f=dict(EMPTY, **raw),
                      editing=False, error="Acreage and rent have to be numbers.",
                      action="/dashboard/listings/new", statuses=STATUSES)

    if not data["title"] or data["acres"] <= 0 or not data["district"]:
        return render(request, "listing_form.html", user=user, f=dict(EMPTY, **raw),
                      editing=False,
                      error="We need at least a description, the acreage and the district.",
                      action="/dashboard/listings/new", statuses=STATUSES)

    listing_id = db.create_listing(conn, int(user["id"]), data)
    conn.commit()
    flash(request, "Parcel listed. Nothing about this creates a tenancy.")
    return RedirectResponse(f"/land/{listing_id}", status_code=303)


def _own_listing(conn: sqlite3.Connection, listing_id: int, user) -> sqlite3.Row:
    listing = db.listing_by_id(conn, listing_id)
    if listing is None:
        raise NotFound("That parcel is not listed here.")
    if listing["owner_id"] != user["id"] and not user["is_admin"]:
        raise Forbidden("That parcel belongs to someone else.")
    return listing


@router.get("/dashboard/listings/{listing_id}/edit")
def edit_listing_form(
    listing_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    listing = _own_listing(conn, listing_id, user)
    f = {k: (listing[k] if listing[k] is not None else "") for k in EMPTY}
    return render(request, "listing_form.html", user=user, f=f, editing=True, error=None,
                  action=f"/dashboard/listings/{listing_id}/edit", statuses=STATUSES)


@router.post("/dashboard/listings/{listing_id}/edit")
async def save_listing(
    listing_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    _own_listing(conn, listing_id, user)
    raw = dict(await request.form())
    try:
        data = _listing_form(raw)
    except ValueError:
        return render(request, "listing_form.html", user=user, f=dict(EMPTY, **raw),
                      editing=True, error="Acreage and rent have to be numbers.",
                      action=f"/dashboard/listings/{listing_id}/edit", statuses=STATUSES)

    db.update_listing(conn, listing_id, data)
    conn.commit()
    flash(request, "Parcel updated.")
    return RedirectResponse(f"/land/{listing_id}", status_code=303)


@router.post("/dashboard/listings/{listing_id}/delete")
def remove_listing(
    listing_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    _own_listing(conn, listing_id, user)
    db.delete_listing(conn, listing_id)
    conn.commit()
    flash(request, "Listing removed, along with the messages about it.")
    return RedirectResponse("/dashboard", status_code=303)
