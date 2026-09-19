from app import db
from app.settings import get_settings
from tests.conftest import ADMIN


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "admin_configured": True}


def test_join(client, entry):
    r = client.post("/api/waitlist", json=entry)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "joined"
    assert "Gunesh" in body["message"]
    assert "Belagavi" in body["message"]


def test_phone_is_normalised(client, entry):
    client.post("/api/waitlist", json={**entry, "phone": "+91 98765 43210"})
    with db.closing_conn(get_settings().db_path) as conn:
        rows = db.list_waitlist(conn)
    assert [r["phone"] for r in rows] == ["9876543210"]


def test_repeat_number_updates_instead_of_duplicating(client, entry):
    client.post("/api/waitlist", json=entry)
    r = client.post("/api/waitlist", json={**entry, "role": "Landowner", "place": "Satara, Maharashtra"})
    assert r.status_code == 201
    assert r.json()["status"] == "updated"

    with db.closing_conn(get_settings().db_path) as conn:
        rows = db.list_waitlist(conn)
    assert len(rows) == 1
    assert rows[0]["role"] == "Landowner"
    assert rows[0]["place"] == "Satara, Maharashtra"


def test_bad_phone_is_readable(client, entry):
    r = client.post("/api/waitlist", json={**entry, "phone": "12345"})
    assert r.status_code == 422
    body = r.json()
    assert "10-digit" in body["error"]
    assert "phone" in body["fields"]


def test_landline_prefix_rejected(client, entry):
    r = client.post("/api/waitlist", json={**entry, "phone": "0223456789"})
    assert r.status_code == 422
    assert "6, 7, 8 or 9" in r.json()["fields"]["phone"]


def test_missing_role(client, entry):
    payload = {k: v for k, v in entry.items() if k != "role"}
    r = client.post("/api/waitlist", json=payload)
    assert r.status_code == 422
    assert "role" in r.json()["fields"]


def test_unknown_role_rejected(client, entry):
    r = client.post("/api/waitlist", json={**entry, "role": "Broker"})
    assert r.status_code == 422


def test_url_in_name_rejected(client, entry):
    r = client.post("/api/waitlist", json={**entry, "name": "buy now https://spam.example"})
    assert r.status_code == 422


def test_honeypot_is_silently_dropped(client, entry):
    r = client.post("/api/waitlist", json={**entry, "company": "Acme"})
    assert r.status_code == 201
    assert r.json()["status"] == "ignored"
    with db.closing_conn(get_settings().db_path) as conn:
        assert db.list_waitlist(conn) == []


def test_rate_limit(client, entry):
    limit = get_settings().rate_limit_per_hour
    for i in range(limit):
        r = client.post("/api/waitlist", json={**entry, "phone": f"98765432{i:02d}"})
        assert r.status_code == 201
    r = client.post("/api/waitlist", json={**entry, "phone": "9000000000"})
    assert r.status_code == 429
    assert "hour" in r.json()["error"]


def test_admin_requires_token(client, entry):
    client.post("/api/waitlist", json=entry)
    assert client.get("/api/admin/waitlist").status_code == 401
    assert client.get("/api/admin/waitlist", headers={"X-Admin-Token": "wrong"}).status_code == 401


def test_admin_list_and_filter(client, entry):
    client.post("/api/waitlist", json=entry)
    client.post("/api/waitlist", json={**entry, "phone": "9123456780", "role": "Farmer", "name": "Asha Patil"})

    r = client.get("/api/admin/waitlist", headers=ADMIN)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["by_role"] == {"Investor": 1, "Farmer": 1}

    r = client.get("/api/admin/waitlist", params={"role": "Farmer"}, headers=ADMIN)
    assert [e["name"] for e in r.json()["entries"]] == ["Asha Patil"]


def test_admin_csv(client, entry):
    client.post("/api/waitlist", json=entry)
    r = client.get("/api/admin/waitlist.csv", headers=ADMIN)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0] == "name,phone,role,district_state,created_at,updated_at"
    assert "9876543210" in lines[1]


def test_admin_delete(client, entry):
    client.post("/api/waitlist", json=entry)
    with db.closing_conn(get_settings().db_path) as conn:
        entry_id = db.list_waitlist(conn)[0]["id"]

    assert client.delete(f"/api/admin/waitlist/{entry_id}", headers=ADMIN).status_code == 204
    assert client.delete(f"/api/admin/waitlist/{entry_id}", headers=ADMIN).status_code == 404
    with db.closing_conn(get_settings().db_path) as conn:
        assert db.list_waitlist(conn) == []
