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


# --------------------------------------------------------------------------- #
# the map page
# --------------------------------------------------------------------------- #

# Kannada names for the 31 districts.
DISTRICTS_KN: dict[str, str] = {
    "Bagalkote": "ಬಾಗಲಕೋಟೆ", "Belagavi": "ಬೆಳಗಾವಿ", "Dharwad": "ಧಾರವಾಡ", "Gadag": "ಗದಗ",
    "Haveri": "ಹಾವೇರಿ", "Uttara Kannada": "ಉತ್ತರ ಕನ್ನಡ", "Vijayapura": "ವಿಜಯಪುರ",
    "Bengaluru Urban": "ಬೆಂಗಳೂರು ನಗರ", "Bengaluru North": "ಬೆಂಗಳೂರು ಉತ್ತರ",
    "Bengaluru South": "ಬೆಂಗಳೂರು ದಕ್ಷಿಣ", "Chikkaballapura": "ಚಿಕ್ಕಬಳ್ಳಾಪುರ",
    "Chitradurga": "ಚಿತ್ರದುರ್ಗ", "Davanagere": "ದಾವಣಗೆರೆ", "Kolar": "ಕೋಲಾರ",
    "Shivamogga": "ಶಿವಮೊಗ್ಗ", "Tumakuru": "ತುಮಕೂರು", "Ballari": "ಬಳ್ಳಾರಿ", "Bidar": "ಬೀದರ್",
    "Kalaburagi": "ಕಲಬುರಗಿ", "Koppal": "ಕೊಪ್ಪಳ", "Raichur": "ರಾಯಚೂರು",
    "Vijayanagara": "ವಿಜಯನಗರ", "Yadgir": "ಯಾದಗಿರಿ", "Chamarajanagara": "ಚಾಮರಾಜನಗರ",
    "Chikkamagaluru": "ಚಿಕ್ಕಮಗಳೂರು", "Dakshina Kannada": "ದಕ್ಷಿಣ ಕನ್ನಡ", "Hassan": "ಹಾಸನ",
    "Kodagu": "ಕೊಡಗು", "Mandya": "ಮಂಡ್ಯ", "Mysuru": "ಮೈಸೂರು", "Udupi": "ಉಡುಪಿ",
}

# A tile cartogram: each district is one equal tile, placed roughly where it sits
# on the map (north at the top, the coast at the left). (column, row), from 0.
# It is a diagram, not a map; areas are deliberately not to scale.
TILE_POS: dict[str, tuple[int, int]] = {
    "Vijayapura": (3, 0), "Kalaburagi": (5, 0), "Bidar": (6, 0),
    "Belagavi": (2, 1), "Bagalkote": (3, 1), "Raichur": (4, 1), "Yadgir": (5, 1),
    "Uttara Kannada": (1, 2), "Dharwad": (2, 2), "Gadag": (3, 2), "Koppal": (4, 2), "Ballari": (5, 2),
    "Udupi": (1, 3), "Haveri": (2, 3), "Davanagere": (3, 3), "Vijayanagara": (4, 3), "Chitradurga": (5, 3),
    "Dakshina Kannada": (1, 4), "Shivamogga": (2, 4), "Chikkamagaluru": (3, 4),
    "Tumakuru": (4, 4), "Chikkaballapura": (5, 4), "Kolar": (6, 4),
    "Hassan": (3, 5), "Mandya": (4, 5), "Bengaluru North": (5, 5), "Bengaluru Urban": (6, 5),
    "Kodagu": (2, 6), "Mysuru": (3, 6), "Chamarajanagara": (4, 6), "Bengaluru South": (5, 6),
}

# What is commonly grown, by division. General background to orient a reader,
# not advice and not a yield claim: local conditions vary a great deal inside a
# division, and a plan states its own crop.
DIVISION_NOTES: dict[str, dict[str, str]] = {
    "Belagavi": {
        "crops": "Sugarcane, cotton, jowar, maize, groundnut, pulses",
        "note": "Mostly dryland and canal-irrigated black-soil country in the north-west, with the coast and ghats to the west. Our pilot is here.",
    },
    "Bengaluru": {
        "crops": "Ragi, vegetables, flowers, sericulture, arecanut, pulses",
        "note": "Small holdings near a very large city, good for short cycles and produce that sells fresh.",
    },
    "Kalaburagi": {
        "crops": "Tur (pigeon pea), jowar, bengal gram, cotton, sunflower",
        "note": "The north-east: drier, with a strong pulse tradition. Water is the thing to check first.",
    },
    "Mysuru": {
        "crops": "Coffee, arecanut, paddy, sugarcane, spices, ragi",
        "note": "Plantation hills and the Cauvery basin, with more reliable water than much of the state.",
    },
}

PILOT_DISTRICT = "Belagavi"
