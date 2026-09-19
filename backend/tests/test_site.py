"""The website: pages, accounts, listings, plans and who may touch what."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app
from app.security import hash_password
from app.settings import get_settings
from tests.conftest import follow

LISTING = {
    "title": "3 acres with a borewell",
    "acres": "3.0",
    "district": "Belagavi",
    "state": "Karnataka",
    "water_source": "Borewell",
    "term_months": "11",
    "rent_per_acre": "18000",
    "status": "open",
}

SEASON = {
    "parcel_label": "BS-04",
    "acres": "3.2",
    "crop": "Chana",
    "district": "Belagavi",
    "state": "Karnataka",
    "season_label": "Rabi 2026",
    "input_budget": "96000",
    "expected_quintals": "26",
    "expected_price": "5400",
    "investor_pct": "70",
    "status": "open",
}


@pytest.mark.parametrize(
    "path", ["/", "/how-it-works", "/fine-print", "/land", "/seasons", "/login", "/signup"]
)
def test_public_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert "Bhoomi Share" in r.text


def test_unknown_url_gets_the_error_page(client):
    r = client.get("/no-such-page")
    assert r.status_code == 404
    assert "Nothing here" in r.text


def test_dashboard_redirects_anonymous_visitors(client):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login?next=/dashboard"


def test_signup_rejects_bad_input(client):
    base = {
        "name": "Asha Patil", "email": "asha@example.com", "phone": "9876543210",
        "district": "Belagavi", "state": "Karnataka",
        "password": "pilot-season", "password2": "pilot-season", "roles": ["farmer"],
    }
    assert "at least 8 characters" in client.post(
        "/signup", data={**base, "password": "short", "password2": "short"}).text
    assert "two passwords are different" in client.post(
        "/signup", data={**base, "password2": "something-else"}).text
    assert "10-digit" in client.post("/signup", data={**base, "phone": "12345"}).text
    assert "does not look right" in client.post("/signup", data={**base, "email": "asha"}).text
    assert "at least one side" in client.post("/signup", data={**base, "roles": []}).text


def test_signup_then_logout_then_login(client):
    data = {
        "name": "Asha Patil", "email": "asha@example.com", "phone": "9876543210",
        "district": "Belagavi", "state": "Karnataka",
        "password": "pilot-season", "password2": "pilot-season", "roles": ["farmer"],
    }
    assert client.post("/signup", data=data, follow_redirects=False).status_code == 303
    assert "Asha" in client.get("/dashboard").text

    client.post("/logout")
    assert client.get("/dashboard", follow_redirects=False).status_code == 303

    bad = client.post("/login", data={"email": "asha@example.com", "password": "wrong"})
    assert "do not match" in bad.text

    ok = client.post("/login", data={"email": "asha@example.com", "password": "pilot-season"},
                     follow_redirects=False)
    assert ok.status_code == 303


def test_duplicate_email_and_phone_are_refused(client, make_user):
    make_user(email="one@example.com", phone="9800000001")
    r = client.post("/signup", data={
        "name": "Someone Else", "email": "one@example.com", "phone": "9800000002",
        "district": "Pune", "state": "Maharashtra",
        "password": "pilot-season", "password2": "pilot-season", "roles": ["investor"],
    })
    assert "already an account on that email" in r.text

    r = client.post("/signup", data={
        "name": "Someone Else", "email": "two@example.com", "phone": "9800000001",
        "district": "Pune", "state": "Maharashtra",
        "password": "pilot-season", "password2": "pilot-season", "roles": ["investor"],
    })
    assert "already an account on that phone" in r.text


def test_listing_lifecycle_and_search(client, make_user):
    owner = make_user(roles=["landowner"])
    r = owner.post("/dashboard/listings/new", data=LISTING, follow_redirects=False)
    assert r.status_code == 303
    listing_url = r.headers["location"]

    assert "borewell" in client.get("/land").text
    assert "borewell" in client.get("/land", params={"district": "belagavi"}).text
    assert "borewell" not in client.get("/land", params={"district": "satara"}).text
    assert "borewell" not in client.get("/land", params={"min_acres": "10"}).text

    r = owner.post(listing_url.replace("/land/", "/dashboard/listings/") + "/edit",
                   data={**LISTING, "title": "3 acres, bunds redone"}, follow_redirects=False)
    assert r.status_code == 303
    assert "bunds redone" in client.get(listing_url).text

    owner.post(listing_url.replace("/land/", "/dashboard/listings/") + "/delete")
    assert client.get(listing_url).status_code == 404


def test_draft_listing_is_private(client, make_user):
    owner = make_user(roles=["landowner"])
    r = owner.post("/dashboard/listings/new", data={**LISTING, "status": "draft"},
                   follow_redirects=False)
    url = r.headers["location"]
    assert owner.get(url).status_code == 200
    assert client.get(url).status_code == 404
    assert "borewell" not in client.get("/land").text


def test_only_the_owner_may_edit_a_listing(make_user):
    owner = make_user(roles=["landowner"])
    other = make_user(roles=["farmer"])
    url = owner.post("/dashboard/listings/new", data=LISTING,
                     follow_redirects=False).headers["location"]
    edit = url.replace("/land/", "/dashboard/listings/") + "/edit"
    assert other.get(edit).status_code == 403
    assert other.post(edit, data=LISTING).status_code == 403


def test_inquiry_reaches_the_owner(client, make_user):
    owner = make_user(roles=["landowner"])
    farmer = make_user(roles=["farmer"], name="Asha Patil")
    url = owner.post("/dashboard/listings/new", data=LISTING,
                     follow_redirects=False).headers["location"]

    # anonymous visitors are sent to log in first
    assert client.post(f"{url}/inquire", data={"message": "x" * 20},
                       follow_redirects=False).status_code == 303

    short = follow(farmer, farmer.post(f"{url}/inquire", data={"message": "hi"}))
    assert "line or two" in short.text

    ok = follow(farmer, farmer.post(
        f"{url}/inquire", data={"message": "I farm next door and can start in June."}))
    assert "The owner has your name" in ok.text

    board = owner.get("/dashboard").text
    assert "Asha Patil" in board and "farm next door" in board


def test_owner_cannot_inquire_on_their_own_parcel(make_user):
    owner = make_user(roles=["landowner"])
    url = owner.post("/dashboard/listings/new", data=LISTING,
                     follow_redirects=False).headers["location"]
    r = follow(owner, owner.post(f"{url}/inquire", data={"message": "talking to myself here"}))
    assert "your own parcel" in r.text


def test_season_plan_and_pledges(client, make_user):
    grower = make_user(roles=["grower"])
    investor = make_user(roles=["investor"])

    url = grower.post("/dashboard/seasons/new", data=SEASON,
                      follow_redirects=False).headers["location"]
    page = client.get(url).text
    assert "Chana" in page
    assert "1,40,400" in page  # 26 quintals x 5400 expected sale, Indian grouping

    assert "your own plan" in follow(
        grower, grower.post(f"{url}/pledge", data={"amount": "5000"})).text
    assert "at least" in follow(
        investor, investor.post(f"{url}/pledge", data={"amount": "100"})).text

    ok = follow(investor, investor.post(
        f"{url}/pledge", data={"amount": "40000", "note": "Happy to go higher."}))
    assert "Interest recorded" in ok.text
    assert "40,000" in grower.get(url).text          # the grower sees who is in
    assert "40,000" in investor.get("/dashboard").text

    # pledging twice replaces rather than doubles
    investor.post(f"{url}/pledge", data={"amount": "50000"})
    assert "50,000" in client.get(url).text
    assert "90,000" not in client.get(url).text

    assert "Withdrawn" in follow(investor, investor.post(f"{url}/pledge/withdraw")).text


def test_only_the_grower_writes_the_season_log(make_user):
    grower = make_user(roles=["grower"])
    other = make_user(roles=["investor"])
    url = grower.post("/dashboard/seasons/new", data=SEASON,
                      follow_redirects=False).headers["location"]

    assert other.post(f"{url}/updates", data={"body": "I sowed nothing."}).status_code == 403

    grower.post(f"{url}/updates", data={"body": "Sowed 3.2 acres on the 14th.", "spend": "18500"})
    page = other.get(url).text
    assert "Sowed 3.2 acres" in page and "18,500" in page


def test_admin_area_is_closed_to_ordinary_accounts(make_user):
    member = make_user()
    assert member.get("/admin").status_code == 403
    assert member.get("/admin/waitlist.csv").status_code == 403


def test_admin_area_opens_for_an_admin(client):
    settings = get_settings()
    with db.closing_conn(settings.db_path) as conn:
        db.create_user(conn, name="Gunesh Prasad", email="admin@example.com",
                       phone="9812345678", password_hash=hash_password("pilot-season"),
                       roles="grower", district="Belagavi", state="Karnataka", is_admin=True)
        conn.commit()

    admin = TestClient(app, follow_redirects=False)
    admin.post("/login", data={"email": "admin@example.com", "password": "pilot-season"})
    page = admin.get("/admin")
    assert page.status_code == 200
    assert "Waitlist" in page.text
    assert admin.get("/admin/waitlist.csv").status_code == 200


def test_profile_edit(make_user):
    member = make_user(roles=["farmer"])
    r = follow(member, member.post("/dashboard/profile", data={
        "name": "Asha R Patil", "district": "Satara", "state": "Maharashtra",
        "roles": ["farmer", "grower"],
    }))
    assert "Profile saved" in r.text
    assert "Satara" in member.get("/dashboard").text


def test_api_still_serves_listings_and_seasons(client, make_user):
    owner = make_user(roles=["landowner"])
    owner.post("/dashboard/listings/new", data=LISTING)
    body = client.get("/api/listings").json()
    assert body["count"] == 1
    assert body["listings"][0]["title"] == LISTING["title"]

    owner.post("/dashboard/seasons/new", data=SEASON)
    assert client.get("/api/seasons").json()["count"] == 1
