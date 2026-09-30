"""Response hardening: security headers, a per-request CSP nonce, and caching.

One small pure-ASGI middleware, so it adds no per-request buffering and sits
outside everything else. What it sets:

  * Content-Security-Policy with a fresh nonce for every request. No inline
    script runs without that nonce, and inline event handlers are not allowed at
    all; the pages use data attributes and site.js instead.
  * X-Content-Type-Options, Referrer-Policy, Permissions-Policy,
    Cross-Origin-Opener-Policy, X-Frame-Options (and frame-ancestors).
  * Strict-Transport-Security, but only when the site is configured for HTTPS
    (BHOOMI_COOKIE_SECURE=1), so a laptop on http://localhost is not locked in.
  * Cache-Control: versioned static files are cached for a year and marked
    immutable, uploads for a day, everything else must revalidate.
"""

from __future__ import annotations

import secrets
from urllib.parse import urlsplit

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Swagger UI (/api/docs) loads its assets from a CDN, which a strict policy would
# block. It is a developer tool, so it is left out of the policy rather than the
# policy being loosened for the whole site.
CSP_EXEMPT_PREFIXES = ("/api/docs", "/api/openapi.json")


def _origin(url: str) -> str | None:
    """'https://{s}.tile.example/{z}/{x}/{y}.png' -> 'https://*.tile.example'."""
    parts = urlsplit(url.replace("{s}", "wildcard"))
    if not parts.scheme or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc.replace('wildcard', '*')}"


def build_csp(nonce: str, tile_url: str, frame_ancestors: tuple[str, ...] = ()) -> str:
    tile_origin = _origin(tile_url)
    img = ["'self'", "data:", "blob:"] + ([tile_origin] if tile_origin else [])
    return "; ".join([
        "default-src 'self'",
        f"script-src 'self' 'nonce-{nonce}'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src " + " ".join(img),
        "connect-src 'self'",
        "frame-ancestors " + (" ".join(frame_ancestors) if frame_ancestors else "'none'"),
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ])


class Hardening:
    def __init__(self, app: ASGIApp, *, tile_url: str, hsts: bool,
                 frame_ancestors: tuple[str, ...] = (), allowed_origins: tuple[str, ...] = ()) -> None:
        self.app = app
        self.tile_url = tile_url
        self.hsts = hsts
        self.frame_ancestors = frame_ancestors
        self.allowed_origins = allowed_origins

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope["path"]

        # Cross-site request forgery: a browser always sends Origin on a form or
        # fetch POST, so a state-changing request whose Origin is some other site
        # is refused. (No Origin header, as from curl or the test client, is not a
        # browser, and session cookies are SameSite=Lax as a second line.)
        if scope["method"] in ("POST", "PUT", "PATCH", "DELETE"):
            headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
            origin = headers.get("origin")
            hosts = {headers.get("host", ""), headers.get("x-forwarded-host", "").split(",")[0].strip()}
            if origin and origin != "null" and urlsplit(origin).netloc not in hosts \
                    and origin not in self.allowed_origins:
                body = b"Cross-site request refused."
                await send({"type": "http.response.start", "status": 403,
                            "headers": [(b"content-type", b"text/plain; charset=utf-8"),
                                        (b"content-length", str(len(body)).encode())]})
                await send({"type": "http.response.body", "body": body})
                return

        nonce = secrets.token_urlsafe(16)
        scope.setdefault("state", {})["csp_nonce"] = nonce
        has_version = b"v=" in scope.get("query_string", b"")

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                h = MutableHeaders(scope=message)
                h["X-Content-Type-Options"] = "nosniff"
                h["Referrer-Policy"] = "strict-origin-when-cross-origin"
                h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
                h["Cross-Origin-Opener-Policy"] = "same-origin"
                if not self.frame_ancestors:
                    h["X-Frame-Options"] = "DENY"
                if self.hsts:
                    h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
                if not path.startswith(CSP_EXEMPT_PREFIXES):
                    h["Content-Security-Policy"] = build_csp(nonce, self.tile_url, self.frame_ancestors)

                if "cache-control" not in h:
                    if path.startswith("/static/"):
                        h["Cache-Control"] = (
                            "public, max-age=31536000, immutable" if has_version
                            else "public, max-age=86400"
                        )
                    elif path.startswith("/uploads/"):
                        h["Cache-Control"] = "public, max-age=86400"
                    else:
                        h["Cache-Control"] = "no-cache"
            await send(message)

        await self.app(scope, receive, send_wrapper)
