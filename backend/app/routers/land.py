"""Land listings: browse, read, ask about, and manage your own."""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from starlette.datastructures import UploadFile

from .. import db
from ..deps import Forbidden, NotFound, conn_dep, require_user
from ..karnataka import normalise as normalise_district
from ..photos import MAX_PHOTOS, remove_file
from ..routers.projects import save_photos
from ..security import current_user, settings_dep
from ..settings import Settings
from ..templating import flash, render

router = APIRouter()

STATUSES = [
    ("open", "Open — farmers can write to me"),
    ("matched", "Matched — in talks with someone"),
    ("draft", "Draft — not shown to anyone"),
    ("closed", "Closed for this year"),
]
STATUS_VALUES = {s for s, _ in STATUSES}

# What people actually grow across Karnataka, for the "can be grown here" picker.
COMMON_CROPS = (
    "Ragi", "Jowar", "Maize", "Paddy", "Tur", "Chana", "Groundnut", "Sunflower",
    "Cotton", "Sugarcane", "Onion", "Chilli", "Areca", "Coconut", "Coffee",
    "Banana", "Mango", "Vegetables", "Fodder",
)

EMPTY = {
    "title": "", "survey_no": "", "district": "", "taluk": "", "acres": "",
    "water_source": "", "water_hours": "", "soil": "", "road_access": "",
    "last_crop": "", "suitable_crops": "", "term_months": 11, "rent_per_acre": "",
    "share_terms": "", "notes": "", "status": "open",
}


def _listing_form(data: dict[str, Any], crops: list[str]) -> dict[str, Any]:
    rent = str(data.get("rent_per_acre") or "").strip()
    try:
        acres = float(data.get("acres") or 0)
    except ValueError:
        acres = 0.0
    try:
        term = int(data.get("term_months") or 11)
    except ValueError:
        term = 11
    return {
        "title": (data.get("title") or "").strip(),
        "survey_no": (data.get("survey_no") or "").strip(),
        "district": normalise_district(data.get("district")) or "",
        "taluk": (data.get("taluk") or "").strip(),
        "acres": acres,
        "water_source": (data.get("water_source") or "").strip(),
        "water_hours": (data.get("water_hours") or "").strip(),
        "soil": (data.get("soil") or "").strip(),
        "road_access": (data.get("road_access") or "").strip(),
        "last_crop": (data.get("last_crop") or "").strip(),
        "suitable_crops": ", ".join(c for c in crops if c in COMMON_CROPS),
        "term_months": term,
        "rent_per_acre": int(rent) if rent.isdigit() else None,
        "share_terms": (data.get("share_terms") or "").strip(),
        "notes": (data.get("notes") or "").strip(),
        "status": data.get("status") if data.get("status") in STATUS_VALUES else "open",
    }


def _form_page(request: Request, user: Any, f: dict, *, editing: bool, action: str,
               error: str | None = None, photos: list | None = None):
    return render(request, "listing_form.html", user=user, f=f, editing=editing, error=error,
                  action=action, statuses=STATUSES, common_crops=COMMON_CROPS,
                  chosen_crops=[c.strip() for c in str(f.get("suitable_crops") or "").split(",") if c.strip()],
                  photos=photos or [], max_photos=MAX_PHOTOS)


# --------------------------------------------------------------------------- #
# public
# --------------------------------------------------------------------------- #

@router.get("/land")
def land_index(
    request: Request,
    district: str = "", min_acres: str = "", max_acres: str = "", water: str = "",
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user),
):
    def num(value: str) -> float | None:
        try:
            return float(value) if value not in ("", None) else None
        except ValueError:
            return None

    q = {
        "district": normalise_district(district) or "",
        "min_acres": num(min_acres),
        "max_acres": num(max_acres),
        "water": bool(water),
    }
    q["any"] = bool(q["district"] or q["min_acres"] or q["max_acres"] or q["water"])

    listings = db.search_listings(
        conn, district=q["district"], min_acres=q["min_acres"],
        max_acres=q["max_acres"], water_only=q["water"],
    )
    covers = db.cover_photos(conn, "listing", [l["id"] for l in listings])
    return render(request, "land.html", user=user, listings=listings, covers=covers, q=q)


@router.get("/land/{listing_id}")
def land_detail(
    listing_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user),
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
                  photos=db.photos_for(conn, "listing", listing_id),
                  crops=[c.strip() for c in (listing["suitable_crops"] or "").split(",") if c.strip()],
                  inquiry_count=inquiry_count)


@router.post("/land/{listing_id}/inquire")
def inquire(
    listing_id: int, request: Request, message: str = Form(...),
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(require_user),
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
    prefill = dict(EMPTY, district=user["district"], taluk=user["taluk"])
    return _form_page(request, user, prefill, editing=False, action="/dashboard/listings/new")


@router.post("/dashboard/listings/new")
async def create_listing(
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
    settings: Settings = Depends(settings_dep),
):
    form = await request.form()
    raw = {k: v for k, v in form.items() if not isinstance(v, UploadFile)}
    data = _listing_form(raw, form.getlist("crops"))

    if not data["title"] or data["acres"] <= 0 or not data["district"]:
        return _form_page(request, user, dict(EMPTY, **raw), editing=False,
                          action="/dashboard/listings/new",
                          error="We need a description, the acreage and the district.")

    listing_id = db.create_listing(conn, int(user["id"]), data)
    for note in save_photos(conn, form, "listing", listing_id, settings):
        flash(request, note, "bad")
    conn.commit()
    flash(request, "Parcel listed. Nothing about this creates a tenancy.")
    return RedirectResponse(f"/land/{listing_id}", status_code=303)


def _own_listing(conn: sqlite3.Connection, listing_id: int, user: Any) -> sqlite3.Row:
    listing = db.listing_by_id(conn, listing_id)
    if listing is None:
        raise NotFound("That parcel is not listed here.")
    if listing["owner_id"] != user["id"] and not user["is_admin"]:
        raise Forbidden("That parcel belongs to someone else.")
    return listing


@router.get("/dashboard/listings/{listing_id}/edit")
def edit_listing_form(
    listing_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(require_user),
):
    listing = _own_listing(conn, listing_id, user)
    f = {k: (listing[k] if listing[k] is not None else "") for k in EMPTY}
    return _form_page(request, user, f, editing=True,
                      action=f"/dashboard/listings/{listing_id}/edit",
                      photos=db.photos_for(conn, "listing", listing_id))


@router.post("/dashboard/listings/{listing_id}/edit")
async def save_listing(
    listing_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
    settings: Settings = Depends(settings_dep),
):
    _own_listing(conn, listing_id, user)
    form = await request.form()
    raw = {k: v for k, v in form.items() if not isinstance(v, UploadFile)}
    data = _listing_form(raw, form.getlist("crops"))

    if not data["title"] or data["acres"] <= 0 or not data["district"]:
        return _form_page(request, user, dict(EMPTY, **raw), editing=True,
                          action=f"/dashboard/listings/{listing_id}/edit",
                          error="We need a description, the acreage and the district.",
                          photos=db.photos_for(conn, "listing", listing_id))

    db.update_listing(conn, listing_id, data)
    for note in save_photos(conn, form, "listing", listing_id, settings):
        flash(request, note, "bad")
    conn.commit()
    flash(request, "Parcel updated.")
    return RedirectResponse(f"/land/{listing_id}", status_code=303)


@router.post("/dashboard/listings/{listing_id}/photos/{photo_id}/delete")
def delete_listing_photo(
    listing_id: int, photo_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
    settings: Settings = Depends(settings_dep),
):
    _own_listing(conn, listing_id, user)
    photo = db.photo_by_id(conn, photo_id)
    if photo and photo["owner_kind"] == "listing" and int(photo["owner_id"]) == listing_id:
        db.delete_photo(conn, photo_id)
        conn.commit()
        remove_file(settings.uploads_dir, photo["path"])
        flash(request, "Photograph removed.")
    return RedirectResponse(f"/dashboard/listings/{listing_id}/edit", status_code=303)


@router.post("/dashboard/listings/{listing_id}/delete")
def remove_listing(
    listing_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
    settings: Settings = Depends(settings_dep),
):
    _own_listing(conn, listing_id, user)
    paths = db.delete_photos_for(conn, "listing", listing_id)
    db.delete_listing(conn, listing_id)
    conn.commit()
    for path in paths:
        remove_file(settings.uploads_dir, path)
    flash(request, "Listing removed, along with the messages about it.")
    return RedirectResponse("/dashboard", status_code=303)
