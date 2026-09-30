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
