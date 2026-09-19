"""Bhoomi Share.

A landing page, a land-leasing marketplace, and season plans people can read and
register interest in. No money moves through this service and no land agreement
is executed by it; that waits on counsel's review of the structure.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import db, seed
from .deps import Forbidden, LoginRequired, NotFound
from .routers import admin_pages, api, auth, dashboard, land, pages, seasons
from .schemas import ErrorOut
from .security import current_user
from .settings import get_settings
from .templating import render

log = logging.getLogger("bhoomi")
settings = get_settings()

FIELD_LABELS = {
    "name": "name",
    "phone": "phone number",
    "role": "which side you are on",
    "place": "district and state",
}

LENGTH_MESSAGES = {
    "name": "Give us your name as you would like us to say it.",
    "phone": "Enter a 10-digit Indian mobile number.",
    "place": "Which district and state? For example: Belagavi, Karnataka.",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db(settings.db_path)
    if settings.seed_demo:
        seed.seed_if_empty(settings.db_path)
    if settings.secret_key_is_ephemeral:
        log.warning("BHOOMI_SECRET_KEY is not set: sessions end when this process does.")
    yield


app = FastAPI(
    title="Bhoomi Share",
    description="Season plans, farmland listings, and a waitlist. Pre-launch; nothing here takes money.",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="bhoomi_session",
    same_site="lax",
    https_only=settings.cookie_secure,
    max_age=60 * 60 * 24 * 30,
)

if settings.allowed_origins:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

for router in (pages.router, auth.router, land.router, seasons.router,
               dashboard.router, admin_pages.router, api.router):
    app.include_router(router)


# --------------------------------------------------------------------------- #
# errors
# --------------------------------------------------------------------------- #

def _wants_json(request: Request) -> bool:
    return request.url.path.startswith("/api")


def _error_page(request: Request, code: int, headline: str, message: str):
    return render(
        request, "error.html", user=current_user(request, settings),
        code=code, headline=headline, message=message,
        status_code=code,
    )


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(f"/login?next={quote(exc.next_url)}", status_code=303)


@app.exception_handler(Forbidden)
async def forbidden_handler(request: Request, exc: Forbidden):
    return _error_page(request, 403, "That is not yours to open.", exc.message)


@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound):
    return _error_page(request, 404, "Nothing here.", exc.message)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    if _wants_json(request):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorOut(error=str(exc.detail)).model_dump(),
            headers=getattr(exc, "headers", None),
        )
    if exc.status_code == 404:
        return _error_page(
            request, 404, "Nothing here.",
            "That page does not exist. The parcel or plan may also have been taken down.",
        )
    return _error_page(request, exc.status_code, "That did not work.", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    """Return something a person can read; the landing page prints it verbatim."""
    fields: dict[str, str] = {}
    for err in exc.errors():
        loc = [p for p in err["loc"] if p != "body"]
        key = str(loc[0]) if loc else "form"
        msg = err.get("msg", "Invalid value")
        err_type = err.get("type", "")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        elif err_type == "missing":
            msg = f"We need your {FIELD_LABELS.get(key, key)}."
        elif err_type.startswith("string_too_"):
            msg = LENGTH_MESSAGES.get(key, f"Check the {FIELD_LABELS.get(key, key)}.")
        elif key == "role":
            msg = "Pick investor, grower, landowner or farmer."
        fields.setdefault(key, msg)

    first = next(iter(fields.values()), "Check the form and try again.")
    if _wants_json(request):
        return JSONResponse(
            status_code=422,
            content=ErrorOut(error=first, fields=fields).model_dump(),
        )
    return _error_page(request, status.HTTP_400_BAD_REQUEST, "Check that form.", first)
