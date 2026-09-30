"""Photographs survive a host that wipes its disk (BHOOMI_PHOTOS_IN_DB)."""

from app import db
from app.settings import get_settings

from .test_site import LISTING, png_bytes


def _listing_with_photo(make_user):
    owner = make_user(roles=["landowner"])
    url = owner.post("/dashboard/listings/new", data=LISTING,
                     files=[("photos", ("a.png", png_bytes(), "image/png"))]).headers["location"]
    listing_id = int(url.rsplit("/", 1)[-1])
    with db.closing_conn(get_settings().db_target) as conn:
        photo = db.photos_for(conn, "listing", listing_id)[0]
    return owner, listing_id, photo


def test_photo_bytes_are_stored_in_the_database(make_user):
    _owner, _lid, photo = _listing_with_photo(make_user)
    with db.closing_conn(get_settings().db_target) as conn:
        data = db.get_blob(conn, photo["path"])
    assert data and data[:2] == b"\xff\xd8"            # a JPEG


def test_a_wiped_disk_is_served_from_the_database_and_rebuilt(client, make_user):
    _owner, _lid, photo = _listing_with_photo(make_user)
    on_disk = get_settings().uploads_dir / photo["path"]
    on_disk.unlink()                                   # the host redeployed
    r = client.get(f"/uploads/{photo['path']}")
    assert r.status_code == 200 and r.content[:2] == b"\xff\xd8"
    assert on_disk.exists(), "the cache copy should be written back"


def test_removing_a_photo_removes_its_bytes(make_user):
    owner, lid, photo = _listing_with_photo(make_user)
    owner.post(f"/dashboard/listings/{lid}/photos/{photo['id']}/delete")
    with db.closing_conn(get_settings().db_target) as conn:
        assert db.get_blob(conn, photo["path"]) is None


def test_deleting_a_listing_removes_its_photo_bytes(make_user):
    owner, lid, photo = _listing_with_photo(make_user)
    owner.post(f"/dashboard/listings/{lid}/delete")
    with db.closing_conn(get_settings().db_target) as conn:
        assert db.get_blob(conn, photo["path"]) is None


def test_path_traversal_is_refused(client):
    for bad in ("../bhoomi.sqlite3", "..%2f..%2fsecret", "listing/../../etc/passwd"):
        assert client.get(f"/uploads/{bad}").status_code == 404
    assert client.get("/uploads/listing/nope.jpg").status_code == 404
