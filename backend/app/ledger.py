"""The farm ledger: read a plan file, give every plan an account, check it adds up.

A plan's account is "Check" in Check, Predict, Decide. Real ledgers are messy, so
the point is not to reject them but to say precisely where they do not add up,
and to keep "not reported" distinct from "zero".

File format (CSV, long form): plan,record,label,value,season. The `record`
column decides where each number goes:

  meta     one row per fact about the plan (name, district, kind, area, unit,
           investor_pct, stated_budget, expected_yield, expected_price,
           yield_unit, price_unit, benchmark_yield, benchmark_sd)
  cost     a budget line: label is the item, value the rupees
  spent    what the log says was spent (value, rupees)
  history  one past season: season, label "yield" or "price", value
  sale     actual receipts for a sold season (value, season)
"""

from __future__ import annotations

import csv
import io
from typing import Any

from . import example

TOLERANCE = 0.05                # the balance rules allow +/- 5%, like a water balance
MAX_BYTES = 200_000
MAX_PLANS = 40
KINDS = ("crop", "livestock", "space", "shares")

META_NUMERIC = {"area", "investor_pct", "stated_budget", "expected_yield", "expected_price",
                "benchmark_yield", "benchmark_sd"}


class LedgerError(ValueError):
    """Raised for a file that cannot be read at all; the message is shown to people."""


def _num(text: str) -> float | None:
    t = (text or "").strip().replace(",", "").replace("₹", "")
    if t in ("", "-", "—", "n/a", "na", "NA"):
        return None
    try:
        return float(t)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# reading
# --------------------------------------------------------------------------- #

def parse_csv(text: str) -> dict[str, Any]:
    """CSV text -> {"plans": [...], "issues": [...]}. Never guesses silently."""
    if len(text.encode("utf-8", "ignore")) > MAX_BYTES:
        raise LedgerError("That file is larger than 200 KB. Split it by season or by plan.")
    reader = csv.DictReader(io.StringIO(text.strip()))
    need = {"plan", "record", "label", "value"}
    if not reader.fieldnames or not need <= {f.strip().lower() for f in reader.fieldnames}:
        raise LedgerError("The file needs the columns: plan, record, label, value (and season). "
                          "Download the example to see the layout.")

    plans: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    for n, raw in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        pid, record, label, value = row.get("plan", ""), row.get("record", "").lower(), row.get("label", ""), row.get("value", "")
        if not pid:
            issues.append(f"Row {n}: no plan id, skipped.")
            continue
        if pid not in plans:
            if len(plans) >= MAX_PLANS:
                raise LedgerError(f"More than {MAX_PLANS} plans in one file. Import them in batches.")
            plans[pid] = {"id": pid, "name": pid, "kind": "crop", "district": "", "area": None, "unit": "acres",
                          "yield_unit": "per unit", "price_unit": "rupees per unit", "investor_pct": 70.0,
                          "expected_yield": None, "expected_price": None, "stated_budget": None,
                          "costs": [], "spent": None, "history": [], "benchmark": None, "sales": []}
        p = plans[pid]

        if record == "meta":
            if label in META_NUMERIC:
                v = _num(value)
                if v is None:
                    issues.append(f"{pid}: {label} is {value!r}, which is not a number; kept as not reported.")
                else:
                    p[label] = v
            elif label in ("name", "district", "unit", "yield_unit", "price_unit"):
                p[label] = value
            elif label == "kind":
                if value.lower() in KINDS:
                    p["kind"] = value.lower()
                else:
                    issues.append(f"{pid}: kind {value!r} is not one of {', '.join(KINDS)}; treated as crop.")
            else:
                issues.append(f"{pid}: unknown fact {label!r}, skipped.")
        elif record == "cost":
            v = _num(value)
            if v is None or v < 0:
                issues.append(f"{pid}: cost line {label!r} has no usable amount, skipped.")
            else:
                p["costs"].append((label, label, v))
        elif record == "spent":
            v = _num(value)
            if v is None:
                issues.append(f"{pid}: spent is {value!r}; kept as not reported.")
            else:
                p["spent"] = v
        elif record == "history":
            season, v = _num(row.get("season", "")), _num(value)
            if season is None or v is None or label not in ("yield", "price"):
                issues.append(f"{pid}: a history row needs a season and a 'yield' or 'price' value; skipped.")
                continue
            entry = next((h for h in p["history"] if h[0] == season), None)
            if entry is None:
                entry = [season, None, None]
                p["history"].append(entry)
            entry[1 if label == "yield" else 2] = v
        elif record == "sale":
            v, season = _num(value), _num(row.get("season", ""))
            if v is None:
                issues.append(f"{pid}: a sale row has no amount, skipped.")
            else:
                p["sales"].append({"season": season, "receipts": v})
        else:
            issues.append(f"Row {n}: record type {record!r} is not one of meta, cost, spent, history, sale; skipped.")

    out = []
    for p in plans.values():
        p["history"] = [tuple(h) for h in sorted(p["history"], key=lambda h: h[0]) if h[1] is not None and h[2] is not None]
        if p.get("benchmark_yield") is not None and p.get("benchmark_sd") is not None:
            p["benchmark"] = (p.pop("benchmark_yield"), p.pop("benchmark_sd"))
        p.pop("benchmark_yield", None)
        p.pop("benchmark_sd", None)
        out.append(p)
    if not out:
        raise LedgerError("No plans found in that file.")
    return {"plans": out, "issues": issues}


def to_csv(plans: list[dict[str, Any]]) -> str:
    """The plans back out in the same long format, so the example doubles as a template."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["plan", "record", "label", "value", "season"])
    for p in plans:
        pid = p["id"]
        for k in ("name", "kind", "district", "area", "unit", "investor_pct", "stated_budget",
                  "expected_yield", "expected_price", "yield_unit", "price_unit"):
            if p.get(k) is not None:
                w.writerow([pid, "meta", k, p[k], ""])
        if p.get("benchmark"):
            w.writerow([pid, "meta", "benchmark_yield", p["benchmark"][0], ""])
            w.writerow([pid, "meta", "benchmark_sd", p["benchmark"][1], ""])
        for item, _cat, amt in p["costs"]:
            w.writerow([pid, "cost", item, amt, ""])
        if p.get("spent") is not None:
            w.writerow([pid, "spent", "Logged to date", p["spent"], ""])
        for season, y, pr in p["history"]:
            w.writerow([pid, "history", "yield", y, season])
            w.writerow([pid, "history", "price", pr, season])
        for s in p.get("sales", []):
            w.writerow([pid, "sale", "Receipts", s["receipts"], s.get("season") or ""])
    return buf.getvalue()


def example_plans() -> list[dict[str, Any]]:
    plans = []
    for raw in example.PLANS:
        p = {k: v for k, v in raw.items()}
        p["costs"] = [tuple(c) for c in raw["costs"]]
        p["history"] = [tuple(h) for h in raw["history"]]
        settled = example.SETTLED.get(raw["id"])
        p["sales"] = [{"season": settled["season"], "receipts": settled["receipts"]}] if settled else []
        plans.append(p)
    return plans


# --------------------------------------------------------------------------- #
# checking
# --------------------------------------------------------------------------- #

def _pct(a: float, b: float) -> float:
    return (a - b) / b * 100 if b else 0.0


def _check(key: str, label: str, status: str, detail: str, weight: int, score: float) -> dict[str, Any]:
    # status: ok | off | missing ; score is 0..1 of the weight earned
    return {"key": key, "label": label, "status": status, "detail": detail, "weight": weight, "earned": round(weight * score, 1)}


def cost_total(plan: dict[str, Any]) -> float:
    lines = sum(c[2] for c in plan["costs"])
    return lines if lines else float(plan.get("stated_budget") or 0)


def check_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """The balance rules for one plan, and a 0-100 trust score. Each rule says
    what it found in words, and 'not reported' is never read as zero."""
    checks: list[dict[str, Any]] = []
    lines = sum(c[2] for c in plan["costs"])
    stated = plan.get("stated_budget")

    # 1. does the budget add up?
    if not plan["costs"]:
        checks.append(_check("budget", "Budget adds up", "missing", "No cost lines in the file.", 30, 0))
    elif not stated:
        checks.append(_check("budget", "Budget adds up", "missing", "No stated budget to compare the lines with.", 30, 0.4))
    else:
        d = _pct(lines, stated)
        if abs(d) <= TOLERANCE * 100:
            checks.append(_check("budget", "Budget adds up", "ok",
                                 f"Lines total ₹{lines:,.0f} against a stated ₹{stated:,.0f} ({d:+.1f}%).", 30, 1))
        else:
            checks.append(_check("budget", "Budget adds up", "off",
                                 f"Lines total ₹{lines:,.0f} but the plan says ₹{stated:,.0f}: off by {d:+.1f}%. Allowed: ±5%.",
                                 30, max(0, 1 - abs(d) / 25)))

    # 2. was the season's spending logged, and did it stay on budget?
    base = stated or lines
    spent = plan.get("spent")
    if spent is None:
        checks.append(_check("log", "Spend was logged", "missing", "The grower never logged any spending: not reported, not zero.", 25, 0))
    elif not base:
        checks.append(_check("log", "Spend was logged", "missing", "Spending is logged but there is no budget to compare it with.", 25, 0.5))
    else:
        d = _pct(spent, base)
        if abs(d) <= TOLERANCE * 100:
            checks.append(_check("log", "Spend was logged", "ok", f"Logged ₹{spent:,.0f} against a budget of ₹{base:,.0f} ({d:+.1f}%).", 25, 1))
        else:
            checks.append(_check("log", "Spend was logged", "off",
                                 f"Logged ₹{spent:,.0f} against a budget of ₹{base:,.0f}: off by {d:+.1f}%.", 25, max(0, 1 - abs(d) / 30)))

    # 3. does a sold season settle? receipts = repaid + funder's share + grower's share
    settled = example.SETTLED.get(plan["id"]) if plan["id"] in example.SETTLED else None
    sales = plan.get("sales") or []
    if not sales:
        checks.append(_check("settle", "Money in equals money out", "missing", "No sold season yet, so there is no settlement to check.", 25, 0.5))
    elif settled and sales[0]["receipts"] == settled["receipts"]:
        out = settled["repaid_to_funder"] + settled["funder_share"] + settled["grower_share"]
        d = _pct(out, settled["receipts"])
        if abs(d) <= TOLERANCE * 100:
            checks.append(_check("settle", "Money in equals money out", "ok",
                                 f"Receipts ₹{settled['receipts']:,.0f}; repaid ₹{settled['repaid_to_funder']:,.0f} + shares "
                                 f"₹{settled['funder_share'] + settled['grower_share']:,.0f} = ₹{out:,.0f} ({d:+.1f}%).", 25, 1))
        else:
            checks.append(_check("settle", "Money in equals money out", "off",
                                 f"Receipts ₹{settled['receipts']:,.0f} but ₹{out:,.0f} was paid out: off by {d:+.1f}%.", 25, max(0, 1 - abs(d) / 25)))
    else:
        checks.append(_check("settle", "Money in equals money out", "missing",
                             "Receipts are in the file, but the split paid out is not, so it cannot be checked.", 25, 0.4))

    # 4. enough history to say anything about variability?
    n = len(plan["history"])
    if n >= 4:
        checks.append(_check("history", "Enough seasons to judge", "ok", f"{n} past seasons on record.", 20, 1))
    elif n >= 2:
        checks.append(_check("history", "Enough seasons to judge", "off", f"Only {n} past seasons: the spread is a guess, so the forecast band stays wide.", 20, n / 4))
    else:
        checks.append(_check("history", "Enough seasons to judge", "missing", "No past seasons on record.", 20, 0))

    trust = round(sum(c["earned"] for c in checks))
    statuses = {c["status"] for c in checks}
    badge = "adds up" if statuses == {"ok"} else ("has gaps" if "missing" in statuses and "off" not in statuses else "needs a look")
    return {"checks": checks, "trust": trust, "badge": badge,
            "flags": [c["detail"] for c in checks if c["status"] != "ok"]}


def check_holding(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"id": p["id"], **check_plan(p)} for p in plans]


def cost_by_category(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Input costs across the holding, by category, per plan, for the cost tab."""
    cats: dict[str, dict[str, float]] = {}
    for p in plans:
        for _item, cat, amt in p["costs"]:
            cats.setdefault(cat, {})[p["id"]] = cats.get(cat, {}).get(p["id"], 0) + amt
    return [{"category": c, "by_plan": by, "total": sum(by.values())} for c, by in sorted(cats.items(), key=lambda kv: -sum(kv[1].values()))]
