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
