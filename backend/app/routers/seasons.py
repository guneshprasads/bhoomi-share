"""Season plans: browse, read, register interest, and manage your own."""

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
    ("open", "Open — looking for capital"),
    ("funded", "Funded — capital in place"),
    ("growing", "Growing"),
    ("sold", "Sold — proceeds split"),
    ("draft", "Draft — not shown to anyone"),
    ("closed", "Closed"),
]
STATUS_VALUES = {s for s, _ in STATUSES}

STAGES = [
    ("open", "Open for funding"),
    ("growing", "Growing"),
    ("sold", "Sold"),
    ("", "Any stage"),
]

EMPTY = {
    "parcel_label": "", "survey_no": "", "district": "", "state": "", "acres": "",
    "crop": "", "season_label": "", "sowing_window": "", "input_budget": "",
    "expected_quintals": "", "expected_price": "", "investor_pct": 70,
    "grower_pct": 30, "plan_note": "", "status": "open",
}


def _season_form(data: dict) -> dict:
    investor_pct = int(data.get("investor_pct") or 70)
    investor_pct = max(1, min(99, investor_pct))
    return {
        "parcel_label": (data.get("parcel_label") or "").strip(),
        "survey_no": (data.get("survey_no") or "").strip(),
        "district": (data.get("district") or "").strip(),
        "state": (data.get("state") or "").strip(),
        "acres": float(data.get("acres") or 0),
        "crop": (data.get("crop") or "").strip(),
        "season_label": (data.get("season_label") or "").strip(),
        "sowing_window": (data.get("sowing_window") or "").strip(),
        "input_budget": int(data.get("input_budget") or 0),
        "expected_quintals": float(data.get("expected_quintals") or 0),
        "expected_price": int(data.get("expected_price") or 0),
        "investor_pct": investor_pct,
        "grower_pct": 100 - investor_pct,
        "plan_note": (data.get("plan_note") or "").strip(),
        "status": data.get("status") if data.get("status") in STATUS_VALUES else "open",
    }


# --------------------------------------------------------------------------- #
# public
# --------------------------------------------------------------------------- #

@router.get("/seasons")
def seasons_index(
    request: Request,
    district: str = "",
    crop: str = "",
    status: str = "open",
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(current_user),
):
    if status not in STATUS_VALUES:
        status = ""
    q = {"district": district.strip(), "crop": crop.strip(), "status": status}
    q["any"] = bool(q["district"] or q["crop"] or status != "open")

    seasons = db.search_seasons(conn, district=q["district"], crop=q["crop"], status=status)
    return render(request, "seasons.html", user=user, seasons=seasons, q=q, stages=STAGES)


@router.get("/seasons/{season_id}")
def season_detail(
    season_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(current_user),
):
    season = db.season_by_id(conn, season_id)
    if season is None or (season["status"] == "draft" and
                          not (user and user["id"] == season["grower_id"])):
        raise NotFound("There is no plan here.")

    is_grower = bool(user and user["id"] == season["grower_id"])
    expected_sale = int(round(season["expected_quintals"] * season["expected_price"]))
    net = expected_sale - season["input_budget"]

    return render(
        request, "season_detail.html", user=user, season=season,
        expected_sale=expected_sale,
        net=net,
        investor_cut=int(round(net * season["investor_pct"] / 100)) if net > 0 else 0,
        grower_cut=int(round(net * season["grower_pct"] / 100)) if net > 0 else 0,
        updates=db.updates_for_season(conn, season_id),
        pledges=db.pledges_for_season(conn, season_id) if is_grower else [],
        my_pledge=db.pledge_for(conn, season_id, int(user["id"])) if user and not is_grower else None,
        is_grower=is_grower,
    )


@router.post("/seasons/{season_id}/pledge")
def pledge(
    season_id: int,
    request: Request,
    amount: str = Form(...),
    note: str = Form(""),
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    season = db.season_by_id(conn, season_id)
    if season is None:
        raise NotFound("There is no plan here.")
    if season["grower_id"] == user["id"]:
        flash(request, "That is your own plan.", "bad")
        return RedirectResponse(f"/seasons/{season_id}", status_code=303)

    try:
        value = int(float(amount))
    except ValueError:
        value = 0
    if value < 1000:
        flash(request, "Put in a number — at least ₹1,000 — so the grower knows what you mean.", "bad")
        return RedirectResponse(f"/seasons/{season_id}", status_code=303)

    db.upsert_pledge(conn, season_id, int(user["id"]), value, note.strip())
    conn.commit()
    flash(request, "Interest recorded. No money has moved and nothing is binding — if a pool opens for this plan, we come back to you with the deed.")
    return RedirectResponse(f"/seasons/{season_id}", status_code=303)


@router.post("/seasons/{season_id}/pledge/withdraw")
def withdraw(
    season_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    db.withdraw_pledge(conn, season_id, int(user["id"]))
    conn.commit()
    flash(request, "Withdrawn. The grower will see it is gone.")
    return RedirectResponse(f"/seasons/{season_id}", status_code=303)


@router.post("/seasons/{season_id}/updates")
def post_update(
    season_id: int,
    request: Request,
    body: str = Form(...),
    spend: str = Form(""),
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    season = db.season_by_id(conn, season_id)
    if season is None:
        raise NotFound("There is no plan here.")
    if season["grower_id"] != user["id"] and not user["is_admin"]:
        raise Forbidden("Only the grower posts to this log.")

    text = body.strip()
    if len(text) < 5:
        flash(request, "Write what actually happened, even if it is one line.", "bad")
        return RedirectResponse(f"/seasons/{season_id}", status_code=303)

    try:
        spent = int(float(spend)) if spend.strip() else None
    except ValueError:
        spent = None

    db.add_season_update(conn, season_id, text, spent)
    conn.commit()
    flash(request, "Posted to the season log.")
    return RedirectResponse(f"/seasons/{season_id}", status_code=303)


# --------------------------------------------------------------------------- #
# grower
# --------------------------------------------------------------------------- #

@router.get("/dashboard/seasons/new")
def new_season_form(request: Request, user=Depends(require_user)):
    prefill = dict(EMPTY, district=user["district"], state=user["state"])
    return render(request, "season_form.html", user=user, f=prefill, editing=False,
                  error=None, action="/dashboard/seasons/new", statuses=STATUSES)


@router.post("/dashboard/seasons/new")
async def create_season(
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    raw = dict(await request.form())
    try:
        data = _season_form(raw)
    except ValueError:
        return render(request, "season_form.html", user=user, f=dict(EMPTY, **raw),
                      editing=False, error="The budget, yield, price and acreage all have to be numbers.",
                      action="/dashboard/seasons/new", statuses=STATUSES)

    if not data["parcel_label"] or not data["crop"] or data["acres"] <= 0 or data["input_budget"] <= 0:
        return render(request, "season_form.html", user=user, f=dict(EMPTY, **raw),
                      editing=False,
                      error="A plan needs a parcel, a crop, an acreage and an input budget.",
                      action="/dashboard/seasons/new", statuses=STATUSES)

    season_id = db.create_season(conn, int(user["id"]), data)
    conn.commit()
    flash(request, "Plan posted. People can register interest against it; that is not a fundraise.")
    return RedirectResponse(f"/seasons/{season_id}", status_code=303)


def _own_season(conn: sqlite3.Connection, season_id: int, user) -> sqlite3.Row:
    season = db.season_by_id(conn, season_id)
    if season is None:
        raise NotFound("There is no plan here.")
    if season["grower_id"] != user["id"] and not user["is_admin"]:
        raise Forbidden("That plan belongs to another grower.")
    return season


@router.get("/dashboard/seasons/{season_id}/edit")
def edit_season_form(
    season_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    season = _own_season(conn, season_id, user)
    f = {k: (season[k] if season[k] is not None else "") for k in EMPTY}
    return render(request, "season_form.html", user=user, f=f, editing=True, error=None,
                  action=f"/dashboard/seasons/{season_id}/edit", statuses=STATUSES)


@router.post("/dashboard/seasons/{season_id}/edit")
async def save_season(
    season_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    _own_season(conn, season_id, user)
    raw = dict(await request.form())
    try:
        data = _season_form(raw)
    except ValueError:
        return render(request, "season_form.html", user=user, f=dict(EMPTY, **raw),
                      editing=True, error="The budget, yield, price and acreage all have to be numbers.",
                      action=f"/dashboard/seasons/{season_id}/edit", statuses=STATUSES)

    db.update_season(conn, season_id, data)
    conn.commit()
    flash(request, "Plan updated. Anyone who registered interest can see the change.")
    return RedirectResponse(f"/seasons/{season_id}", status_code=303)


@router.post("/dashboard/seasons/{season_id}/delete")
def remove_season(
    season_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    user=Depends(require_user),
):
    _own_season(conn, season_id, user)
    db.delete_season(conn, season_id)
    conn.commit()
    flash(request, "Plan removed, along with the interest registered against it.")
    return RedirectResponse("/dashboard", status_code=303)
