"""The website: pages, accounts, listings, the four funded kinds, and who may
touch what."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import db
from app.karnataka import DISTRICTS, normalise
from app.main import app
from app.security import hash_password
from app.settings import get_settings
from tests.conftest import follow, png_bytes

LISTING = {
    "title": "3 acres with a borewell",
    "acres": "3.0",
    "district": "Belagavi",
    "taluk": "Chikkodi",
    "water_source": "Borewell",
    "term_months": "11",
    "rent_per_acre": "18000",
    "status": "open",
}

CROP = {
    "kind": "crop",
    "title": "Chana on BS-04",
    "parcel_label": "BS-04",
    "acres": "3.2",
    "district": "Belagavi",
    "taluk": "Chikkodi",
    "crop": "Chana",
    "season_label": "Rabi 2026",
    "budget": "96000",
    "expected_quintals": "26",
    "expected_price": "5400",
    "investor_pct": "70",
    "status": "open",
}

LIVESTOCK = {
    "kind": "livestock",
    "title": "Forty ewes on two acres",
    "acres": "2.0",
    "district": "Vijayapura",
    "taluk": "Indi",
    "animal": "Sheep",
    "herd_size": "40",
    "cycle_months": "9",
    "budget": "340000",
    "expected_revenue": "520000",
    "investor_pct": "60",
    "status": "open",
}

SPACE = {
    "kind": "space",
    "title": "Mushrooms on a 30 by 40 site",
    "district": "Mysuru",
    "taluk": "Mysuru",
    "activity": "Mushroom",
    "area_sqft": "1200",
    "space_structure": "Empty site with a tin shed",
    "space_water": "Borewell and single-phase power",
    "space_months": "12",
    "budget": "180000",
    "expected_revenue": "360000",
    "investor_pct": "60",
    "status": "open",
}

SHARES = {
    "kind": "shares",
    "title": "Twenty-two acres at Athani, in shares",
    "acres": "22",
    "district": "Belagavi",
    "taluk": "Athani",
    "budget": "2000000",
    "expected_revenue": "3100000",
    "unit_price": "25000",
    "max_investors": "20",
    "investor_pct": "70",
    "status": "open",
}


# --------------------------------------------------------------------------- #
# pages
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("path", [
    "/", "/invest", "/seasons", "/livestock", "/spaces", "/shares", "/land",
    "/how-it-works", "/fine-print", "/login", "/signup",
])
def test_public_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert "Bhoomi Share" in r.text


def test_unknown_url_gets_the_error_page(client):
    r = client.get("/no-such-page")
    assert r.status_code == 404
    assert "Nothing here" in r.text


def test_dashboard_redirects_anonymous_visitors(client):
    r = client.get("/dashboard")
    assert r.status_code == 303
    assert r.headers["location"] == "/login?next=/dashboard"


# --------------------------------------------------------------------------- #
# Karnataka districts
# --------------------------------------------------------------------------- #

def test_thirty_one_districts():
    assert len(DISTRICTS) == 31
    assert "Belagavi" in DISTRICTS and "Vijayanagara" in DISTRICTS


@pytest.mark.parametrize("typed,expected", [
    ("Ramanagara", "Bengaluru South"),      # renamed in 2025
    ("Bengaluru Rural", "Bengaluru North"),  # renamed in 2025
    ("Belgaum", "Belagavi"),
    ("mysore", "Mysuru"),
    ("  Bagalkot ", "Bagalkote"),
    ("Chennai", None),
])
def test_old_district_names_still_resolve(typed, expected):
    assert normalise(typed) == expected


def test_signup_refuses_a_district_outside_karnataka(client):
    r = client.post("/signup", data={
        "name": "Asha Patil", "email": "asha@example.com", "phone": "9876543210",
        "district": "Pune", "taluk": "Haveli",
        "password": "pilot-season", "password2": "pilot-season", "roles": ["farmer"],
    })
    assert "Karnataka" in r.text


def test_search_accepts_the_old_district_name(client, make_user):
    owner = make_user(roles=["landowner"], district="Bengaluru South")
    owner.post("/dashboard/listings/new", data={**LISTING, "district": "Bengaluru South"})

    # someone still typing the old name finds it
    assert "borewell" in client.get("/land", params={"district": "Ramanagara"}).text
    assert "borewell" not in client.get("/land", params={"district": "Kodagu"}).text


# --------------------------------------------------------------------------- #
# accounts
# --------------------------------------------------------------------------- #

def test_signup_rejects_bad_input(client):
    base = {
        "name": "Asha Patil", "email": "asha@example.com", "phone": "9876543210",
        "district": "Belagavi", "taluk": "Chikkodi",
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
        "district": "Belagavi", "taluk": "Chikkodi",
        "password": "pilot-season", "password2": "pilot-season", "roles": ["farmer"],
    }
    assert client.post("/signup", data=data).status_code == 303
    assert "Asha" in client.get("/dashboard").text

    client.post("/logout")
    assert client.get("/dashboard").status_code == 303
    assert "do not match" in client.post(
        "/login", data={"email": "asha@example.com", "password": "wrong"}).text
    assert client.post(
        "/login", data={"email": "asha@example.com", "password": "pilot-season"}
    ).status_code == 303


def test_duplicate_email_and_phone_are_refused(client, make_user):
    make_user(email="one@example.com", phone="9800000001")
    base = {
        "name": "Someone Else", "district": "Mysuru", "taluk": "Nanjangud",
        "password": "pilot-season", "password2": "pilot-season", "roles": ["investor"],
    }
    assert "already an account on that email" in client.post(
        "/signup", data={**base, "email": "one@example.com", "phone": "9800000002"}).text
    assert "already an account on that phone" in client.post(
        "/signup", data={**base, "email": "two@example.com", "phone": "9800000001"}).text


def test_profile_edit(make_user):
    member = make_user(roles=["farmer"])
    r = follow(member, member.post("/dashboard/profile", data={
        "name": "Asha R Patil", "district": "Mysuru", "taluk": "Nanjangud",
        "roles": ["farmer", "grower"],
    }))
    assert "Profile saved" in r.text
    assert "Mysuru" in member.get("/dashboard").text


# --------------------------------------------------------------------------- #
# land listings
# --------------------------------------------------------------------------- #

def test_listing_lifecycle_and_search(client, make_user):
    owner = make_user(roles=["landowner"])
    r = owner.post("/dashboard/listings/new", data=LISTING)
    assert r.status_code == 303
    listing_url = r.headers["location"]

    assert "borewell" in client.get("/land").text
    assert "borewell" in client.get("/land", params={"district": "Belagavi"}).text
    assert "borewell" not in client.get("/land", params={"district": "Udupi"}).text
    assert "borewell" not in client.get("/land", params={"min_acres": "10"}).text

    edit = listing_url.replace("/land/", "/dashboard/listings/") + "/edit"
    assert owner.post(edit, data={**LISTING, "title": "3 acres, bunds redone"}).status_code == 303
    assert "bunds redone" in client.get(listing_url).text

    owner.post(listing_url.replace("/land/", "/dashboard/listings/") + "/delete")
    assert client.get(listing_url).status_code == 404


def test_suitable_crops_are_stored_and_shown(client, make_user):
    owner = make_user(roles=["landowner"])
    url = owner.post("/dashboard/listings/new",
                     data={**LISTING, "crops": ["Ragi", "Tur", "Nonsense"]}).headers["location"]
    page = client.get(url).text
    assert "Ragi" in page and "Tur" in page
    assert "Nonsense" not in page          # only crops from the list are kept


def test_draft_listing_is_private(client, make_user):
    owner = make_user(roles=["landowner"])
    url = owner.post("/dashboard/listings/new",
                     data={**LISTING, "status": "draft"}).headers["location"]
    assert owner.get(url).status_code == 200
    assert client.get(url).status_code == 404
    assert "borewell" not in client.get("/land").text


def test_only_the_owner_may_edit_a_listing(make_user):
    owner = make_user(roles=["landowner"])
    other = make_user(roles=["farmer"])
    url = owner.post("/dashboard/listings/new", data=LISTING).headers["location"]
    edit = url.replace("/land/", "/dashboard/listings/") + "/edit"
    assert other.get(edit).status_code == 403
    assert other.post(edit, data=LISTING).status_code == 403


def test_inquiry_reaches_the_owner(client, make_user):
    owner = make_user(roles=["landowner"])
    farmer = make_user(roles=["farmer"], name="Asha Patil")
    url = owner.post("/dashboard/listings/new", data=LISTING).headers["location"]

    assert client.post(f"{url}/inquire", data={"message": "x" * 20}).status_code == 303
    assert "line or two" in follow(farmer, farmer.post(f"{url}/inquire",
                                                       data={"message": "hi"})).text
    ok = follow(farmer, farmer.post(f"{url}/inquire",
                                    data={"message": "I farm next door and can start in June."}))
    assert "The owner has your name" in ok.text

    board = owner.get("/dashboard").text
    assert "Asha Patil" in board and "farm next door" in board


def test_owner_cannot_inquire_on_their_own_parcel(make_user):
    owner = make_user(roles=["landowner"])
    url = owner.post("/dashboard/listings/new", data=LISTING).headers["location"]
    r = follow(owner, owner.post(f"{url}/inquire", data={"message": "talking to myself here"}))
    assert "your own parcel" in r.text


# --------------------------------------------------------------------------- #
# photographs
# --------------------------------------------------------------------------- #

def test_photo_upload_strips_exif_and_shows_on_the_page(client, make_user):
    owner = make_user(roles=["landowner"])
    r = owner.post("/dashboard/listings/new", data=LISTING,
                   files=[("photos", ("field.jpg", png_bytes(gps=True), "image/jpeg"))])
    url = r.headers["location"]

    with db.closing_conn(get_settings().db_path) as conn:
        photos = db.photos_for(conn, "listing", int(url.rsplit("/", 1)[-1]))
    assert len(photos) == 1

    saved = get_settings().uploads_dir / photos[0]["path"]
    assert saved.exists()
    stored = Image.open(saved)
    assert stored.format == "JPEG"
    assert dict(stored.getexif()) == {}, "EXIF (and its GPS tags) must not survive upload"

    assert photo_path_in(client.get(url).text, photos[0]["path"])
    assert client.get(f"/uploads/{photos[0]['path']}").status_code == 200


def photo_path_in(html: str, path: str) -> bool:
    return f"/uploads/{path}" in html


def test_heic_is_refused_with_an_explanation(make_user):
    owner = make_user(roles=["landowner"])
    r = owner.post("/dashboard/listings/new", data=LISTING,
                   files=[("photos", ("IMG_0001.HEIC", b"not-really-heic", "image/heic"))])
    page = follow(owner, r)
    assert "HEIC" in page.text

    with db.closing_conn(get_settings().db_path) as conn:
        assert db.photos_for(conn, "listing", 1) == []


def test_a_photo_can_be_removed(make_user):
    owner = make_user(roles=["landowner"])
    url = owner.post("/dashboard/listings/new", data=LISTING,
                     files=[("photos", ("a.png", png_bytes(), "image/png"))]).headers["location"]
    listing_id = int(url.rsplit("/", 1)[-1])

    with db.closing_conn(get_settings().db_path) as conn:
        photo = db.photos_for(conn, "listing", listing_id)[0]
    saved = get_settings().uploads_dir / photo["path"]

    owner.post(f"/dashboard/listings/{listing_id}/photos/{photo['id']}/delete")
    with db.closing_conn(get_settings().db_path) as conn:
        assert db.photos_for(conn, "listing", listing_id) == []
    assert not saved.exists(), "the file should go with the row"


# --------------------------------------------------------------------------- #
# projects: crop, livestock, shares
# --------------------------------------------------------------------------- #

def test_crop_plan_end_to_end(client, make_user):
    grower = make_user(roles=["grower"])
    investor = make_user(roles=["investor"])

    url = grower.post("/dashboard/projects/new", data=CROP).headers["location"]
    page = client.get(url).text
    assert "Chana" in page
    assert "1,40,400" in page              # 26 quintals x 5400, Indian grouping
    assert "Chana" in client.get("/seasons").text

    assert "your own plan" in follow(grower, grower.post(f"{url}/pledge",
                                                         data={"amount": "5000"})).text
    assert "at least" in follow(investor, investor.post(f"{url}/pledge",
                                                        data={"amount": "100"})).text

    ok = follow(investor, investor.post(f"{url}/pledge",
                                        data={"amount": "40000", "note": "Happy to go higher."}))
    assert "Interest recorded" in ok.text
    assert "40,000" in grower.get(url).text
    assert "40,000" in investor.get("/dashboard").text

    investor.post(f"{url}/pledge", data={"amount": "50000"})
    assert "50,000" in client.get(url).text and "90,000" not in client.get(url).text
    assert "Withdrawn" in follow(investor, investor.post(f"{url}/pledge/withdraw")).text


def test_livestock_unit(client, make_user):
    keeper = make_user(roles=["grower"])
    investor = make_user(roles=["investor"])

    url = keeper.post("/dashboard/projects/new", data=LIVESTOCK).headers["location"]
    page = client.get(url).text
    assert "Sheep" in page and "40 head" in page
    assert "1,80,000" in page              # 5,20,000 revenue less 3,40,000 budget
    assert "ewes" in client.get("/livestock").text
    assert "ewes" not in client.get("/seasons").text

    assert "Interest recorded" in follow(
        investor, investor.post(f"{url}/pledge", data={"amount": "60000"})).text


def test_livestock_needs_an_animal_and_a_count(make_user):
    keeper = make_user(roles=["grower"])
    assert "Which animal" in keeper.post(
        "/dashboard/projects/new", data={**LIVESTOCK, "animal": ""}).text
    assert "How many animals" in keeper.post(
        "/dashboard/projects/new", data={**LIVESTOCK, "herd_size": "0"}).text


def test_shares_maths_and_display(client, make_user):
    owner = make_user(roles=["landowner"])
    url = owner.post("/dashboard/projects/new", data=SHARES).headers["location"]
    project_id = int(url.rsplit("/", 1)[-1])

    with db.closing_conn(get_settings().db_path) as conn:
        project = db.project_by_id(conn, project_id)
    assert project["total_units"] == 80          # 20,00,000 / 25,000

    page = client.get(url).text
    assert "80" in page and "25,000" in page
    assert "11,00,000" in page                   # net: 31,00,000 - 20,00,000
    assert "9,625" in page                       # per share: 70% of net / 80


def test_shares_need_five_acres(make_user):
    owner = make_user(roles=["landowner"])
    r = owner.post("/dashboard/projects/new", data={**SHARES, "acres": "3"})
    assert "5 acres or more" in r.text


def test_share_price_must_leave_at_least_two_shares(make_user):
    owner = make_user(roles=["landowner"])
    r = owner.post("/dashboard/projects/new",
                   data={**SHARES, "unit_price": "1500000"})
    assert "fewer than two shares" in r.text


def test_reserving_shares(client, make_user):
    owner = make_user(roles=["landowner"])
    investor = make_user(roles=["investor"])
    url = owner.post("/dashboard/projects/new", data=SHARES).headers["location"]

    ok = follow(investor, investor.post(f"{url}/pledge", data={"units": "6"}))
    assert "6 shares noted" in ok.text

    with db.closing_conn(get_settings().db_path) as conn:
        pledge = db.pledge_for(conn, int(url.rsplit("/", 1)[-1]), 2)
    assert pledge["units"] == 6
    assert pledge["amount"] == 6 * 25000         # rupees follow from the units

    assert "6 of 80" in client.get(url).text
    assert "How many shares" in follow(
        investor, investor.post(f"{url}/pledge", data={"units": "0"})).text
    assert "Only 74 shares are left" in follow(
        investor, investor.post(f"{url}/pledge", data={"units": "99"})).text


def test_the_cap_on_people_per_parcel_is_enforced(client, make_user):
    owner = make_user(roles=["landowner"])
    url = owner.post("/dashboard/projects/new",
                     data={**SHARES, "max_investors": "2"}).headers["location"]

    first = make_user(roles=["investor"])
    second = make_user(roles=["investor"])
    third = make_user(roles=["investor"])

    assert "noted" in follow(first, first.post(f"{url}/pledge", data={"units": "1"})).text
    assert "noted" in follow(second, second.post(f"{url}/pledge", data={"units": "1"})).text

    blocked = follow(third, third.post(f"{url}/pledge", data={"units": "1"}))
    assert "as many people as it is allowed to" in blocked.text

    # someone already in may still change their mind
    assert "noted" in follow(first, first.post(f"{url}/pledge", data={"units": "3"})).text


def test_only_the_owner_writes_the_log(make_user):
    grower = make_user(roles=["grower"])
    other = make_user(roles=["investor"])
    url = grower.post("/dashboard/projects/new", data=CROP).headers["location"]

    assert other.post(f"{url}/updates", data={"body": "I sowed nothing."}).status_code == 403
    grower.post(f"{url}/updates", data={"body": "Sowed 3.2 acres on the 14th.", "spend": "18500"})
    page = other.get(url).text
    assert "Sowed 3.2 acres" in page and "18,500" in page


def test_project_kind_cannot_be_switched_after_posting(make_user):
    grower = make_user(roles=["grower"])
    url = grower.post("/dashboard/projects/new", data=CROP).headers["location"]
    project_id = int(url.rsplit("/", 1)[-1])

    grower.post(f"/dashboard/projects/{project_id}/edit",
                data={**CROP, "kind": "shares", "title": "Sneaky switch"})
    with db.closing_conn(get_settings().db_path) as conn:
        assert db.project_by_id(conn, project_id)["kind"] == "crop"


def test_invest_page_lists_every_kind(client, make_user):
    grower = make_user(roles=["grower"])
    grower.post("/dashboard/projects/new", data=CROP)
    grower.post("/dashboard/projects/new", data=LIVESTOCK)
    grower.post("/dashboard/projects/new", data=SHARES)

    page = client.get("/invest").text
    assert "Chana" in page and "ewes" in page and "Athani" in page
    assert "Chana" in client.get("/invest", params={"kind": "crop"}).text
    assert "ewes" not in client.get("/invest", params={"kind": "crop"}).text


# --------------------------------------------------------------------------- #
# language
# --------------------------------------------------------------------------- #

def test_kannada_switch_sticks_and_renders(client):
    r = client.get("/lang/kn", params={"next": "/land"})
    assert r.status_code == 303
    assert r.headers["location"] == "/land"
    assert "bhoomi_lang=kn" in r.headers["set-cookie"]

    page = client.get("/land")
    assert "ಲಭ್ಯವಿರುವ ಭೂಮಿ" in page.text        # "Land on offer"
    assert 'lang="kn"' in page.text

    client.get("/lang/en", params={"next": "/land"})
    assert "Land on offer" in client.get("/land").text


def test_language_switch_only_redirects_inside_the_site(client):
    r = client.get("/lang/kn", params={"next": "https://example.com/evil"})
    assert r.headers["location"] == "/"


# --------------------------------------------------------------------------- #
# admin
# --------------------------------------------------------------------------- #

def test_admin_area_is_closed_to_ordinary_accounts(make_user):
    member = make_user()
    assert member.get("/admin").status_code == 403
    assert member.get("/admin/waitlist.csv").status_code == 403


def test_admin_area_opens_for_an_admin(client):
    settings = get_settings()
    with db.closing_conn(settings.db_path) as conn:
        db.create_user(conn, name="Gunesh Prasad", email="admin@example.com",
                       phone="9812345678", password_hash=hash_password("pilot-season"),
                       roles="grower", district="Belagavi", taluk="Chikkodi", is_admin=True)
        conn.commit()

    admin = TestClient(app, follow_redirects=False)
    admin.post("/login", data={"email": "admin@example.com", "password": "pilot-season"})
    page = admin.get("/admin")
    assert page.status_code == 200 and "Waitlist" in page.text
    assert admin.get("/admin/waitlist.csv").status_code == 200


# --------------------------------------------------------------------------- #
# json api
# --------------------------------------------------------------------------- #

def test_api_serves_listings_projects_and_districts(client, make_user):
    owner = make_user(roles=["landowner"])
    owner.post("/dashboard/listings/new", data=LISTING)
    owner.post("/dashboard/projects/new", data=CROP)
    owner.post("/dashboard/projects/new", data=SHARES)

    assert client.get("/api/listings").json()["count"] == 1
    assert client.get("/api/projects").json()["count"] == 2
    assert client.get("/api/projects", params={"kind": "shares"}).json()["count"] == 1

    districts = client.get("/api/districts").json()
    assert districts["state"] == "Karnataka"
    assert sum(len(v) for v in districts["divisions"].values()) == 31


# --------------------------------------------------------------------------- #
# the first-run tour
# --------------------------------------------------------------------------- #

def test_a_new_account_gets_the_tour_once(make_user):
    member = make_user()

    first = member.get("/dashboard")
    assert 'id="tour-data"' in first.text
    assert "no money moves through this site" in first.text

    assert member.post("/dashboard/tour/done").json() == {"ok": True}

    again = member.get("/dashboard")
    assert 'id="tour-data"' not in again.text
    assert "Show me around again" in again.text     # but it can be replayed


def test_the_tour_can_be_replayed_on_demand(make_user):
    member = make_user()
    member.post("/dashboard/tour/done")
    assert 'id="tour-data"' in member.get("/dashboard", params={"tour": "1"}).text


def test_the_tour_flag_lives_on_the_account_not_the_browser(make_user):
    """A second device must not be shown the tour again."""
    member = make_user(email="tourist@example.com")
    member.post("/dashboard/tour/done")

    other_device = TestClient(app, follow_redirects=False)
    other_device.post("/login", data={"email": "tourist@example.com",
                                      "password": "pilot-season"})
    assert 'id="tour-data"' not in other_device.get("/dashboard").text


def test_the_tour_speaks_kannada(make_user):
    member = make_user()
    member.get("/lang/kn", params={"next": "/dashboard"})
    page = member.get("/dashboard")
    assert 'id="tour-data"' in page.text
    assert "ಸ್ವಾಗತ" in page.text                     # "Welcome."
    assert "ಮುಂದೆ" in page.text                      # the Next button


def test_the_tour_endpoint_needs_an_account(client):
    assert client.post("/dashboard/tour/done").status_code == 303


def test_every_tour_step_points_at_something_that_exists(make_user):
    """Each target selector must match an element the dashboard actually renders."""
    import json
    import re

    from app.tour import steps

    member = make_user()
    html = member.get("/dashboard").text
    for step in steps("en"):
        attr = re.match(r"\[data-tour='([a-z]+)'\]$", step["target"])
        assert attr, f"unexpected selector {step['target']}"
        assert f'data-tour="{attr.group(1)}"' in html, f"nothing carries {step['target']}"

    assert json.loads(re.search(
        r'<script id="tour-data" type="application/json">(.*?)</script>', html, re.S
    ).group(1))["steps"]



# --------------------------------------------------------------------------- #
# small spaces: a 30 by 40 site, a shed, a terrace
# --------------------------------------------------------------------------- #

def test_a_small_space_end_to_end(client, make_user):
    grower = make_user(roles=["grower"], district="Mysuru")
    investor = make_user(roles=["investor"])

    url = grower.post("/dashboard/projects/new", data=SPACE).headers["location"]
    page = client.get(url).text
    assert "Mushroom" in page and "1,200 sq ft" in page
    assert "Empty site with a tin shed" in page
    assert "1,80,000" in page              # 3,60,000 revenue less the 1,80,000 budget
    assert "1,08,000" in page              # investor side: 60% of that

    # it lives under Small spaces and Invest, and under none of the others
    assert SPACE["title"] in client.get("/spaces").text
    assert SPACE["title"] in client.get("/invest").text
    for elsewhere in ("/seasons", "/livestock", "/shares"):
        assert SPACE["title"] not in client.get(elsewhere).text, elsewhere

    assert "Interest recorded" in follow(
        investor, investor.post(f"{url}/pledge", data={"amount": "30000"})).text


def test_a_space_is_stored_in_acres_too(make_user):
    """Everything else on the site measures land in acres; keep that column honest."""
    grower = make_user(roles=["grower"])
    url = grower.post("/dashboard/projects/new", data=SPACE).headers["location"]
    with db.closing_conn(get_settings().db_path) as conn:
        project = db.project_by_id(conn, int(url.rsplit("/", 1)[-1]))
    assert project["area_sqft"] == 1200
    assert project["acres"] == pytest.approx(1200 / 43560, abs=1e-4)
    assert project["shed"] == "Empty site with a tin shed"
    assert project["cycle_months"] == 12


def test_a_space_needs_an_activity_and_a_sensible_area(make_user):
    grower = make_user(roles=["grower"])
    assert "What will it be used for" in grower.post(
        "/dashboard/projects/new", data={**SPACE, "activity": ""}).text
    assert "How big is the space" in grower.post(
        "/dashboard/projects/new", data={**SPACE, "area_sqft": ""}).text
    too_big = grower.post("/dashboard/projects/new", data={**SPACE, "area_sqft": "50000"})
    assert "up to one acre" in too_big.text


def test_a_space_can_be_edited_and_keeps_its_fields(client, make_user):
    grower = make_user(roles=["grower"])
    url = grower.post("/dashboard/projects/new", data=SPACE).headers["location"]
    project_id = url.rsplit("/", 1)[-1]

    form = grower.get(f"/dashboard/projects/{project_id}/edit").text
    assert "Empty site with a tin shed" in form      # the structure came back
    assert 'value="1200"' in form

    grower.post(f"/dashboard/projects/{project_id}/edit",
                data={**SPACE, "title": "Oyster mushrooms, second batch running"})
    assert "second batch running" in client.get(url).text


def test_search_finds_a_space_by_its_activity(client, make_user):
    grower = make_user(roles=["grower"])
    grower.post("/dashboard/projects/new", data=SPACE)
    assert SPACE["title"] in client.get("/invest", params={"query": "mushroom"}).text
    assert SPACE["title"] not in client.get("/invest", params={"query": "sheep"}).text
    assert SPACE["title"] in client.get("/spaces", params={"district": "Mysuru"}).text
    assert SPACE["title"] not in client.get("/spaces", params={"district": "Kodagu"}).text


def test_the_other_kinds_are_unaffected_by_the_new_columns(make_user):
    grower = make_user(roles=["grower"])
    for payload in (CROP, LIVESTOCK, SHARES):
        url = grower.post("/dashboard/projects/new", data=payload).headers["location"]
        project_id = int(url.rsplit("/", 1)[-1])
        with db.closing_conn(get_settings().db_path) as conn:
            project = db.project_by_id(conn, project_id)
        assert project["area_sqft"] == 0 and project["activity"] == ""


def test_the_home_page_lists_five_ways(client):
    page = client.get("/").text
    assert "Five ways to work land and space" in page
    assert 'href="/spaces"' in page


def test_small_space_is_in_kannada(client):
    client.get("/lang/kn", params={"next": "/spaces"})
    page = client.get("/spaces").text
    assert "ಸಣ್ಣ ಜಾಗ" in page
    assert "ಅಣಬೆ" in page                            # mushroom


# --------------------------------------------------------------------------- #
# schema: columns added after release, and a database that has never seen them
# --------------------------------------------------------------------------- #

def test_migrate_adds_new_columns_to_an_existing_database(tmp_path):
    """The live database holds real accounts, so a new column is added in place."""
    path = tmp_path / "old.sqlite3"
    with db.closing_conn(path) as conn:
        conn.execute("CREATE TABLE user (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("CREATE TABLE project (id INTEGER PRIMARY KEY, title TEXT)")
        conn.execute("INSERT INTO user (name) VALUES ('someone real')")
        conn.execute("INSERT INTO project (title) VALUES ('an old plan')")

        applied = db.migrate(conn)
        assert {"project.activity", "project.area_sqft", "user.tour_done"} <= set(applied)

        row = db.one(conn, "SELECT * FROM project")
        assert row["title"] == "an old plan"          # nothing was lost
        assert row["activity"] == "" and row["area_sqft"] == 0
        assert db.one(conn, "SELECT name FROM user")["name"] == "someone real"

        assert db.migrate(conn) == []                 # and a second run is a no-op


def test_the_seed_builds_a_fresh_database(tmp_path):
    """Nothing else exercises seed.py, and a new column once broke it silently."""
    from app import seed

    path = tmp_path / "fresh.sqlite3"
    db.init_db(path)
    assert seed.seed_if_empty(path) is True
    assert seed.seed_if_empty(path) is False          # only ever into an empty database

    with db.closing_conn(path) as conn:
        kinds = {r["kind"] for r in db.all_rows(conn, "SELECT kind FROM project")}
        assert kinds == {"crop", "livestock", "space", "shares"}
        space = db.one(conn, "SELECT * FROM project WHERE kind = 'space'")
        assert space["activity"] == "Mushroom" and space["area_sqft"] == 1200
