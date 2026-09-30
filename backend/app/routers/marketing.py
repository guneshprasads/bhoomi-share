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
