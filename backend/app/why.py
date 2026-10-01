"""Numbers for the /why page, computed from the public data in static/data/why.json.

Nothing on that page is typed in by hand: every figure is derived here from the
file that scripts/build_why_data.py fetched from the World Bank and FAO, so the
text and the charts cannot disagree with their sources.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent.parent / "static" / "data" / "why.json"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _label(period: str) -> str:
    y, m = period.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


@lru_cache
def load() -> dict[str, Any]:
    return json.loads(DATA.read_text())


def numbers() -> dict[str, Any]:
    d = load()
    food = d["food_inflation_monthly"]
    hi = max(food, key=lambda x: x[1])
    lo = min(food, key=lambda x: x[1])
    by_year: dict[str, list[float]] = {}
    for p, v in food:
        by_year.setdefault(p[:4], []).append(v)
    yearly = {y: sum(v) / len(v) for y, v in by_year.items() if len(v) == 12}
    top_year = max(yearly, key=yearly.get)
    low_year = min(yearly, key=yearly.get)

    ann = d["annual"]
    first, last = ann[0], ann[-1]
    return {
        "retrieved": d["retrieved"],
        "sources": d["sources"],
        "food_first": food[0][0], "food_last": food[-1][0], "food_last_label": _label(food[-1][0]),
        "peak_val": round(hi[1], 1), "peak_label": _label(hi[0]),
        "low_val": round(lo[1], 1), "low_label": _label(lo[0]),
        "swing": round(hi[1] - lo[1], 1),
        "top_year": top_year, "top_year_avg": round(yearly[top_year], 1),
        "low_year": low_year, "low_year_avg": round(yearly[low_year], 1),
        "months_negative": sum(1 for _, v in food if v < 0),
        "months_above_10": sum(1 for _, v in food if v >= 10),
        "months_total": len(food),
        "emp_first": round(first["agri_employment"], 1), "emp_last": round(last["agri_employment"], 1),
        "gdp_first": round(first["agri_gdp_share"], 1), "gdp_last": round(last["agri_gdp_share"], 1),
        "year_first": first["year"], "year_last": last["year"],
        "ratio_last": round(last["agri_employment"] / last["agri_gdp_share"], 1),
    }
