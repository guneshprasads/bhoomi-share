"""Request and response shapes, plus the validation rules that matter here."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

DIGITS = re.compile(r"\D+")


class Role(str, Enum):
    investor = "Investor"
    grower = "Grower"
    landowner = "Landowner"
    farmer = "Farmer"


def normalise_phone(raw: str) -> str:
    """Reduce an Indian mobile number to its ten digits.

    Accepts +91, 0091, a leading 0, and any spacing or dashes people type.
    """
    digits = DIGITS.sub("", raw or "")
    if digits.startswith("0091"):
        digits = digits[4:]
    elif len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    if len(digits) != 10:
        raise ValueError("Enter a 10-digit Indian mobile number.")
    if digits[0] not in "6789":
        raise ValueError("An Indian mobile number starts with 6, 7, 8 or 9.")
    return digits


class WaitlistIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(max_length=24)
    role: Role
    place: str = Field(min_length=2, max_length=120)
    # Honeypot: the form renders this off-screen, so only a bot fills it in.
    company: str = ""

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalise_phone(v)

    @field_validator("name", "place")
    @classmethod
    def _no_urls(cls, v: str) -> str:
        if "http://" in v.lower() or "https://" in v.lower():
            raise ValueError("That does not look like a name or a place.")
        return v


class WaitlistOut(BaseModel):
    status: str  # joined | updated | ignored
    message: str


class WaitlistEntry(BaseModel):
    id: int
    name: str
    phone: str
    role: Role
    place: str
    created_at: str
    updated_at: str


class WaitlistPage(BaseModel):
    total: int
    by_role: dict[str, int]
    entries: list[WaitlistEntry]


class ErrorOut(BaseModel):
    error: str
    fields: dict[str, str] = {}
