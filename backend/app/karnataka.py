"""Karnataka districts.

The site covers one state, so the district is a choice from a list rather than a
box people type into — it makes search work and stops "Belgaum" and "Belagavi"
being two different places.
"""

from __future__ import annotations

# 31 districts, in their four revenue divisions.
DIVISIONS: dict[str, tuple[str, ...]] = {
    "Belagavi": (
        "Bagalkote", "Belagavi", "Dharwad", "Gadag", "Haveri",
        "Uttara Kannada", "Vijayapura",
    ),
    "Bengaluru": (
        "Bengaluru Urban", "Bengaluru North", "Bengaluru South",
        "Chikkaballapura", "Chitradurga", "Davanagere", "Kolar",
        "Shivamogga", "Tumakuru",
    ),
    "Kalaburagi": (
        "Ballari", "Bidar", "Kalaburagi", "Koppal", "Raichur",
        "Vijayanagara", "Yadgir",
    ),
    "Mysuru": (
        "Chamarajanagara", "Chikkamagaluru", "Dakshina Kannada", "Hassan",
        "Kodagu", "Mandya", "Mysuru", "Udupi",
    ),
}

DISTRICTS: tuple[str, ...] = tuple(
    sorted(d for districts in DIVISIONS.values() for d in districts)
)

DIVISION_OF: dict[str, str] = {
    d: division for division, districts in DIVISIONS.items() for d in districts
}

# Old names people still use, and names that predate the 2014 renamings.
# Bengaluru Rural and Ramanagara were renamed in 2025; everyone still says both.
ALIASES: dict[str, str] = {
    "bengaluru rural": "Bengaluru North",
    "bangalore rural": "Bengaluru North",
    "ramanagara": "Bengaluru South",
    "ramanagaram": "Bengaluru South",
    "bangalore": "Bengaluru Urban",
    "bangalore urban": "Bengaluru Urban",
    "bengaluru": "Bengaluru Urban",
    "belgaum": "Belagavi",
    "bellary": "Ballari",
    "bijapur": "Vijayapura",
    "gulbarga": "Kalaburagi",
    "mysore": "Mysuru",
    "shimoga": "Shivamogga",
    "tumkur": "Tumakuru",
    "chikmagalur": "Chikkamagaluru",
    "chickmagalur": "Chikkamagaluru",
    "bagalkot": "Bagalkote",
    "chamarajanagar": "Chamarajanagara",
    "chikballapur": "Chikkaballapura",
    "chikkaballapur": "Chikkaballapura",
    "mangalore": "Dakshina Kannada",
    "karwar": "Uttara Kannada",
    "hospet": "Vijayanagara",
}

_LOOKUP = {d.lower(): d for d in DISTRICTS} | ALIASES

STATE = "Karnataka"


def normalise(value: str | None) -> str | None:
    """Return the canonical district name, or None if it isn't one.

    Accepts old names — someone searching "Ramanagara" means Bengaluru South.
    """
    if not value:
        return None
    return _LOOKUP.get(value.strip().lower())


def is_district(value: str | None) -> bool:
    return normalise(value) is not None
