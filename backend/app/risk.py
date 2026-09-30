"""Money-at-risk: Predict and Decide.

For one plan, simulate many possible seasons and ask how often the sale fails to
cover the costs, by how much, and whether a fix would pay for itself.

It is a simulation from stated assumptions, NOT a forecast. Everything it assumes
is returned with the result so the page can show what is data, what is model and
what is assumed.

The same underlying random draws are reused for every option (common random
numbers), so the difference between "do nothing" and a fix is the fix, not noise.
Results are seeded, so the same inputs always give the same numbers.
"""

from __future__ import annotations

import math
import random
import statistics
from typing import Any

from . import example
from .ledger import cost_total

RUNS = 2000
MAX_RUNS = 5000
SEED = 20260928
BINS = 28

# Fixes a grower could make. Effects and prices are ASSUMPTIONS, editable on the
# page, and meant to be replaced with a real quote. `kinds` says where each applies.
FIX_CATALOG: dict[str, dict[str, Any]] = {
    "drip": {
        "label": "Drip irrigation", "kinds": ("crop", "shares"),
        "blurb": "Steadier water: fewer failed seasons and a narrower yield spread.",
        "cost_per_unit": 6000, "cost_label": "Cost per acre",
        "p_fail_mult": 0.5, "cv_mult": 0.85, "yield_uplift": 0.04,
    },
    "insurance": {
        "label": "Crop insurance", "kinds": ("crop", "shares"),
        "blurb": "Pays out when the yield falls well short of normal. The premium is the cost.",
        "cover_pct": 0.6, "premium_rate": 0.04, "trigger": 0.7,
        "cost_label": "Premium, as a share of the amount covered",
    },
    "contract": {
        "label": "Assured buyer (forward price)", "kinds": ("crop", "shares", "livestock", "space"),
        "blurb": "Fixes the price in advance: no price swings, at a small discount to the expected price.",
        "price_discount": 0.06,
    },
    "seed": {
        "label": "Better seed or stock", "kinds": ("crop", "livestock", "shares"),
        "blurb": "A higher, steadier yield for a little more up front.",
        "cost_per_unit": 1500, "cost_label": "Extra cost per unit",
        "yield_uplift": 0.05, "cv_mult": 0.92,
    },
    "vet": {
        "label": "Vaccination and vet plan", "kinds": ("livestock",),
        "blurb": "Fewer outbreaks: a lower chance of a badly failed cycle.",
        "cost_per_unit": 350, "cost_label": "Cost per head",
        "p_fail_mult": 0.45, "cv_mult": 0.9, "yield_uplift": 0.0,
    },
    "climate": {
        "label": "Humidity and temperature control", "kinds": ("space",),
        "blurb": "Fewer spoiled batches in a hot week.",
        "cost_per_unit": 2500, "cost_label": "Cost per batch",
        "p_fail_mult": 0.4, "cv_mult": 0.8, "yield_uplift": 0.03,
    },
}


# --------------------------------------------------------------------------- #
# Is the starting number trustworthy? Three sources, one best estimate.
# --------------------------------------------------------------------------- #

def reconcile(plan: dict[str, Any]) -> dict[str, Any]:
    """Combine the grower's own figure, the farm's history and a district benchmark
    into one expected yield, weighting each by how precise it is."""
    sources: list[dict[str, Any]] = []
    exp = plan.get("expected_yield")
    if exp:
        sources.append({"name": "The plan's own figure", "mean": float(exp), "sd": float(exp) * 0.18, "kind": "claim"})
    hist = [h[1] for h in plan.get("history", []) if h[1] is not None]
    if len(hist) >= 2:
        sd = statistics.pstdev(hist) / math.sqrt(len(hist))
        sources.append({"name": f"The land's own {len(hist)} seasons", "mean": statistics.fmean(hist), "sd": max(sd, 1e-6), "kind": "history"})
    elif len(hist) == 1:
        sources.append({"name": "The land's one past season", "mean": hist[0], "sd": hist[0] * 0.3, "kind": "history"})
    bm = plan.get("benchmark")
    if bm:
        sources.append({"name": "District benchmark (assumed)", "mean": float(bm[0]), "sd": float(bm[1]), "kind": "benchmark"})
    if not sources:
        return {"sources": [], "mean": None, "sd": None, "trust": 0, "agreement": None}

    weights = [1 / (s["sd"] ** 2) for s in sources]
    mean = sum(w * s["mean"] for w, s in zip(weights, sources)) / sum(weights)
    sd = math.sqrt(1 / sum(weights))

    gap = 0.0
    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):
            combined = math.hypot(sources[i]["sd"], sources[j]["sd"])
            gap = max(gap, abs(sources[i]["mean"] - sources[j]["mean"]) / combined)
    # trust: many independent sources that agree
    trust = round(100 * max(0.0, 1 - gap / 2.5) * (0.55 + 0.15 * min(len(sources), 3)))
    return {
        "sources": [{**s, "mean": round(s["mean"], 3), "sd": round(s["sd"], 3)} for s in sources],
        "mean": round(mean, 3), "sd": round(sd, 3), "rel_error_95": round(1.96 * sd / mean * 100, 1) if mean else None,
        "agreement": round(gap, 2), "trust": min(100, trust),
    }


# --------------------------------------------------------------------------- #
# the simulation
# --------------------------------------------------------------------------- #

def _draws(n: int, seed: int) -> list[tuple[float, float, float]]:
    rng = random.Random(seed)
    return [(rng.gauss(0, 1), rng.gauss(0, 1), rng.random()) for _ in range(n)]


def _percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def _scenario(plan: dict[str, Any], a: dict[str, float], mu: float, fix: dict[str, float] | None) -> dict[str, float]:
    """Numbers that define one option: yield mean/spread, failure chance, price rule, cost."""
    f = fix or {}
    cv = a["yield_cv"] * f.get("cv_mult", 1.0)
    p_fail = min(1.0, a["p_fail"] * f.get("p_fail_mult", 1.0))
    return {
        "mu": mu * (1 + f.get("yield_uplift", 0.0)), "cv": cv, "p_fail": p_fail,
        "fail_factor": a["fail_factor"], "price_vol": 0.0 if f.get("fixed_price") else a["price_vol"],
        "price0": plan["expected_price"] * (1 - f.get("price_discount", 0.0)),
        "extra_cost": f.get("extra_cost", 0.0), "insured": f.get("insured", 0.0), "trigger": f.get("trigger", 0.0),
        "rho": a["rho"],
    }


def _run(plan: dict[str, Any], sc: dict[str, float], base_cost: float, draws) -> list[float]:
    """Net profit for each simulated season (revenue + payouts - costs - the fix's cost)."""
    area = float(plan["area"])
    sig = math.sqrt(math.log(1 + sc["cv"] ** 2))
    tau = math.sqrt(math.log(1 + sc["price_vol"] ** 2)) if sc["price_vol"] > 0 else 0.0
    rho = sc["rho"]
    out = []
    for zy, zp, u in draws:
        zp2 = rho * zy + math.sqrt(max(0.0, 1 - rho * rho)) * zp
        y = sc["mu"] * math.exp(sig * zy - sig * sig / 2)
        if u < sc["p_fail"]:
            y *= sc["fail_factor"]
        price = sc["price0"] * (math.exp(tau * zp2 - tau * tau / 2) if tau else 1.0)
        revenue = area * y * price
        payout = 0.0
        if sc["insured"] and y < sc["trigger"] * sc["mu"]:
            payout = sc["insured"] * (sc["trigger"] * sc["mu"] - y) / (sc["trigger"] * sc["mu"])
        out.append(revenue + payout - base_cost - sc["extra_cost"])
    return out


def _stats(profit: list[float], cost: float) -> dict[str, Any]:
    n = len(profit)
    short = [max(-p, 0.0) for p in profit]
    srt = sorted(profit)
    return {
        "p_short": round(sum(1 for p in profit if p < 0) / n, 4),
        "expected_shortfall": round(sum(short) / n),
        "bad_case": round(_percentile(sorted(short), 0.95)),       # 1 season in 20
        "expected_profit": round(sum(profit) / n),
        "p10_profit": round(_percentile(srt, 0.10)), "p50_profit": round(_percentile(srt, 0.50)),
        "p90_profit": round(_percentile(srt, 0.90)),
    }


def applicable_fixes(kind: str) -> list[str]:
    return [k for k, v in FIX_CATALOG.items() if kind in v["kinds"]]


def _fix_params(key: str, plan: dict[str, Any], overrides: dict[str, float], base_cost: float, mu: float) -> dict[str, float]:
    spec = {**FIX_CATALOG[key], **{k: v for k, v in (overrides or {}).items() if isinstance(v, (int, float))}}
    area = float(plan["area"])
    out: dict[str, float] = {}
    for k in ("p_fail_mult", "cv_mult", "yield_uplift", "price_discount", "trigger"):
        if k in spec:
            out[k] = float(spec[k])
    if key == "contract":
        out["fixed_price"] = 1.0
    if "cost_per_unit" in spec:
        out["extra_cost"] = float(spec["cost_per_unit"]) * area
    if key == "insurance":
        insured = float(spec["cover_pct"]) * base_cost
        out["insured"] = insured
        out["extra_cost"] = insured * float(spec["premium_rate"])
    return out


def assess(plan: dict[str, Any], assumptions: dict[str, float] | None = None,
           fix_overrides: dict[str, dict[str, float]] | None = None, runs: int = RUNS) -> dict[str, Any]:
    """Everything the risk page shows for one plan."""
    if not plan.get("area") or not plan.get("expected_price") or not (plan.get("expected_yield") or plan.get("history")):
        raise ValueError("A plan needs an area, an expected price and an expected yield (or some history) to be simulated.")
    a = {**example.DEFAULT_ASSUMPTIONS, **{k: float(v) for k, v in (assumptions or {}).items() if k in example.DEFAULT_ASSUMPTIONS}}
    a["yield_cv"] = min(max(a["yield_cv"], 0.02), 0.9)
    a["price_vol"] = min(max(a["price_vol"], 0.0), 0.8)
    a["p_fail"] = min(max(a["p_fail"], 0.0), 0.6)
    a["fail_factor"] = min(max(a["fail_factor"], 0.0), 0.9)
    a["rho"] = min(max(a["rho"], -0.9), 0.9)
    runs = max(200, min(int(runs), MAX_RUNS))

    rec = reconcile(plan)
    mu = rec["mean"] or float(plan["expected_yield"])
    cost = cost_total(plan)
    draws = _draws(runs, SEED)

    base = _run(plan, _scenario(plan, a, mu, None), cost, draws)
    base_stats = _stats(base, cost)
    base_ev = sum(base) / len(base)

    # histogram of profit, with the break-even line at zero
    lo, hi = _percentile(sorted(base), 0.005), _percentile(sorted(base), 0.995)
    width = (hi - lo) / BINS or 1.0
    counts = [0] * BINS
    for p in base:
        counts[min(BINS - 1, max(0, int((p - lo) / width)))] += 1
    hist = [{"from": round(lo + i * width), "to": round(lo + (i + 1) * width), "share": round(c / runs, 4)} for i, c in enumerate(counts)]

    options = [{"key": "none", "label": "Do nothing", **base_stats, "cost": 0, "protects": 0, "value": 0, "net_benefit": 0, "multiple": None}]
    for key in applicable_fixes(plan["kind"]):
        params = _fix_params(key, plan, (fix_overrides or {}).get(key, {}), cost, mu)
        profit = _run(plan, _scenario(plan, a, mu, params), cost, draws)
        st = _stats(profit, cost)
        fix_cost = round(params.get("extra_cost", 0.0))
        protects = base_stats["expected_shortfall"] - st["expected_shortfall"]
        net = round(sum(profit) / len(profit) - base_ev)            # change in expected profit, after the fix's own cost
        value = net + fix_cost                                      # expected value the fix creates, before its cost
        options.append({"key": key, "label": FIX_CATALOG[key]["label"], "blurb": FIX_CATALOG[key]["blurb"], **st,
                        "cost": fix_cost, "protects": protects, "value": value, "net_benefit": net,
                        "multiple": round(value / fix_cost, 1) if fix_cost else None})

    paying = [o for o in options[1:] if o["net_benefit"] > 0]
    best = max(paying, key=lambda o: o["net_benefit"]) if paying else None
    return {
        "plan": {"id": plan["id"], "name": plan.get("name", plan["id"]), "kind": plan["kind"], "area": plan["area"], "unit": plan.get("unit", "")},
        "runs": runs, "cost": round(cost),
        "expected_revenue": round(sum(base) / len(base) + cost),
        "reconciliation": rec, "base": base_stats, "histogram": hist,
        "options": options, "best": best["key"] if best else None,
        "verdict": _verdict(base_stats, best),
        "assumptions": a,
        "provenance": {
            "data": ["Cost lines, stated budget and logged spending from the ledger", "Past seasons' yield and price, where the ledger has them"],
            "model": ["Yield and price drawn from lognormal spreads, with a failed-season event", f"{runs:,} simulated seasons, seeded so the same inputs give the same numbers"],
            "assumed": ["Yield spread, price swing, chance and severity of a failed season, their correlation",
                        "Every fix's cost and effect, and the district benchmark"],
        },
    }


def _verdict(base: dict[str, Any], best: dict[str, Any] | None) -> str:
    if base["p_short"] < 0.02:
        return "On these assumptions the sale almost always covers the costs, so a fix would not pay back."
    if not best:
        return "No single fix here pays for itself on these assumptions. The risk is real; it is cheaper to carry than to insure against."
    m = f", {best['multiple']}× its cost" if best["multiple"] else ""
    return (f"{best['label']} pays back: it protects ₹{best['protects']:,} of expected shortfall{m}, "
            f"for a net gain of ₹{best['net_benefit']:,} a season.")


def holding(plans: list[dict[str, Any]], assumptions: dict[str, float] | None = None, runs: int = 1200) -> dict[str, Any]:
    """The whole holding on one table: where to act first."""
    rows = []
    for p in plans:
        try:
            r = assess(p, assumptions, runs=runs)
        except ValueError:
            rows.append({"id": p["id"], "name": p.get("name", p["id"]), "skipped": True})
            continue
        best = next((o for o in r["options"] if o["key"] == r["best"]), None)
        rows.append({
            "id": p["id"], "name": r["plan"]["name"], "kind": p["kind"], "cost": r["cost"],
            "trust": r["reconciliation"]["trust"], "p_short": r["base"]["p_short"],
            "expected_shortfall": r["base"]["expected_shortfall"], "bad_case": r["base"]["bad_case"],
            "best_fix": best["label"] if best else None, "best_key": r["best"],
            "net_benefit": best["net_benefit"] if best else 0,
            "after_fix_shortfall": best["expected_shortfall"] if best else r["base"]["expected_shortfall"],
        })
    live = [r for r in rows if not r.get("skipped")]
    return {
        "rows": rows,
        "totals": {
            "cost": sum(r["cost"] for r in live),
            "expected_shortfall": sum(r["expected_shortfall"] for r in live),
            "after_fixes": sum(r["after_fix_shortfall"] for r in live),
            "net_benefit": sum(r["net_benefit"] for r in live),
            "bad_case_sum": sum(r["bad_case"] for r in live),
        },
    }
