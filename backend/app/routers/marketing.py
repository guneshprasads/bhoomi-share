"""The pages that explain the idea: ways to earn, the five models, stories,
the district map, FAQ and about. They read the database for live counts but
hold no state of their own."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Request

from .. import db, simulator
from ..deps import conn_dep
from ..security import current_user
from ..templating import render

router = APIRouter()


@router.get("/earn")
def earn(request: Request, conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user)):
    return render(
        request, "earn.html", user=user,
        defaults=simulator.DEFAULTS,
        # First paint for the investor calculator, so the page is useful before
        # any script runs and the numbers match what the API returns.
        sim=simulator.run("crop", simulator.DEFAULTS["crop"]),
    )


# --------------------------------------------------------------------------- #
# the five models
# --------------------------------------------------------------------------- #

from .. import content  # noqa: E402
from ..deps import NotFound  # noqa: E402


@router.get("/models")
def models_index(request: Request, conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user)):
    return render(
        request, "models.html", user=user,
        models=[content.get(s) for s in content.ORDER],
        counts=content.open_counts(conn),
    )


@router.get("/models/{slug}")
def model_detail(slug: str, request: Request, conn: sqlite3.Connection = Depends(conn_dep),
                 user=Depends(current_user)):
    model = content.get(slug)
    if model is None:
        raise NotFound("There is no such model.")
    counts = content.open_counts(conn)
    return render(
        request, "model.html", user=user,
        model=model,
        counts=counts,
        open_count=counts[model["kind"]],
        cost_total=content.cost_total(model),
        sim=content.worked_example(model),
        others=[content.get(s) for s in content.ORDER if s != slug],
    )


@router.get("/stories")
def stories(request: Request, user=Depends(current_user)):
    return render(
        request, "stories.html", user=user,
        stories=[content.story_with_numbers(s) for s in content.STORIES],
    )


@router.get("/karnataka")
def karnataka_map(request: Request, conn: sqlite3.Connection = Depends(conn_dep),
                  user=Depends(current_user)):
    from .. import agri
    from .. import karnataka as k
    from ..settings import get_settings

    plans = {r["district"]: int(r["n"]) for r in db.all_rows(
        conn, "SELECT district, COUNT(*) AS n FROM project WHERE status = 'open' GROUP BY district")}
    parcels = {r["district"]: int(r["n"]) for r in db.all_rows(
        conn, "SELECT district, COUNT(*) AS n FROM listing WHERE status = 'open' GROUP BY district")}

    tiles = []
    for name, (col, row) in k.TILE_POS.items():
        tiles.append({
            "name": name,
            "name_kn": k.DISTRICTS_KN[name],
            "col": col, "row": row,
            "division": k.DIVISION_OF[name],
            "plans": plans.get(name, 0),
            "parcels": parcels.get(name, 0),
            "pilot": name == k.PILOT_DISTRICT,
            **agri.for_map(name),
        })
    settings = get_settings()
    return render(
        request, "karnataka.html", user=user,
        tiles=tiles,
        divisions=k.DIVISIONS,
        notes=k.DIVISION_NOTES,
        tiers=agri.TIERS,
        active=sum(1 for t in tiles if t["plans"] or t["parcels"]),
        total_plans=sum(plans.values()),
        total_parcels=sum(parcels.values()),
        tile_url=settings.tile_url,
        tile_attribution=settings.tile_attribution,
    )


@router.get("/faq")
def faq(request: Request, user=Depends(current_user)):
    import json

    # FAQPage structured data, so the answers can appear in search results. The
    # "</" escape keeps an answer from closing the script tag early.
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in content.faq_flat()
        ],
    }, ensure_ascii=False).replace("</", "<\\/")
    return render(request, "faq.html", user=user, groups=content.FAQ_GROUPS, jsonld=jsonld)


@router.get("/about")
def about(request: Request, conn: sqlite3.Connection = Depends(conn_dep), user=Depends(current_user)):
    return render(request, "about.html", user=user)


@router.get("/ledger")
def ledger_page(request: Request, user=Depends(current_user)):
    return render(request, "ledger.html", user=user)


@router.get("/ledger/risk")
def risk_page(request: Request, user=Depends(current_user)):
    return render(request, "risk.html", user=user)


@router.get("/foresight")
def foresight(request: Request, user=Depends(current_user)):
    return render(request, "foresight.html", user=user, f=content.FORESIGHT)


@router.get("/story")
def story(request: Request, user=Depends(current_user)):
    from .. import simulator

    n = content.product_numbers()
    rent = simulator.landowner(4, 8000, 2)
    farm = simulator.farmer(3, 45000, 22000, 8000)
    return render(
        request, "story.html", user=user,
        holding=n["holding"], totals=n["totals"], flagged=n["flagged"], plans_n=n["plans_n"],
        cut=n["cut"], best=n["best"], rent=rent, farm=farm,
    )
