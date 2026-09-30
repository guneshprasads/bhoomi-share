"""The explanatory pages: they must render, in both languages, and carry the
honesty the site promises (a failed season is always shown)."""

import pytest


def test_earn_page_renders_all_four_roles(client):
    r = client.get("/earn")
    assert r.status_code == 200
    for role in ("investor", "grower", "landowner", "farmer"):
        assert f'id="{role}"' in r.text
    assert "Failed season" in r.text                      # never just the good case
    assert "No return is guaranteed" in r.text


def test_earn_page_first_paint_matches_the_simulator(client):
    page = client.get("/earn").text
    # default crop plan: 1,00,000 in, 1,60,000 expected -> +42,000 for the funder
    assert "1,00,000" in page and "1,60,000" in page and "+42,000" in page


def test_earn_page_in_kannada(client):
    client.get("/lang/kn", params={"next": "/earn"})
    page = client.get("/earn").text
    assert "ಗಳಿಕೆ" in page


def test_assets_are_versioned(client):
    page = client.get("/earn").text
    assert "/static/earn.css?v=" in page
    assert "/static/site.css?v=" in page


MODEL_SLUGS = ("crop-plans", "livestock", "small-spaces", "land-shares", "land-lease")


@pytest.mark.parametrize("slug", MODEL_SLUGS)
def test_every_model_page_renders_with_risks_and_a_worked_example(client, slug):
    r = client.get(f"/models/{slug}")
    assert r.status_code == 200
    assert "What can go wrong" in r.text
    assert "not a forecast" in r.text.lower()


def test_funded_models_show_a_failed_season(client):
    for slug in ("crop-plans", "livestock", "small-spaces", "land-shares"):
        assert "Failed season" in client.get(f"/models/{slug}").text


def test_land_shares_page_says_a_share_is_not_land(client):
    assert "never of the land" in client.get("/models/land-shares").text


def test_unknown_model_is_a_404(client):
    assert client.get("/models/nope").status_code == 404


def test_models_index_compares_all_five(client):
    page = client.get("/models").text
    for needle in ("Crop plan", "Livestock unit", "Small space", "Land shares", "Lease"):
        assert needle in page


def test_model_example_budgets_add_up():
    from app import content
    for slug in content.ORDER:
        m = content.get(slug)
        if m["costs"]:
            assert content.cost_total(m) > 0
    # the crop example matches the simulator's default crop budget
    assert content.cost_total(content.get("crop-plans")) == 100000
    assert content.cost_total(content.get("livestock")) == 250000
    assert content.cost_total(content.get("land-shares")) == 2000000


def test_how_it_works_walks_one_season_and_states_what_the_site_does_not_do(client):
    r = client.get("/how-it-works")
    assert r.status_code == 200
    for step in ("A plan is posted", "The agreement is signed", "Proceeds are split"):
        assert step in r.text
    assert "Hold deposits, collect rent, or move money" in r.text
    assert "Guarantee any return" in r.text


def test_stories_are_labelled_illustrative_and_show_failure(client):
    r = client.get("/stories")
    assert r.status_code == 200
    assert "illustrative, not real customers" in r.text
    assert "Failed season" in r.text
    for name in ("Ravi", "Manjula", "Shalini", "Asha", "Lakshmi", "Mahesh"):
        assert name in r.text


def test_story_numbers_come_from_the_simulator():
    from app import content
    ravi = content.story_with_numbers(next(s for s in content.STORIES if s["slug"] == "ravi"))
    expected = next(x for x in ravi["result"]["scenarios"] if x["key"] == "expected")
    assert expected["you_net"] == 42000
    shalini = content.story_with_numbers(next(s for s in content.STORIES if s["slug"] == "shalini"))
    assert shalini["result"]["per_year"] == 64000
