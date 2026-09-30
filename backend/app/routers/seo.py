"""robots.txt, sitemap.xml and a health check."""

from __future__ import annotations

import sqlite3
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from .. import content, db
from ..deps import conn_dep
from ..settings import get_settings

router = APIRouter()

# Public pages, most important first. Private areas are deliberately absent.
STATIC_PAGES: list[tuple[str, str, str]] = [
    ("/", "1.0", "weekly"),
    ("/earn", "0.9", "monthly"),
    ("/models", "0.9", "monthly"),
    ("/how-it-works", "0.8", "monthly"),
    ("/karnataka", "0.8", "weekly"),
    ("/stories", "0.7", "monthly"),
    ("/faq", "0.7", "monthly"),
    ("/fine-print", "0.6", "yearly"),
    ("/about", "0.5", "yearly"),
    ("/invest", "0.8", "daily"),
    ("/seasons", "0.6", "daily"),
    ("/livestock", "0.6", "daily"),
    ("/spaces", "0.6", "daily"),
    ("/shares", "0.6", "daily"),
    ("/land", "0.8", "daily"),
]


def _base(request: Request) -> str:
    return get_settings().site_url or f"{request.url.scheme}://{request.url.netloc}"


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots(request: Request) -> str:
    return "\n".join([
        "User-agent: *",
        "Allow: /",
        "Disallow: /dashboard",
        "Disallow: /admin",
        "Disallow: /api/",
        "Disallow: /login",
        "Disallow: /signup",
        "Disallow: /logout",
        "",
        f"Sitemap: {_base(request)}/sitemap.xml",
        "",
    ])


@router.get("/sitemap.xml")
def sitemap(request: Request, conn: sqlite3.Connection = Depends(conn_dep)) -> Response:
    base = _base(request)
    urls: list[tuple[str, str, str, str | None]] = [(p, prio, freq, None) for p, prio, freq in STATIC_PAGES]
    urls += [(f"/models/{slug}", "0.8", "monthly", None) for slug in content.ORDER]
    for row in db.search_projects(conn, status="open", limit=500):
        urls.append((f"/projects/{row['id']}", "0.6", "weekly", str(row["updated_at"])[:10]))
    for row in db.search_listings(conn, status="open", limit=500):
        urls.append((f"/land/{row['id']}", "0.6", "weekly", str(row["updated_at"])[:10]))

    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, prio, freq, lastmod in urls:
        body.append("<url>")
        body.append(f"<loc>{escape(base + path)}</loc>")
        if lastmod:
            body.append(f"<lastmod>{escape(lastmod)}</lastmod>")
        body.append(f"<changefreq>{freq}</changefreq><priority>{prio}</priority>")
        body.append("</url>")
    body.append("</urlset>")
    return Response("\n".join(body), media_type="application/xml")


@router.get("/healthz")
def healthz(conn: sqlite3.Connection = Depends(conn_dep)) -> JSONResponse:
    """For load balancers and uptime monitors: 200 only if the database answers."""
    try:
        conn.execute("SELECT 1").fetchone()
    except Exception:  # noqa: BLE001 - any failure means "not healthy"
        return JSONResponse({"ok": False, "db": "down"}, status_code=503)
    return JSONResponse({"ok": True, "db": "up"})
