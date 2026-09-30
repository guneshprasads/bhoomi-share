import pytest

from app import example, ledger, risk


def plan(pid="chana-212-3"):
    return next(p for p in ledger.example_plans() if p["id"] == pid)


# ------------------------------------------------------------------ ledger

def test_csv_round_trip_keeps_every_plan():
    plans = ledger.example_plans()
    parsed = ledger.parse_csv(ledger.to_csv(plans))
    assert parsed["issues"] == []
    assert [p["id"] for p in parsed["plans"]] == [p["id"] for p in plans]
    a, b = plans[0], parsed["plans"][0]
    assert ledger.cost_total(a) == ledger.cost_total(b) == 100000
    assert len(a["history"]) == len(b["history"]) == 5
    assert b["benchmark"] == a["benchmark"]


def test_a_budget_that_does_not_add_up_is_flagged_with_the_size_of_the_gap():
    c = ledger.check_plan(plan("jowar-214-1"))
    budget = next(x for x in c["checks"] if x["key"] == "budget")
    assert budget["status"] == "off" and "+9.7%" in budget["detail"]


def test_a_never_logged_spend_is_not_reported_not_zero():
    c = ledger.check_plan(plan("tur-211"))
    log = next(x for x in c["checks"] if x["key"] == "log")
    assert log["status"] == "missing" and "not reported, not zero" in log["detail"]


def test_a_clean_plan_adds_up_and_earns_full_trust():
    c = ledger.check_plan(plan("chana-212-3"))
    assert c["badge"] == "adds up" and c["trust"] >= 95


def test_settlement_balance_closes_for_a_sold_season():
    c = ledger.check_plan(plan("jowar-214-1"))
    settle = next(x for x in c["checks"] if x["key"] == "settle")
    assert settle["status"] == "ok"


def test_import_reports_problems_instead_of_hiding_them():
    bad = "plan,record,label,value,season\np1,meta,area,three,\np1,cost,Seed,abc,\np1,weird,x,1,\n,meta,area,3,\n"
    parsed = ledger.parse_csv(bad)
    assert len(parsed["issues"]) >= 4
    assert parsed["plans"][0]["area"] is None                   # kept as not reported


def test_import_rejects_the_wrong_file_in_plain_words():
    with pytest.raises(ledger.LedgerError, match="columns"):
        ledger.parse_csv("a,b\n1,2\n")
    with pytest.raises(ledger.LedgerError, match="200 KB"):
        ledger.parse_csv("x" * 300_000)
    with pytest.raises(ledger.LedgerError, match="No plans"):
        ledger.parse_csv("plan,record,label,value,season\n")


# ------------------------------------------------------------------ risk

def test_risk_is_deterministic():
    a, b = risk.assess(plan()), risk.assess(plan())
    assert a["base"] == b["base"] and a["histogram"] == b["histogram"]


def test_more_failed_seasons_means_more_shortfall():
    low = risk.assess(plan(), {"p_fail": 0.02})["base"]
    high = risk.assess(plan(), {"p_fail": 0.30})["base"]
    assert high["p_short"] > low["p_short"]
    assert high["expected_shortfall"] > low["expected_shortfall"]


def test_bad_case_is_at_least_the_expected_shortfall():
    for p in ledger.example_plans():
        s = risk.assess(p)["base"]
        assert s["bad_case"] >= s["expected_shortfall"]


def test_insurance_cuts_the_bad_case():
    r = risk.assess(plan())
    none = r["options"][0]
    ins = next(o for o in r["options"] if o["key"] == "insurance")
    assert ins["bad_case"] < none["bad_case"]


def test_fixes_are_only_offered_where_they_apply():
    sheep = {o["key"] for o in risk.assess(plan("sheep-unit-hassan"))["options"]}
    assert "vet" in sheep and "drip" not in sheep
    mush = {o["key"] for o in risk.assess(plan("mushroom-mysuru"))["options"]}
    assert "climate" in mush and "insurance" not in mush


def test_a_fix_that_costs_more_than_it_gives_does_not_pay_back():
    r = risk.assess(plan())                                     # drip on 3.2 acres is dear for what it saves
    drip = next(o for o in r["options"] if o["key"] == "drip")
    assert drip["net_benefit"] < 0 and r["best"] != "drip"


def test_overriding_a_fix_changes_the_answer():
    cheap = risk.assess(plan(), fix_overrides={"drip": {"cost_per_unit": 500}})
    drip = next(o for o in cheap["options"] if o["key"] == "drip")
    assert drip["net_benefit"] > 0


def test_reconciliation_weights_the_precise_source_and_scores_agreement():
    rec = risk.reconcile(plan())
    assert len(rec["sources"]) == 3
    hist = next(s for s in rec["sources"] if s["kind"] == "history")
    assert abs(rec["mean"] - hist["mean"]) < abs(rec["mean"] - 8.0)   # pulled toward the land's own record
    disagree = dict(plan(), expected_yield=16.0)
    assert risk.reconcile(disagree)["trust"] < rec["trust"]


def test_holding_adds_up():
    h = risk.holding(ledger.example_plans())
    live = [r for r in h["rows"] if not r.get("skipped")]
    assert h["totals"]["expected_shortfall"] == sum(r["expected_shortfall"] for r in live)
    assert h["totals"]["after_fixes"] <= h["totals"]["expected_shortfall"]


def test_a_plan_without_what_it_needs_is_refused_clearly():
    with pytest.raises(ValueError, match="area"):
        risk.assess({"id": "x", "kind": "crop", "area": None, "expected_price": 1, "costs": [], "history": []})


def test_assumptions_are_clamped_not_trusted():
    r = risk.assess(plan(), {"p_fail": 99, "yield_cv": -5, "rho": 7})
    assert r["assumptions"]["p_fail"] == 0.6 and r["assumptions"]["yield_cv"] == 0.02 and r["assumptions"]["rho"] == 0.9


# ------------------------------------------------------------------ API

def test_api_example_and_import_and_risk(client):
    ex = client.get("/api/ledger/example").json()
    assert len(ex["plans"]) == 6 and ex["csv"].startswith("plan,record")
    imp = client.post("/api/ledger/import", json={"csv": ex["csv"]}).json()
    assert [p["id"] for p in imp["plans"]] == [p["id"] for p in ex["plans"]]
    r = client.post("/api/risk", json={"plan": ex["plans"][0]}).json()
    assert r["runs"] == risk.RUNS and r["options"][0]["key"] == "none"
    h = client.post("/api/holding", json={"plans": ex["plans"]}).json()
    assert len(h["rows"]) == 6


def test_api_errors_are_readable(client):
    assert "columns" in client.post("/api/ledger/import", json={"csv": "nope"}).json()["error"]
    assert client.post("/api/risk", json={}).status_code == 422
    assert client.post("/api/holding", json={"plans": []}).status_code == 422
    bad = client.post("/api/risk", json={"plan": {"id": "z", "kind": "crop"}})
    assert bad.status_code == 422


def test_verdict_uses_value_created_not_a_possibly_negative_shortfall_change():
    r = risk.assess(plan())
    assert r["best"] and "adds" in r["verdict"] and "protects" not in r["verdict"]
    assert "-" not in r["verdict"].split("pays back")[1].split("a net gain")[0]


def test_ledger_and_risk_pages_render(client):
    for path in ("/ledger", "/ledger/risk"):
        r = client.get(path)
        assert r.status_code == 200 and "Example data" in r.text or "simulation, not a forecast" in r.text
