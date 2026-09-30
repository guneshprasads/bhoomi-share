import pytest

from app import simulator
from app.simulator import SimulationError


def scenario(result, key):
    return next(s for s in result["scenarios"] if s["key"] == key)


def test_expected_season_splits_surplus_after_costs():
    r = simulator.funded(cost=100000, expected_sale=160000, investor_pct=70)
    s = scenario(r, "expected")
    # costs repaid first, then 60,000 surplus split 70/30
    assert s["costs_repaid"] == 100000
    assert s["surplus"] == 60000
    assert s["you_get_back"] == 100000 + 42000
    assert s["you_net"] == 42000
    assert s["grower_take"] == 18000
    assert s["you_return_pct"] == 42.0


def test_failed_season_returns_nothing_and_loses_everything():
    s = scenario(simulator.funded(100000, 160000, 70), "failed")
    assert s["you_get_back"] == 0
    assert s["you_net"] == -100000
    assert s["grower_take"] == 0


def test_weak_season_below_cost_repays_what_there_is_and_grower_gets_zero():
    # 160k * 0.6 = 96k, which is less than the 100k spent
    s = scenario(simulator.funded(100000, 160000, 70), "weak")
    assert s["sale"] == 96000
    assert s["you_get_back"] == 96000
    assert s["you_net"] == -4000
    assert s["grower_take"] == 0


def test_money_is_conserved_in_every_scenario():
    r = simulator.funded(123456, 200000, 55)
    for s in r["scenarios"]:
        assert s["you_get_back"] + s["grower_take"] == s["sale"]


def test_breakeven_is_the_cost():
    r = simulator.funded(100000, 160000, 70)
    assert r["breakeven_sale"] == 100000
    assert r["breakeven_vs_expected_pct"] == 62.5


def test_shares_scale_by_holding():
    r = simulator.shares(total_units=80, unit_price=25000, units_held=4,
                         expected_sale=2600000, investor_pct=70)
    assert r["cost"] == 2000000
    s = scenario(r, "expected")
    assert s["you_put_in"] == 100000          # 4 of 80 shares
    assert s["you_net"] == round(600000 * 0.7 * 4 / 80)


def test_shares_reject_more_than_the_parcel_has():
    with pytest.raises(SimulationError):
        simulator.shares(80, 25000, 81, 2600000, 70)
    with pytest.raises(SimulationError):
        simulator.shares(80, 25000, 0, 2600000, 70)


def test_small_space_builds_cost_from_setup_and_batches():
    r = simulator.small_space(40000, 6, 9000, 20000, 60)
    assert r["cost"] == 40000 + 6 * 9000
    assert r["expected_sale"] == 120000


def test_landowner_rent():
    r = simulator.landowner(acres=4, rent_per_acre=8000, seasons=2, own_cost_per_acre=500)
    assert r["per_season"] == 32000
    assert r["per_year"] == 64000
    assert r["net_per_year"] == 64000 - 2000


def test_farmer_profit_and_breakeven():
    r = simulator.farmer(acres=3, revenue_per_acre=45000, inputs_per_acre=22000, rent_per_acre=8000)
    assert r["cost_per_acre"] == 30000
    assert scenario(r, "expected")["profit_total"] == 45000
    assert scenario(r, "failed")["profit_per_acre"] == -30000
    assert r["breakeven_vs_expected_pct"] == pytest.approx(66.7, abs=0.05)


@pytest.mark.parametrize("bad", [
    dict(cost=-1, expected_sale=10, investor_pct=50),
    dict(cost=0, expected_sale=10, investor_pct=50),
    dict(cost=10, expected_sale=-5, investor_pct=50),
    dict(cost=10, expected_sale=10, investor_pct=101),
    dict(cost="abc", expected_sale=10, investor_pct=50),
    dict(cost=float("nan"), expected_sale=10, investor_pct=50),
    dict(cost=10**12, expected_sale=10, investor_pct=50),
])
def test_funded_rejects_nonsense(bad):
    with pytest.raises(SimulationError):
        simulator.funded(**bad)


def test_defaults_all_run():
    for kind, params in simulator.DEFAULTS.items():
        assert simulator.run(kind, params)["kind"] in {"funded", "shares", "space",
                                                        "landowner", "farmer"}


def test_api_endpoint_returns_scenarios(client):
    r = client.get("/api/simulate/crop", params={"cost": 100000, "sale": 160000,
                                                 "investor_pct": 70})
    assert r.status_code == 200
    assert [s["key"] for s in r.json()["scenarios"]] == ["strong", "expected", "weak", "failed"]


def test_api_endpoint_rejects_bad_input_in_plain_words(client):
    r = client.get("/api/simulate/crop", params={"cost": "x", "sale": 1})
    assert r.status_code == 422
    assert "number" in r.json()["error"]


def test_api_endpoint_unknown_kind(client):
    assert client.get("/api/simulate/nonsense").status_code == 422
