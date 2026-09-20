"""Accounts: sign up, log in, log out, edit your profile."""

from __future__ import annotations

import re
import sqlite3

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from .. import db
from ..deps import conn_dep, require_user
from ..karnataka import is_district, normalise as normalise_district
from ..schemas import normalise_phone
from ..security import (
    ROLE_LABELS,
    ROLES,
    current_user,
    hash_password,
    login_session,
    logout_session,
    verify_password,
)
from ..templating import flash, render

router = APIRouter()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]+$")
ROLE_CHOICES = [(r, ROLE_LABELS[r]) for r in ROLES]


def _safe_next(value: str | None) -> str:
    """Only ever redirect inside this site."""
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return "/dashboard"


@router.get("/login")
def login_form(request: Request, next: str = "", user=Depends(current_user)):
    if user:
        return RedirectResponse(_safe_next(next), status_code=303)
    return render(request, "login.html", user=None, next=next, error=None, email="")


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(""),
    conn: sqlite3.Connection = Depends(conn_dep),
):
    user = db.user_by_email(conn, email.strip())
    if user is None or not verify_password(password, user["password_hash"]):
        return render(
            request, "login.html", user=None, next=next, email=email,
            error="That email and password do not match anything here.",
        )
    login_session(request, int(user["id"]))
    flash(request, f"Welcome back, {user['name'].split(' ')[0]}.")
    return RedirectResponse(_safe_next(next), status_code=303)


@router.post("/logout")
def logout(request: Request):
    logout_session(request)
    return RedirectResponse("/", status_code=303)


@router.get("/signup")
def signup_form(request: Request, next: str = "", user=Depends(current_user)):
    if user:
        return RedirectResponse(_safe_next(next), status_code=303)
    empty = {"name": "", "email": "", "phone": "", "district": "", "taluk": "", "roles": []}
    return render(request, "signup.html", user=None, next=next, error=None,
                  form=empty, roles=ROLE_CHOICES)


@router.post("/signup")
def signup(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    district: str = Form(""),
    taluk: str = Form(""),
    password: str = Form(...),
    password2: str = Form(...),
    roles: list[str] = Form(default=[]),
    next: str = Form(""),
    conn: sqlite3.Connection = Depends(conn_dep),
):
    form = {
        "name": name.strip(), "email": email.strip(), "phone": phone.strip(),
        "district": district.strip(), "taluk": taluk.strip(),
        "roles": [r for r in roles if r in ROLES],
    }

    def fail(message: str):
        return render(request, "signup.html", user=None, next=next, error=message,
                      form=form, roles=ROLE_CHOICES)

    if len(form["name"]) < 2:
        return fail("Give us your name as you would like us to say it.")
    if not EMAIL_RE.match(form["email"]):
        return fail("That email address does not look right.")
    try:
        phone_clean = normalise_phone(form["phone"])
    except ValueError as exc:
        return fail(str(exc))
    if len(password) < 8:
        return fail("Use a password of at least 8 characters.")
    if password != password2:
        return fail("The two passwords are different.")
    if not form["roles"]:
        return fail("Pick at least one side — you can change it later.")
    district_clean = normalise_district(form["district"])
    if district_clean is None:
        return fail("Pick your district from the list. Bhoomi Share covers Karnataka.")
    if db.user_by_email(conn, form["email"]):
        return fail("There is already an account on that email. Log in instead.")
    if db.user_by_phone(conn, phone_clean):
        return fail("There is already an account on that phone number.")

    user_id = db.create_user(
        conn,
        name=form["name"], email=form["email"], phone=phone_clean,
        password_hash=hash_password(password), roles=",".join(form["roles"]),
        district=district_clean, taluk=form["taluk"],
    )
    conn.commit()
    login_session(request, user_id)
    flash(request, "Account made. Nothing here takes money — read the fine print before you commit to anything.")
    return RedirectResponse(_safe_next(next), status_code=303)


@router.get("/dashboard/profile")
def profile_form(request: Request, user=Depends(require_user)):
    return render(request, "profile.html", user=user, roles=ROLE_CHOICES)


@router.post("/dashboard/profile")
def profile_save(
    request: Request,
    name: str = Form(...),
    district: str = Form(""),
    taluk: str = Form(""),
    roles: list[str] = Form(default=[]),
    user=Depends(require_user),
    conn: sqlite3.Connection = Depends(conn_dep),
):
    district_clean = normalise_district(district)
    if district_clean is None:
        flash(request, "Pick your district from the list.", "bad")
        return RedirectResponse("/dashboard/profile", status_code=303)

    db.update_profile(
        conn, int(user["id"]),
        name=name.strip() or user["name"],
        roles=",".join(r for r in roles if r in ROLES),
        district=district_clean, taluk=taluk.strip(),
    )
    conn.commit()
    flash(request, "Profile saved.")
    return RedirectResponse("/dashboard", status_code=303)
