"""The money maths behind the "ways to earn" page.

One place, so the page, the JSON endpoint and the tests all agree. Nothing here
is a forecast: every function takes the person's own assumptions and shows what
the *agreement's arithmetic* does with them, including a season that fails.

The rule it models is the one the site states everywhere: what the crop or the
animals sell for first repays the costs that were listed in the plan, to whoever
paid them; what is left is split by the agreed percentages. If the sale does not
cover the costs, the funder gets back what there is and the person doing the
work gets nothing for their labour. There is no guaranteed return.
"""

from __future__ import annotations

from typing import Any

# How the expected sale value is stressed. Labels are keys the templates translate.
SCENARIOS: tuple[tuple[str, float], ...] = (
    ("strong", 1.25),
    ("expected", 1.0),
    ("weak", 0.6),
    ("failed", 0.0),
)

MAX_MONEY = 10_00_00_000  # ₹10 crore: beyond this the page is being played with


class SimulationError(ValueError):
    """Raised for inputs that cannot be modelled; the message is shown to people."""


def _money(value: Any, name: str, *, allow_zero: bool = True) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise SimulationError(f"{name} needs to be a number.") from None
    if n != n or n in (float("inf"), float("-inf")):
        raise SimulationError(f"{name} needs to be a number.")
    if n < 0 or (n == 0 and not allow_zero):
        raise SimulationError(f"{name} cannot be {'zero or ' if not allow_zero else ''}negative.")
    if n > MAX_MONEY:
        raise SimulationError(f"{name} is larger than this page can sensibly model.")
    return n


def _pct(value: Any, name: str) -> float:
    n = _money(value, name)
    if n > 100:
        raise SimulationError(f"{name} cannot be more than 100.")
    return n


def _r(n: float) -> int:
    return int(round(n))


# --------------------------------------------------------------------------- #
# funding a plan (crop, livestock, small space, shares)
# --------------------------------------------------------------------------- #

def funded(
    cost: float,
    expected_sale: float,
    investor_pct: float,
    my_fraction: float = 1.0,
) -> dict[str, Any]:
    """What the funder and the grower each take home, for four kinds of season.

    `my_fraction` is the funder's slice of the funding side: 1.0 when one person
    funds the whole plan, 0.125 when they hold 10 of 80 shares.
    """
    cost = _money(cost, "The budget", allow_zero=False)
    expected_sale = _money(expected_sale, "The expected sale")
    investor_pct = _pct(investor_pct, "The investor's share")
    if not 0 < my_fraction <= 1:
        raise SimulationError("Your slice of the funding has to be between 0 and 100 percent.")

    rows = []
    for key, factor in SCENARIOS:
        sale = expected_sale * factor
        repaid = min(sale, cost)           # costs come out first, to the funder
        surplus = max(sale - cost, 0.0)    # what is left is divided
        funder_pool = repaid + surplus * investor_pct / 100
        grower_take = surplus * (100 - investor_pct) / 100

        mine_in = cost * my_fraction
        mine_out = funder_pool * my_fraction
        mine_net = mine_out - mine_in
        rows.append({
            "key": key,
            "sale": _r(sale),
            "costs_repaid": _r(repaid),
            "surplus": _r(surplus),
            "you_put_in": _r(mine_in),
            "you_get_back": _r(mine_out),
            "you_net": _r(mine_net),
            "you_return_pct": round(mine_net / mine_in * 100, 1) if mine_in else 0.0,
            "grower_take": _r(grower_take),
        })

    breakeven = cost  # the sale value at which the funder is made whole
    return {
        "kind": "funded",
        "cost": _r(cost),
        "expected_sale": _r(expected_sale),
        "investor_pct": round(investor_pct, 1),
        "grower_pct": round(100 - investor_pct, 1),
        "my_fraction": round(my_fraction, 4),
        "breakeven_sale": _r(breakeven),
        "breakeven_vs_expected_pct": round(breakeven / expected_sale * 100, 1) if expected_sale else None,
        "scenarios": rows,
    }


def shares(total_units: int, unit_price: float, units_held: int,
           expected_sale: float, investor_pct: float) -> dict[str, Any]:
    try:
        total_units = int(total_units)
        units_held = int(units_held)
    except (TypeError, ValueError):
        raise SimulationError("Shares have to be whole numbers.") from None
    if total_units < 1:
        raise SimulationError("A parcel needs at least one share.")
    if not 1 <= units_held <= total_units:
        raise SimulationError("You cannot hold fewer than one share or more than the parcel has.")
    unit_price = _money(unit_price, "A share's value", allow_zero=False)
    out = funded(total_units * unit_price, expected_sale, investor_pct, units_held / total_units)
    out.update(kind="shares", total_units=total_units, units_held=units_held,
               unit_price=_r(unit_price))
    return out


def small_space(setup: float, batches: int, batch_cost: float, batch_sale: float,
                investor_pct: float) -> dict[str, Any]:
    try:
        batches = int(batches)
    except (TypeError, ValueError):
        raise SimulationError("Batches have to be a whole number.") from None
    if not 1 <= batches <= 60:
        raise SimulationError("A plan covers between 1 and 60 batches.")
    setup = _money(setup, "The setup cost")
    batch_cost = _money(batch_cost, "The cost of a batch")
    batch_sale = _money(batch_sale, "What a batch sells for")
    cost = setup + batches * batch_cost
    out = funded(cost, batches * batch_sale, investor_pct)
    out.update(kind="space", setup=_r(setup), batches=batches,
               batch_cost=_r(batch_cost), batch_sale=_r(batch_sale))
    return out


# --------------------------------------------------------------------------- #
# owning land (licence rent)
# --------------------------------------------------------------------------- #

def landowner(acres: float, rent_per_acre: float, seasons: int,
              own_cost_per_acre: float = 0.0) -> dict[str, Any]:
    acres = _money(acres, "The area", allow_zero=False)
    rent_per_acre = _money(rent_per_acre, "The rent")
    own_cost_per_acre = _money(own_cost_per_acre, "Your yearly upkeep")
    try:
        seasons = int(seasons)
    except (TypeError, ValueError):
        raise SimulationError("Seasons have to be a whole number.") from None
    if not 1 <= seasons <= 3:
        raise SimulationError("A year holds one to three seasons.")

    gross = acres * rent_per_acre * seasons
    upkeep = acres * own_cost_per_acre
    return {
        "kind": "landowner",
        "acres": round(acres, 2),
        "rent_per_acre": _r(rent_per_acre),
        "seasons": seasons,
        "per_season": _r(acres * rent_per_acre),
        "per_year": _r(gross),
        "upkeep": _r(upkeep),
        "net_per_year": _r(gross - upkeep),
        "idle_per_year": 0,
        "note_term": "A licence is a fixed term; this is what one year of it pays if it is renewed.",
    }


# --------------------------------------------------------------------------- #
# working land (what a farmer keeps after rent)
# --------------------------------------------------------------------------- #

def farmer(acres: float, revenue_per_acre: float, inputs_per_acre: float,
           rent_per_acre: float) -> dict[str, Any]:
    acres = _money(acres, "The area", allow_zero=False)
    revenue_per_acre = _money(revenue_per_acre, "Expected revenue")
    inputs_per_acre = _money(inputs_per_acre, "Inputs")
    rent_per_acre = _money(rent_per_acre, "Rent")

    rows = []
    for key, factor in SCENARIOS:
        revenue = revenue_per_acre * factor
        profit_acre = revenue - inputs_per_acre - rent_per_acre
        rows.append({
            "key": key,
            "revenue_per_acre": _r(revenue),
            "profit_per_acre": _r(profit_acre),
            "profit_total": _r(profit_acre * acres),
        })
    cost_acre = inputs_per_acre + rent_per_acre
    return {
        "kind": "farmer",
        "acres": round(acres, 2),
        "cost_per_acre": _r(cost_acre),
        "breakeven_revenue_per_acre": _r(cost_acre),
        "breakeven_vs_expected_pct": (
            round(cost_acre / revenue_per_acre * 100, 1) if revenue_per_acre else None
        ),
        "scenarios": rows,
    }


# --------------------------------------------------------------------------- #
# dispatch for the JSON endpoint
# --------------------------------------------------------------------------- #

def run(kind: str, p: dict[str, Any]) -> dict[str, Any]:
    """`kind` is one of: crop, livestock, space, shares, landowner, farmer."""
    if kind in ("crop", "livestock"):
        return funded(p.get("cost", 0), p.get("sale", 0), p.get("investor_pct", 70))
    if kind == "space":
        return small_space(p.get("setup", 0), p.get("batches", 1), p.get("batch_cost", 0),
                           p.get("batch_sale", 0), p.get("investor_pct", 70))
    if kind == "shares":
        return shares(p.get("total_units", 0), p.get("unit_price", 0), p.get("units_held", 1),
                      p.get("sale", 0), p.get("investor_pct", 70))
    if kind == "landowner":
        return landowner(p.get("acres", 0), p.get("rent_per_acre", 0), p.get("seasons", 1),
                         p.get("upkeep_per_acre", 0))
    if kind == "farmer":
        return farmer(p.get("acres", 0), p.get("revenue_per_acre", 0),
                      p.get("inputs_per_acre", 0), p.get("rent_per_acre", 0))
    raise SimulationError("Unknown kind of arrangement.")


# Starting numbers for each calculator. They are round placeholders to be
# changed, not market data, and the page says so.
DEFAULTS: dict[str, dict[str, Any]] = {
    "crop": {"cost": 100000, "sale": 160000, "investor_pct": 70},
    "livestock": {"cost": 250000, "sale": 380000, "investor_pct": 60},
    "space": {"setup": 40000, "batches": 6, "batch_cost": 9000, "batch_sale": 20000,
              "investor_pct": 60},
    "shares": {"total_units": 80, "unit_price": 25000, "units_held": 4, "sale": 2600000,
               "investor_pct": 70},
    "landowner": {"acres": 4, "rent_per_acre": 8000, "seasons": 2, "upkeep_per_acre": 0},
    "farmer": {"acres": 3, "revenue_per_acre": 45000, "inputs_per_acre": 22000,
               "rent_per_acre": 8000},
}
