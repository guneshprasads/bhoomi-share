"""Security headers, CSP nonces, caching, and the SEO/health endpoints."""

import re
import xml.etree.ElementTree as ET


def test_security_headers_on_every_page(client):
    r = client.get("/")
    h = r.headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["referrer-policy"]
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert "object-src 'none'" in h["content-security-policy"]
    # not on http://localhost: HSTS would lock the browser into https
    assert "strict-transport-security" not in h


def test_csp_nonce_matches_the_inline_scripts_and_changes_per_request(client):
    a, b = client.get("/earn"), client.get("/earn")
    nonce_a = re.search(r"'nonce-([\w-]+)'", a.headers["content-security-policy"]).group(1)
    nonce_b = re.search(r"'nonce-([\w-]+)'", b.headers["content-security-policy"]).group(1)
    assert nonce_a != nonce_b
    # every executable inline script carries this request's nonce
    for tag in re.findall(r"<script(?![^>]*\bsrc=)(?![^>]*type=)[^>]*>", a.text):
        assert f'nonce="{nonce_a}"' in tag, tag


def test_no_inline_event_handlers_remain(client, make_user):
    for path in ("/", "/earn", "/karnataka", "/how-it-works", "/login"):
        assert not re.search(r"\son\w+=\"", client.get(path).text), path


def test_csp_allows_the_map_tile_origin_but_not_arbitrary_images(client):
    csp = client.get("/karnataka").headers["content-security-policy"]
    assert "https://tile.openstreetmap.org" in csp
    assert "img-src 'self' data: blob: https://tile.openstreetmap.org" in csp


def test_versioned_static_is_cached_for_a_year_and_pages_revalidate(client):
    page = client.get("/earn").text
    href = re.search(r'href="(/static/earn\.css\?v=\d+)"', page).group(1)
    assert "immutable" in client.get(href).headers["cache-control"]
    assert client.get("/earn").headers["cache-control"] == "no-cache"


def test_robots_and_sitemap(client):
    robots = client.get("/robots.txt").text
    assert "Disallow: /admin" in robots and "Sitemap:" in robots
    root = ET.fromstring(client.get("/sitemap.xml").text)
    locs = [e.text for e in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert any(u.endswith("/models/crop-plans") for u in locs)
    assert any(u.endswith("/karnataka") for u in locs)
    assert not any("/dashboard" in u or "/admin" in u for u in locs)


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json() == {"ok": True, "db": "up"}


def test_unhandled_errors_do_not_leak_a_traceback(client):
    from app.main import app

    @app.get("/__boom")
    def boom():  # pragma: no cover - raising is the point
        raise RuntimeError("secret detail")

    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/__boom")
    assert r.status_code == 500
    assert "secret detail" not in r.text and "Traceback" not in r.text
