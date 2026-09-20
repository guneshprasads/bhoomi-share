"""Funded projects: a crop season, a livestock unit, or a big parcel in shares.

All four share an owner, a parcel, a budget, a split and a set of photographs,
so they share a table, a card, a form and a detail page. What differs is a
handful of fields and, for shares, the arithmetic of units.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from starlette.datastructures import UploadFile

from .. import db
from ..deps import Forbidden, NotFound, conn_dep
from ..karnataka import normalise as normalise_district
from ..photos import MAX_PHOTOS, PhotoError, remove_file, save_upload
from ..security import current_user, settings_dep
from ..settings import Settings
from ..templating import flash, render
from ..deps import require_user

router = APIRouter()

KIND_LABELS = {
    "crop": "Crop plan",
    "livestock": "Livestock unit",
    "space": "Small space",
    "shares": "Land shares",
}

KIND_PATHS = {"crop": "/seasons", "livestock": "/livestock", "space": "/spaces",
              "shares": "/shares"}

STATUSES = [
    ("open", "Open — looking for capital"),
    ("funded", "Funded — capital in place"),
    ("growing", "Under way"),
    ("sold", "Sold — proceeds split"),
    ("draft", "Draft — not shown to anyone"),
    ("closed", "Closed"),
]
STATUS_VALUES = {s for s, _ in STATUSES}

STAGES = [("open", "stage.open"), ("growing", "stage.growing"),
          ("sold", "stage.sold"), ("", "stage.any")]

EMPTY: dict[str, Any] = {
    "kind": "crop", "title": "", "parcel_label": "", "survey_no": "", "district": "",
    "taluk": "", "acres": "", "budget": "", "expected_revenue": "", "investor_pct": 70,
    "grower_pct": 30, "plan_note": "", "status": "open",
    "crop": "", "season_label": "", "sowing_window": "", "expected_quintals": "",
    "expected_price": "",
    "animal": "", "herd_size": "", "cycle_months": "", "shed": "", "water": "", "fodder": "",
    "activity": "", "area_sqft": "",
    "unit_price": "", "total_units": "", "max_investors": db.DEFAULT_MAX_INVESTORS,
}


# --------------------------------------------------------------------------- #
# form handling
# --------------------------------------------------------------------------- #

def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def project_form(data: dict[str, Any]) -> dict[str, Any]:
    """Shape a posted form into the columns the table expects."""
    kind = data.get("kind") if data.get("kind") in db.KINDS else "crop"
    investor_pct = max(1, min(99, _int(data.get("investor_pct"), 70)))

    out: dict[str, Any] = {
        "kind": kind,
        "title": (data.get("title") or "").strip(),
        "parcel_label": (data.get("parcel_label") or "").strip(),
        "survey_no": (data.get("survey_no") or "").strip(),
        "district": normalise_district(data.get("district")) or "",
        "taluk": (data.get("taluk") or "").strip(),
        "acres": _float(data.get("acres")),
        "budget": _int(data.get("budget")),
        "investor_pct": investor_pct,
        "grower_pct": 100 - investor_pct,
        "plan_note": (data.get("plan_note") or "").strip(),
        "status": data.get("status") if data.get("status") in STATUS_VALUES else "open",
        # kind-specific, defaulted so every column has a value
        "crop": "", "season_label": "", "sowing_window": "",
        "expected_quintals": 0.0, "expected_price": 0,
        "animal": "", "herd_size": 0, "cycle_months": 0, "shed": "", "water": "", "fodder": "",
        "activity": "", "area_sqft": 0,
        "unit_price": 0, "total_units": 0, "max_investors": db.DEFAULT_MAX_INVESTORS,
    }

    if kind == "crop":
        out["crop"] = (data.get("crop") or "").strip()
        out["season_label"] = (data.get("season_label") or "").strip()
        out["sowing_window"] = (data.get("sowing_window") or "").strip()
        out["expected_quintals"] = _float(data.get("expected_quintals"))
        out["expected_price"] = _int(data.get("expected_price"))
        # Revenue is derived here rather than asked for twice.
        out["expected_revenue"] = int(round(out["expected_quintals"] * out["expected_price"]))
    elif kind == "livestock":
        out["animal"] = (data.get("animal") or "").strip()
        out["herd_size"] = _int(data.get("herd_size"))
        out["cycle_months"] = _int(data.get("cycle_months"))
        out["shed"] = (data.get("shed") or "").strip()
        out["water"] = (data.get("water") or "").strip()
        out["fodder"] = (data.get("fodder") or "").strip()
        out["expected_revenue"] = _int(data.get("expected_revenue"))
    elif kind == "space":
        # The space fields have their own names (space_*) because `shed`, `water`
        # and `cycle_months` already belong to the livestock fieldset on the same
        # form, and two inputs with one name would overwrite each other.
        out["activity"] = (data.get("activity") or "").strip()
        out["area_sqft"] = _int(data.get("area_sqft"))
        out["shed"] = (data.get("space_structure") or "").strip()
        out["water"] = (data.get("space_water") or "").strip()
        out["cycle_months"] = _int(data.get("space_months"))
        out["expected_revenue"] = _int(data.get("expected_revenue"))
        # Everything else on the site measures land in acres, so keep that column
        # honest rather than special-casing square feet in every query.
        out["acres"] = round(out["area_sqft"] / db.SQFT_PER_ACRE, 4)
    else:  # shares
        out["unit_price"] = _int(data.get("unit_price"))
        out["max_investors"] = max(2, min(200, _int(data.get("max_investors"),
                                                    db.DEFAULT_MAX_INVESTORS)))
        out["expected_revenue"] = _int(data.get("expected_revenue"))
        # Units follow from the budget: no second number to keep in step.
        out["total_units"] = (out["budget"] // out["unit_price"]) if out["unit_price"] else 0

    return out


def validate(data: dict[str, Any]) -> str | None:
    if not data["title"]:
        return "Give the plan a name people will recognise."
    if not data["district"]:
        return "Pick the district the land is in."
    if data["kind"] == "space":
        if data["area_sqft"] <= 0:
            return "How big is the space, in square feet? A 30 by 40 site is 1,200."
        if data["area_sqft"] > db.SMALL_SPACE_MAX_SQFT:
            return ("Small spaces are up to one acre (43,560 sq ft). Anything bigger "
                    "is a farm — post it as a crop plan or as shares.")
    elif data["acres"] <= 0:
        return "How many acres is it?"
    if data["budget"] <= 0:
        return "A plan needs a budget — what the cycle costs to run."

    if data["kind"] == "crop" and not data["crop"]:
        return "Which crop?"
    if data["kind"] == "space" and not data["activity"]:
        return "What will it be used for — mushrooms, vermicompost, microgreens?"
    if data["kind"] == "livestock":
        if not data["animal"]:
            return "Which animal — sheep, goat, dairy cattle or poultry?"
        if data["herd_size"] <= 0:
            return "How many animals?"
    if data["kind"] == "shares":
        if data["acres"] < db.BIG_LAND_ACRES:
            return (f"Shares are for parcels of {db.BIG_LAND_ACRES:g} acres or more. "
                    f"A smaller parcel can still be posted as a crop plan.")
        if data["unit_price"] <= 0:
            return "What is one share worth, in rupees?"
        if data["total_units"] < 2:
            return "That share price gives fewer than two shares. Lower the price per share."
    return None


def save_photos(
    conn: sqlite3.Connection, form: Any, owner_kind: str, owner_id: int, settings: Settings
) -> list[str]:
    """Store whatever images came with the form. Returns human-readable problems."""
    problems: list[str] = []
    uploads = [f for f in form.getlist("photos") if isinstance(f, UploadFile) and f.filename]
    if not uploads:
        return problems

    room = MAX_PHOTOS - db.photo_count(conn, owner_kind, owner_id)
    for upload in uploads:
        if room <= 0:
            problems.append(f"Only {MAX_PHOTOS} photographs per listing; the rest were skipped.")
            break
        data = upload.file.read()
        try:
            path = save_upload(data, upload.content_type or "", upload.filename or "",
                               settings.uploads_dir, owner_kind)
        except PhotoError as exc:
            problems.append(str(exc))
            continue
        db.add_photo(conn, owner_kind, owner_id, path)
        room -= 1
    return problems


# --------------------------------------------------------------------------- #
# browsing
# --------------------------------------------------------------------------- #

def _browse(
    request: Request, conn: sqlite3.Connection, user: Any, kind: str,
    district: str, query: str, status: str, template: str,
):
    if status not in STATUS_VALUES:
        status = ""
    district_clean = normalise_district(district) or ""
    q = {"district": district_clean, "query": query.strip(), "status": status, "kind": kind}
    q["any"] = bool(q["district"] or q["query"] or status != "open")

    projects = db.search_projects(conn, kind=kind, district=q["district"],
                                  query=q["query"], status=status)
    covers = db.cover_photos(conn, "project", [p["id"] for p in projects])
    return render(request, template, user=user, projects=projects, covers=covers,
                  q=q, stages=STAGES, kind_labels=KIND_LABELS, kind_paths=KIND_PATHS,
                  action=KIND_PATHS.get(kind, "/invest"))


@router.get("/invest")
def invest_index(
    request: Request, district: str = "", query: str = "", kind: str = "", status: str = "open",
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user),
):
    return _browse(request, conn, user, kind if kind in db.KINDS else "",
                   district, query, status, "invest.html")


@router.get("/seasons")
def crop_index(
    request: Request, district: str = "", query: str = "", status: str = "open",
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user),
):
    return _browse(request, conn, user, "crop", district, query, status, "seasons.html")


@router.get("/livestock")
def livestock_index(
    request: Request, district: str = "", query: str = "", status: str = "open",
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user),
):
    return _browse(request, conn, user, "livestock", district, query, status, "livestock.html")


@router.get("/spaces")
def spaces_index(
    request: Request, district: str = "", query: str = "", status: str = "open",
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user),
):
    return _browse(request, conn, user, "space", district, query, status, "spaces.html")


@router.get("/shares")
def shares_index(
    request: Request, district: str = "", query: str = "", status: str = "open",
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user),
):
    return _browse(request, conn, user, "shares", district, query, status, "shares.html")


# --------------------------------------------------------------------------- #
# one project
# --------------------------------------------------------------------------- #

def project_maths(project: sqlite3.Row) -> dict[str, Any]:
    """The same split for every kind, plus per-share figures where they apply."""
    revenue = int(project["expected_revenue"])
    net = revenue - int(project["budget"])
    investor_cut = int(round(net * project["investor_pct"] / 100)) if net > 0 else 0
    grower_cut = net - investor_cut if net > 0 else 0

    total_units = int(project["total_units"] or 0)
    units_taken = int(project["units_taken"] or 0)
    per_unit = int(round(investor_cut / total_units)) if total_units else 0

    if project["kind"] == "shares" and total_units:
        pct = units_taken * 100 // total_units
    else:
        pct = (int(project["pledged"]) * 100 // int(project["budget"])) if project["budget"] else 0

    return {
        "revenue": revenue, "net": net, "investor_cut": investor_cut, "grower_cut": grower_cut,
        "per_unit": per_unit, "units_left": max(0, total_units - units_taken),
        "pct": min(100, pct), "seats_left": max(0, int(project["max_investors"] or 0)
                                                - int(project["backers"])),
    }


@router.get("/projects/{project_id}")
def project_detail(
    project_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user),
):
    project = db.project_by_id(conn, project_id)
    if project is None or (project["status"] == "draft" and
                           not (user and user["id"] == project["owner_id"])):
        raise NotFound("There is no plan here.")

    is_owner = bool(user and user["id"] == project["owner_id"])
    return render(
        request, "project_detail.html", user=user, project=project,
        maths=project_maths(project),
        photos=db.photos_for(conn, "project", project_id),
        updates=db.updates_for_project(conn, project_id),
        pledges=db.pledges_for_project(conn, project_id) if is_owner else [],
        my_pledge=db.pledge_for(conn, project_id, int(user["id"])) if user and not is_owner else None,
        is_owner=is_owner, kind_labels=KIND_LABELS, kind_paths=KIND_PATHS,
    )


@router.post("/projects/{project_id}/pledge")
def pledge(
    project_id: int, request: Request,
    amount: str = Form(""), units: str = Form(""), note: str = Form(""),
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(require_user),
):
    project = db.project_by_id(conn, project_id)
    if project is None:
        raise NotFound("There is no plan here.")
    if project["owner_id"] == user["id"]:
        flash(request, "That is your own plan.", "bad")
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    mine = db.pledge_for(conn, project_id, int(user["id"]))
    maths = project_maths(project)

    if project["kind"] == "shares":
        wanted = _int(units)
        if wanted < 1:
            flash(request, "How many shares do you want? At least one.", "bad")
            return RedirectResponse(f"/projects/{project_id}", status_code=303)

        already = int(mine["units"]) if mine else 0
        if wanted - already > maths["units_left"]:
            flash(request, f"Only {maths['units_left']} shares are left in this parcel.", "bad")
            return RedirectResponse(f"/projects/{project_id}", status_code=303)
        if mine is None and maths["seats_left"] <= 0:
            flash(request,
                  "This parcel has taken as many people as it is allowed to. "
                  "The cap is deliberate — see the fine print.", "bad")
            return RedirectResponse(f"/projects/{project_id}", status_code=303)

        value = wanted * int(project["unit_price"])
        db.upsert_pledge(conn, project_id, int(user["id"]), value, note.strip(), units=wanted)
        conn.commit()
        flash(request, f"{wanted} share{'' if wanted == 1 else 's'} noted against this parcel. "
                       "No money has moved and nothing is binding.")
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    value = _int(amount)
    if value < 1000:
        flash(request, "Put in a number — at least ₹1,000 — so the grower knows what you mean.",
              "bad")
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    db.upsert_pledge(conn, project_id, int(user["id"]), value, note.strip())
    conn.commit()
    flash(request, "Interest recorded. No money has moved and nothing is binding — if a pool "
                   "opens for this plan, we come back to you with the deed.")
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@router.post("/projects/{project_id}/pledge/withdraw")
def withdraw(
    project_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(require_user),
):
    db.withdraw_pledge(conn, project_id, int(user["id"]))
    conn.commit()
    flash(request, "Withdrawn. The person running it will see it is gone.")
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@router.post("/projects/{project_id}/updates")
def post_update(
    project_id: int, request: Request,
    body: str = Form(...), spend: str = Form(""),
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(require_user),
):
    project = db.project_by_id(conn, project_id)
    if project is None:
        raise NotFound("There is no plan here.")
    if project["owner_id"] != user["id"] and not user["is_admin"]:
        raise Forbidden("Only the person running this posts to its log.")

    text = body.strip()
    if len(text) < 5:
        flash(request, "Write what actually happened, even if it is one line.", "bad")
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    db.add_project_update(conn, project_id, text, _int(spend) or None)
    conn.commit()
    flash(request, "Posted to the log.")
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


# --------------------------------------------------------------------------- #
# owner: create, edit, photos, delete
# --------------------------------------------------------------------------- #

def _own(conn: sqlite3.Connection, project_id: int, user: Any) -> sqlite3.Row:
    project = db.project_by_id(conn, project_id)
    if project is None:
        raise NotFound("There is no plan here.")
    if project["owner_id"] != user["id"] and not user["is_admin"]:
        raise Forbidden("That plan belongs to someone else.")
    return project


def _form_page(request: Request, user: Any, f: dict, *, editing: bool, action: str,
               error: str | None = None, photos: list | None = None):
    return render(request, "project_form.html", user=user, f=f, editing=editing,
                  error=error, action=action, statuses=STATUSES, animals=db.ANIMALS,
                  kind_labels=KIND_LABELS, photos=photos or [],
                  activities=db.SPACE_ACTIVITIES,
                  max_photos=MAX_PHOTOS, big_land=db.BIG_LAND_ACRES)


@router.get("/dashboard/projects/new")
def new_project_form(request: Request, kind: str = "crop", user=Depends(require_user)):
    prefill = dict(EMPTY, kind=kind if kind in db.KINDS else "crop", district=user["district"],
                   taluk=user["taluk"])
    return _form_page(request, user, prefill, editing=False, action="/dashboard/projects/new")


@router.post("/dashboard/projects/new")
async def create_project(
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
    settings: Settings = Depends(settings_dep),
):
    form = await request.form()
    raw = {k: v for k, v in form.items() if not isinstance(v, UploadFile)}
    data = project_form(raw)

    problem = validate(data)
    if problem:
        return _form_page(request, user, dict(EMPTY, **raw), editing=False,
                          action="/dashboard/projects/new", error=problem)

    project_id = db.create_project(conn, int(user["id"]), data)
    for note in save_photos(conn, form, "project", project_id, settings):
        flash(request, note, "bad")
    conn.commit()
    flash(request, "Posted. People can register interest against it; that is not a fundraise.")
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@router.get("/dashboard/projects/{project_id}/edit")
def edit_project_form(
    project_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep), user=Depends(require_user),
):
    project = _own(conn, project_id, user)
    f = {k: (project[k] if project[k] is not None else "") for k in EMPTY}
    return _form_page(request, user, f, editing=True,
                      action=f"/dashboard/projects/{project_id}/edit",
                      photos=db.photos_for(conn, "project", project_id))


@router.post("/dashboard/projects/{project_id}/edit")
async def save_project(
    project_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
    settings: Settings = Depends(settings_dep),
):
    _own(conn, project_id, user)
    form = await request.form()
    raw = {k: v for k, v in form.items() if not isinstance(v, UploadFile)}
    data = project_form(raw)

    problem = validate(data)
    if problem:
        return _form_page(request, user, dict(EMPTY, **raw), editing=True,
                          action=f"/dashboard/projects/{project_id}/edit", error=problem,
                          photos=db.photos_for(conn, "project", project_id))

    db.update_project(conn, project_id, data)
    for note in save_photos(conn, form, "project", project_id, settings):
        flash(request, note, "bad")
    conn.commit()
    flash(request, "Updated. Anyone who registered interest can see the change.")
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@router.post("/dashboard/projects/{project_id}/photos/{photo_id}/delete")
def delete_project_photo(
    project_id: int, photo_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
    settings: Settings = Depends(settings_dep),
):
    _own(conn, project_id, user)
    photo = db.photo_by_id(conn, photo_id)
    if photo and photo["owner_kind"] == "project" and int(photo["owner_id"]) == project_id:
        db.delete_photo(conn, photo_id)
        conn.commit()
        remove_file(settings.uploads_dir, photo["path"])
        flash(request, "Photograph removed.")
    return RedirectResponse(f"/dashboard/projects/{project_id}/edit", status_code=303)


@router.post("/dashboard/projects/{project_id}/delete")
def remove_project(
    project_id: int, request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
    settings: Settings = Depends(settings_dep),
):
    _own(conn, project_id, user)
    paths = db.delete_photos_for(conn, "project", project_id)
    db.delete_project(conn, project_id)
    conn.commit()
    for path in paths:
        remove_file(settings.uploads_dir, path)
    flash(request, "Removed, along with the interest registered against it.")
    return RedirectResponse("/dashboard", status_code=303)
