import os
import tempfile
from pathlib import Path

import pytest

TMP = Path(tempfile.mkdtemp(prefix="bhoomi-test-"))

# Settings are read once at import time, so the environment has to be right
# before anything imports the app.
os.environ["BHOOMI_DB"] = str(TMP / "test.sqlite3")
# Run the same suite against Postgres by setting BHOOMI_TEST_DATABASE_URL, e.g.
#   docker run -d -p 54329:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=bhoomi_test postgres:16-alpine
#   BHOOMI_TEST_DATABASE_URL=postgresql://postgres:test@localhost:54329/bhoomi_test pytest
_pg = os.environ.get("BHOOMI_TEST_DATABASE_URL")
os.environ.pop("DATABASE_URL", None)
os.environ.pop("BHOOMI_DATABASE_URL", None)
if _pg:
    os.environ["BHOOMI_DATABASE_URL"] = _pg
os.environ["BHOOMI_UPLOADS"] = str(TMP / "uploads")
os.environ["BHOOMI_ADMIN_TOKEN"] = "test-token"
os.environ["BHOOMI_IP_SALT"] = "test-salt"
os.environ["BHOOMI_RATE_LIMIT"] = "5"
os.environ["BHOOMI_SEED_DEMO"] = "0"
os.environ["BHOOMI_SECRET_KEY"] = "test-secret-key"
os.environ["BHOOMI_PHOTOS_IN_DB"] = "1"        # exercise the database-backed photo path on both backends

from fastapi.testclient import TestClient  # noqa: E402

from app import db  # noqa: E402
from app.main import app  # noqa: E402
from app.settings import get_settings  # noqa: E402

ADMIN = {"X-Admin-Token": "test-token"}

TABLES = ("pledge", "project_update", "project", "inquiry", "photo", "listing",
          "user", "waitlist", "submission")


@pytest.fixture()
def client():
    settings = get_settings()
    db.init_db(settings.db_target)
    with db.closing_conn(settings.db_target) as conn:
        if db.is_postgres(settings.db_target):
            conn.execute('TRUNCATE "user", listing, inquiry, project, pledge, project_update, '
                         'photo, waitlist, submission RESTART IDENTITY CASCADE')
        else:
            for table in TABLES:
                conn.execute(f"DELETE FROM {table}")
                conn.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
        conn.commit()
    # Redirects are followed explicitly, via follow(), so that Set-Cookie on a
    # 303 is honoured the way a browser honours it.
    with TestClient(app, follow_redirects=False) as c:
        yield c


@pytest.fixture()
def entry():
    return {
        "name": "Gunesh Prasad",
        "phone": "9876543210",
        "role": "Investor",
        "place": "Belagavi, Karnataka",
    }


@pytest.fixture()
def make_user(client):
    """Register an account and return a client logged in as them."""
    counter = {"n": 0}

    def _make(**over):
        counter["n"] += 1
        n = counter["n"]
        data = {
            "name": over.get("name", f"Test Person {n}"),
            "email": over.get("email", f"person{n}@example.com"),
            "phone": over.get("phone", f"98765{n:05d}"),
            "district": over.get("district", "Belagavi"),
            "taluk": over.get("taluk", "Chikkodi"),
            "password": over.get("password", "pilot-season"),
            "password2": over.get("password2", over.get("password", "pilot-season")),
            "roles": over.get("roles", ["farmer"]),
        }
        c = TestClient(app, follow_redirects=False)
        r = c.post("/signup", data=data, follow_redirects=False)
        assert r.status_code == 303, r.text[:400]
        return c

    return _make


def follow(client, response):
    """POST-then-GET, the way a browser handles a 303.

    httpx reuses the original request's headers when it follows a redirect, so
    a session cookie set on the redirect itself would be dropped — and flash
    messages live in that cookie.
    """
    assert response.status_code == 303, response.text[:400]
    return client.get(response.headers["location"])


def png_bytes(width: int = 40, height: int = 30, gps: bool = False) -> bytes:
    """A small real image, optionally carrying EXIF with GPS in it."""
    import io

    from PIL import Image

    image = Image.new("RGB", (width, height), (90, 120, 60))
    buf = io.BytesIO()
    if gps:
        exif = Image.Exif()
        exif[0x8825] = {1: "N", 2: (15.0, 51.0, 0.0), 3: "E", 4: (74.0, 30.0, 0.0)}
        exif[0x010F] = "TestPhone"
        image.save(buf, "JPEG", exif=exif)
    else:
        image.save(buf, "PNG")
    return buf.getvalue()
