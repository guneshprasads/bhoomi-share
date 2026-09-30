"""The JSON API: the waitlist the landing page posts to, and a token-guarded read.

Kept separate from the HTML pages so scripts and the page can use it without a
session cookie.
"""

from __future__ import annotations

import csv
import io
import secrets
import sqlite3

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import Response

from .. import db, simulator
from ..deps import conn_dep
from ..schemas import ErrorOut, Role, WaitlistEntry, WaitlistIn, WaitlistOut, WaitlistPage
from ..security import settings_dep
from ..settings import Settings

router = APIRouter(prefix="/api")

NEXT_STEP = {
    Role.investor: (
        "We will send you the season plans that are open, once counsel has signed "
        "off on the structure."
    ),
    Role.grower: (
        "We will ask you for the parcel, the crop plan, and what a season of inputs "
        "actually costs you."
    ),
    Role.landowner: (
        "We will send you the licence we drafted for your state, so you can read it "
        "before deciding anything."
    ),
    Role.farmer: "We will tell you what is listed in your district, and on what terms.",
}


def require_admin(
    x_admin_token: str | None = Header(default=None),
    settings: Settings = Depends(settings_dep),
) -> None:
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="No admin token is configured on this server.")
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail="Bad or missing admin token.")


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/health")
def health(settings: Settings = Depends(settings_dep)) -> dict[str, object]:
    return {"ok": True, "admin_configured": bool(settings.admin_token)}


@router.get("/simulate/{kind}", responses={422: {"model": ErrorOut}})
def simulate(kind: str, request: Request) -> dict[str, object]:
    """Run one of the earnings calculators. Every query parameter is a number the
    person chose; nothing is stored."""
    params = {k: v for k, v in request.query_params.items()}
    try:
        return simulator.run(kind, params)
    except simulator.SimulationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.post(
    "/waitlist",
    response_model=WaitlistOut,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorOut}, 429: {"model": ErrorOut}},
)
def join_waitlist(
    payload: WaitlistIn,
    request: Request,
    conn: sqlite3.Connection = Depends(conn_dep),
    settings: Settings = Depends(settings_dep),
) -> WaitlistOut:
    if payload.company:
        # Honeypot tripped. Say nothing useful, store nothing.
        return WaitlistOut(status="ignored", message="Thanks — we have your details.")

    ip_hash = db.hash_ip(client_ip(request), settings.ip_salt)
    if db.recent_submission_count(conn, ip_hash) >= settings.rate_limit_per_hour:
        raise HTTPException(
            status_code=429,
            detail="That is a lot of submissions from one connection. Try again in an hour.",
        )

    result, _row = db.upsert_waitlist(
        conn, name=payload.name, phone=payload.phone,
        role=payload.role.value, place=payload.place,
    )
    db.log_submission(conn, ip_hash)
    conn.commit()

    first_name = payload.name.split(" ")[0]
    if result == "updated":
        message = (f"{first_name}, we already had that number — it now says "
                   f"{payload.role.value.lower()} in {payload.place}.")
    else:
        message = (f"{first_name}, you are on the list as a {payload.role.value.lower()} "
                   f"in {payload.place}. {NEXT_STEP[payload.role]}")
    return WaitlistOut(status=result, message=message)


@router.get("/admin/waitlist", response_model=WaitlistPage, dependencies=[Depends(require_admin)])
def read_waitlist(
    role: Role | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    conn: sqlite3.Connection = Depends(conn_dep),
) -> WaitlistPage:
    rows = db.list_waitlist(conn, role=role.value if role else None, limit=limit, offset=offset)
    by_role = db.count_by_role(conn)
    return WaitlistPage(
        total=sum(by_role.values()),
        by_role=by_role,
        entries=[WaitlistEntry(**dict(r)) for r in rows],
    )


@router.get("/admin/waitlist.csv", dependencies=[Depends(require_admin)])
def read_waitlist_csv(conn: sqlite3.Connection = Depends(conn_dep)) -> Response:
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


@router.delete(
    "/admin/waitlist/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def remove_entry(entry_id: int, conn: sqlite3.Connection = Depends(conn_dep)) -> Response:
    """For when someone asks to be taken off the list. They will."""
    if not db.delete_waitlist_entry(conn, entry_id):
        raise HTTPException(status_code=404, detail="No entry with that id.")
    conn.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/listings")
def api_listings(
    district: str = "",
    conn: sqlite3.Connection = Depends(conn_dep),
) -> dict[str, object]:
    rows = db.search_listings(conn, district=district)
    return {"count": len(rows), "listings": [dict(r) for r in rows]}


@router.get("/projects")
def api_projects(
    kind: str = "",
    district: str = "",
    query: str = "",
    conn: sqlite3.Connection = Depends(conn_dep),
) -> dict[str, object]:
    rows = db.search_projects(conn, kind=kind, district=district, query=query)
    return {"count": len(rows), "projects": [dict(r) for r in rows]}


@router.get("/districts")
def api_districts() -> dict[str, object]:
    from ..karnataka import DIVISIONS, STATE
    return {"state": STATE,
            "divisions": {k: list(v) for k, v in DIVISIONS.items()}}


# --------------------------------------------------------------------------- #
# ledger and money-at-risk (stateless: the page keeps the ledger, the server does the maths)
# --------------------------------------------------------------------------- #

from fastapi import Body  # noqa: E402

from .. import example, ledger, risk  # noqa: E402


def _ledger_payload(plans: list[dict], issues: list[str]) -> dict:
    return {
        "plans": plans, "issues": issues,
        "checks": ledger.check_holding(plans),
        "costs": ledger.cost_by_category(plans),
    }


@router.get("/ledger/example")
def ledger_example() -> dict:
    plans = ledger.example_plans()
    return {
        "name": example.HOLDING_NAME, "note": example.HOLDING_NOTE,
        "csv": ledger.to_csv(plans), "settled": example.SETTLED,
        "assumptions": example.DEFAULT_ASSUMPTIONS,
        "fixes": {k: {kk: vv for kk, vv in v.items() if kk != "kinds"} | {"kinds": list(v["kinds"])}
                  for k, v in risk.FIX_CATALOG.items()},
        **_ledger_payload(plans, []),
    }


@router.post("/ledger/import", responses={422: {"model": ErrorOut}})
def ledger_import(body: dict = Body(...)) -> dict:
    try:
        parsed = ledger.parse_csv(str(body.get("csv", "")))
    except ledger.LedgerError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return _ledger_payload(parsed["plans"], parsed["issues"])


def _plan_from(body: dict) -> dict:
    plan = body.get("plan")
    if not isinstance(plan, dict) or "id" not in plan:
        raise HTTPException(status_code=422, detail="Send the plan from the ledger as {\"plan\": {...}}.")
    plan = dict(plan)
    plan["costs"] = [tuple(c) for c in plan.get("costs", [])]
    plan["history"] = [tuple(h) for h in plan.get("history", [])]
    plan.setdefault("kind", "crop")
    return plan


@router.post("/risk", responses={422: {"model": ErrorOut}})
def risk_one(body: dict = Body(...)) -> dict:
    try:
        return risk.assess(_plan_from(body), body.get("assumptions"), body.get("fixes"), int(body.get("runs", risk.RUNS)))
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.post("/holding", responses={422: {"model": ErrorOut}})
def risk_holding(body: dict = Body(...)) -> dict:
    plans = body.get("plans")
    if not isinstance(plans, list) or not plans or len(plans) > ledger.MAX_PLANS:
        raise HTTPException(status_code=422, detail=f"Send between 1 and {ledger.MAX_PLANS} plans.")
    try:
        prepared = [_plan_from({"plan": p}) for p in plans]
        return risk.holding(prepared, body.get("assumptions"))
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
