"""Jinja setup: one render() helper that every page route uses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .i18n import COOKIE, DEFAULT_LANG, LANG_NAMES, LANGS, normalise_lang
from .i18n import t as translate
from .karnataka import DISTRICTS, DIVISIONS, STATE
from .security import ROLE_LABELS, role_list
from .settings import get_settings

templates = Jinja2Templates(directory=str(get_settings().templates_dir))

# Without this, `| tojson` renders every Kannada character as \uXXXX — valid, but
# it triples the size of the tour payload and makes the page source unreadable.
# htmlsafe_json_dumps still escapes <, > and & either way.
templates.env.policies["json.dumps_kwargs"] = {"ensure_ascii": False, "sort_keys": False}


def inr(value: Any) -> str:
    """Indian digit grouping: 1234567 -> 12,34,567."""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return "—"
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) <= 3:
        return sign + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return sign + ",".join(parts) + "," + tail


def acres(value: Any) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{f:.2f}".rstrip("0").rstrip(".") + " ac"


def short_date(value: Any) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value)).strftime("%d %b %Y")
    except ValueError:
        return str(value)[:10]


def photo_url(path: str | None) -> str:
    return f"/uploads/{path}" if path else ""


def current_lang(request: Request) -> str:
    """?lang= wins for this request; otherwise whatever the cookie remembers."""
    asked = request.query_params.get("lang")
    if asked in LANGS:
        return asked
    return normalise_lang(request.cookies.get(COOKIE))


def flash(request: Request, message: str, kind: str = "good") -> None:
    """Queue a message for the next page this person loads.

    Assigning a new list matters: Starlette's session only notices changes made
    through __setitem__, so appending in place would never reach the cookie.
    """
    queued = list(request.session.get("flash", []))
    queued.append({"message": message, "kind": kind})
    request.session["flash"] = queued


def _take_flash(request: Request) -> list[dict[str, str]]:
    messages = request.session.pop("flash", [])
    return list(messages)


templates.env.globals.update(
    inr=inr,
    acres=acres,
    short_date=short_date,
    photo_url=photo_url,
    role_labels=ROLE_LABELS,
    role_list=role_list,
    districts=DISTRICTS,
    divisions=DIVISIONS,
    state=STATE,
    lang_names=LANG_NAMES,
    langs=LANGS,
    site_name="Bhoomi Share",
)


def render(
    request: Request,
    name: str,
    user: Any = None,
    status_code: int = 200,
    **context: Any,
) -> HTMLResponse:
    lang = current_lang(request)
    ctx = {
        "request": request,
        "user": user,
        "lang": lang,
        "t": lambda key, **kw: translate(key, lang, **kw),
        "flashes": _take_flash(request),
        "now": datetime.now(),
        **context,
    }
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
