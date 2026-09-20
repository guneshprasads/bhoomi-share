"""English and Kannada.

A dictionary, not gettext: no compile step, no .po files, and a translator can
read the whole thing in one file. Short strings live here; long prose lives in
the templates behind `{% if lang == 'kn' %}`, because a paragraph of legal
argument is easier to keep honest as a paragraph than as forty fragments.

Anything a person typed themselves — a listing's notes, a season log — is shown
as they wrote it and never translated.
"""

from __future__ import annotations

LANGS = ("en", "kn")
LANG_NAMES = {"en": "English", "kn": "ಕನ್ನಡ"}
DEFAULT_LANG = "en"
COOKIE = "bhoomi_lang"

STRINGS: dict[str, dict[str, str]] = {
    # --- navigation and account -------------------------------------------
    "nav.invest": {"en": "Invest", "kn": "ಹೂಡಿಕೆ"},
    "nav.crop": {"en": "Crop plans", "kn": "ಬೆಳೆ ಯೋಜನೆಗಳು"},
    "nav.livestock": {"en": "Livestock", "kn": "ಜಾನುವಾರು"},
    "nav.shares": {"en": "Land shares", "kn": "ಭೂಮಿ ಪಾಲುಗಳು"},
    "nav.land": {"en": "Land on offer", "kn": "ಲಭ್ಯವಿರುವ ಭೂಮಿ"},
    "nav.how": {"en": "How it works", "kn": "ಇದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ"},
    "nav.fineprint": {"en": "The fine print", "kn": "ಕಾನೂನು ವಿವರ"},
    "nav.dashboard": {"en": "Dashboard", "kn": "ನನ್ನ ಪುಟ"},
    "nav.admin": {"en": "Admin", "kn": "ನಿರ್ವಹಣೆ"},
    "auth.login": {"en": "Log in", "kn": "ಲಾಗಿನ್"},
    "auth.logout": {"en": "Log out", "kn": "ಲಾಗ್ ಔಟ್"},
    "auth.signup": {"en": "Create an account", "kn": "ಖಾತೆ ತೆರೆಯಿರಿ"},
    "auth.signed_in_as": {"en": "Signed in as", "kn": "ಲಾಗಿನ್ ಆಗಿರುವವರು"},
    "auth.have_account": {"en": "I already have one", "kn": "ನನ್ನ ಖಾತೆ ಇದೆ"},
    "auth.email": {"en": "Email", "kn": "ಇಮೇಲ್"},
    "auth.password": {"en": "Password", "kn": "ಪಾಸ್‌ವರ್ಡ್"},
    "auth.password_again": {"en": "Again", "kn": "ಮತ್ತೊಮ್ಮೆ"},

    # --- common fields ------------------------------------------------------
    "field.name": {"en": "Name", "kn": "ಹೆಸರು"},
    "field.phone": {"en": "Phone", "kn": "ಫೋನ್"},
    "field.district": {"en": "District", "kn": "ಜಿಲ್ಲೆ"},
    "field.taluk": {"en": "Taluk", "kn": "ತಾಲೂಕು"},
    "field.acres": {"en": "Size (acres)", "kn": "ವಿಸ್ತೀರ್ಣ (ಎಕರೆ)"},
    "field.survey_no": {"en": "Survey number", "kn": "ಸರ್ವೆ ನಂಬರ್"},
    "field.water": {"en": "Water", "kn": "ನೀರು"},
    "field.soil": {"en": "Soil", "kn": "ಮಣ್ಣು"},
    "field.crop": {"en": "Crop", "kn": "ಬೆಳೆ"},
    "field.crops_grown": {"en": "What can be grown here", "kn": "ಇಲ್ಲಿ ಏನು ಬೆಳೆಯಬಹುದು"},
    "field.animal": {"en": "Animal", "kn": "ಪ್ರಾಣಿ"},
    "field.budget": {"en": "Budget", "kn": "ಬಂಡವಾಳ"},
    "field.term": {"en": "Term", "kn": "ಅವಧಿ"},
    "field.rent": {"en": "Rent", "kn": "ಬಾಡಿಗೆ"},
    "field.optional": {"en": "optional", "kn": "ಐಚ್ಛಿಕ"},
    "field.photos": {"en": "Photographs", "kn": "ಫೋಟೋಗಳು"},
    "field.months": {"en": "months", "kn": "ತಿಂಗಳು"},
    "field.acres_short": {"en": "acres", "kn": "ಎಕರೆ"},
    "field.acre_one": {"en": "acre", "kn": "ಎಕರೆ"},
    "field.per_acre": {"en": "per acre", "kn": "ಪ್ರತಿ ಎಕರೆಗೆ"},

    # --- actions ------------------------------------------------------------
    "action.search": {"en": "Search", "kn": "ಹುಡುಕಿ"},
    "action.clear": {"en": "Clear", "kn": "ತೆರವುಗೊಳಿಸಿ"},
    "action.save": {"en": "Save", "kn": "ಉಳಿಸಿ"},
    "action.cancel": {"en": "Cancel", "kn": "ರದ್ದುಮಾಡಿ"},
    "action.edit": {"en": "Edit", "kn": "ಬದಲಾಯಿಸಿ"},
    "action.remove": {"en": "Remove", "kn": "ತೆಗೆದುಹಾಕಿ"},
    "action.list_land": {"en": "List your land", "kn": "ನಿಮ್ಮ ಭೂಮಿ ನೋಂದಾಯಿಸಿ"},
    "action.post_plan": {"en": "Post a plan", "kn": "ಯೋಜನೆ ಪ್ರಕಟಿಸಿ"},
    "action.read_plan": {"en": "Read the plan", "kn": "ಯೋಜನೆ ಓದಿ"},
    "action.see_parcel": {"en": "See the parcel", "kn": "ಜಮೀನು ನೋಡಿ"},
    "action.register_interest": {"en": "Register interest", "kn": "ಆಸಕ್ತಿ ದಾಖಲಿಸಿ"},
    "action.update_interest": {"en": "Update my interest", "kn": "ನನ್ನ ಆಸಕ್ತಿ ಬದಲಾಯಿಸಿ"},
    "action.withdraw": {"en": "Withdraw it", "kn": "ಹಿಂಪಡೆಯಿರಿ"},
    "action.send_owner": {"en": "Send to the owner", "kn": "ಮಾಲೀಕರಿಗೆ ಕಳುಹಿಸಿ"},
    "action.ask_parcel": {"en": "Ask about this parcel", "kn": "ಈ ಜಮೀನಿನ ಬಗ್ಗೆ ಕೇಳಿ"},

    # --- project kinds ------------------------------------------------------
    "kind.crop": {"en": "Crop plan", "kn": "ಬೆಳೆ ಯೋಜನೆ"},
    "kind.livestock": {"en": "Livestock unit", "kn": "ಜಾನುವಾರು ಘಟಕ"},
    "kind.shares": {"en": "Land shares", "kn": "ಭೂಮಿ ಪಾಲುಗಳು"},
    "kind.lease": {"en": "Lease", "kn": "ಗುತ್ತಿಗೆ"},

    # --- status -------------------------------------------------------------
    "status.open": {"en": "open", "kn": "ತೆರೆದಿದೆ"},
    "status.funded": {"en": "funded", "kn": "ಹಣ ಸಂದಾಯ"},
    "status.growing": {"en": "growing", "kn": "ಬೆಳೆಯುತ್ತಿದೆ"},
    "status.sold": {"en": "sold", "kn": "ಮಾರಾಟವಾಗಿದೆ"},
    "status.closed": {"en": "closed", "kn": "ಮುಚ್ಚಲಾಗಿದೆ"},
    "status.draft": {"en": "draft", "kn": "ಕರಡು"},
    "status.matched": {"en": "matched", "kn": "ಹೊಂದಾಣಿಕೆಯಾಗಿದೆ"},
    "status.new": {"en": "new", "kn": "ಹೊಸದು"},

    # --- units and money ----------------------------------------------------
    "units.one": {"en": "share", "kn": "ಪಾಲು"},
    "units.many": {"en": "shares", "kn": "ಪಾಲುಗಳು"},
    "units.taken": {"en": "{taken} of {total} shares taken", "kn": "{total} ರಲ್ಲಿ {taken} ಪಾಲುಗಳು ಬುಕ್ ಆಗಿವೆ"},
    "units.price_each": {"en": "₹{price} a share", "kn": "ಪ್ರತಿ ಪಾಲಿಗೆ ₹{price}"},
    "money.spoken_for": {"en": "spoken for", "kn": "ಬುಕ್ ಆಗಿದೆ"},
    "money.interested": {"en": "interested", "kn": "ಆಸಕ್ತರು"},
    "money.of": {"en": "of", "kn": "ರಲ್ಲಿ"},

    # --- notices ------------------------------------------------------------
    "notice.no_money": {
        "en": "Nothing on this page takes money. Interest recorded here is not binding "
              "on you or on us, and no pool opens until counsel has signed off the structure.",
        "kn": "ಈ ಪುಟದಲ್ಲಿ ಯಾವುದೇ ಹಣ ಸ್ವೀಕರಿಸುವುದಿಲ್ಲ. ಇಲ್ಲಿ ದಾಖಲಾದ ಆಸಕ್ತಿ ನಿಮಗೂ ನಮಗೂ "
              "ಬದ್ಧವಲ್ಲ, ಮತ್ತು ವಕೀಲರ ಪರಿಶೀಲನೆ ಮುಗಿಯುವವರೆಗೆ ಯಾವುದೇ ಹೂಡಿಕೆ ಆರಂಭವಾಗುವುದಿಲ್ಲ.",
    },
    "notice.reasoning_here": {"en": "the reasoning is here", "kn": "ಕಾರಣ ಇಲ್ಲಿದೆ"},
    "notice.prelaunch": {
        "en": "Bhoomi Share is pre-launch. No investment is being offered or accepted, no "
              "money moves through this site, and no land agreement is executed here.",
        "kn": "ಭೂಮಿ ಶೇರ್ ಇನ್ನೂ ಆರಂಭವಾಗಿಲ್ಲ. ಯಾವುದೇ ಹೂಡಿಕೆ ನೀಡಲಾಗುತ್ತಿಲ್ಲ ಅಥವಾ "
              "ಸ್ವೀಕರಿಸಲಾಗುತ್ತಿಲ್ಲ, ಈ ತಾಣದ ಮೂಲಕ ಹಣ ವರ್ಗಾವಣೆಯಾಗುವುದಿಲ್ಲ, ಮತ್ತು ಯಾವುದೇ "
              "ಭೂ ಒಪ್ಪಂದ ಇಲ್ಲಿ ಮಾಡಲಾಗುವುದಿಲ್ಲ.",
    },

    # --- dashboard ----------------------------------------------------------
    "dash.your_land": {"en": "Your land", "kn": "ನಿಮ್ಮ ಭೂಮಿ"},
    "dash.your_plans": {"en": "Your plans", "kn": "ನಿಮ್ಮ ಯೋಜನೆಗಳು"},
    "dash.backing": {"en": "Plans you are backing", "kn": "ನೀವು ಬೆಂಬಲಿಸುತ್ತಿರುವ ಯೋಜನೆಗಳು"},
    "dash.asking": {"en": "Farmers asking about your land", "kn": "ನಿಮ್ಮ ಭೂಮಿ ಬಗ್ಗೆ ಕೇಳಿರುವ ರೈತರು"},
    "dash.edit_profile": {"en": "Edit profile", "kn": "ವಿವರ ಬದಲಾಯಿಸಿ"},
    "dash.tour_again": {"en": "Show me around again", "kn": "ಮತ್ತೊಮ್ಮೆ ಪರಿಚಯ ಮಾಡಿ"},
    "dash.stat_parcels": {"en": "parcels you list", "kn": "ನೀವು ನೋಂದಾಯಿಸಿದ ಜಮೀನು"},
    "dash.stat_asking": {"en": "farmers asking", "kn": "ಕೇಳಿರುವ ರೈತರು"},
    "dash.stat_plans": {"en": "plans posted", "kn": "ಪ್ರಕಟಿಸಿದ ಯೋಜನೆಗಳು"},
    "dash.stat_backing": {"en": "plans you back", "kn": "ನೀವು ಬೆಂಬಲಿಸಿದ ಯೋಜನೆಗಳು"},
    "dash.stat_interest": {"en": "interest registered", "kn": "ದಾಖಲಾದ ಆಸಕ್ತಿ"},

    # --- misc ---------------------------------------------------------------
    "misc.grown_by": {"en": "grown by", "kn": "ಬೆಳೆಯುವವರು"},
    "misc.kept_by": {"en": "kept by", "kn": "ಸಾಕುವವರು"},
    "misc.posted_by": {"en": "posted by", "kn": "ಪ್ರಕಟಿಸಿದವರು"},
    "misc.listed_by": {"en": "listed by", "kn": "ನೋಂದಾಯಿಸಿದವರು"},
    "misc.all_districts": {"en": "All districts", "kn": "ಎಲ್ಲಾ ಜಿಲ್ಲೆಗಳು"},
    "misc.select_district": {"en": "Select a district", "kn": "ಜಿಲ್ಲೆ ಆರಿಸಿ"},
    "misc.nothing_here": {"en": "Nothing here yet.", "kn": "ಇಲ್ಲಿ ಇನ್ನೂ ಏನೂ ಇಲ್ಲ."},
    "misc.language": {"en": "Language", "kn": "ಭಾಷೆ"},
    "cross.to_land": {
        "en": "Looking for land to farm or lease instead of a plan to fund?",
        "kn": "ಹೂಡಿಕೆ ಮಾಡುವ ಯೋಜನೆ ಅಲ್ಲ, ಸಾಗುವಳಿ ಮಾಡಲು ಅಥವಾ ಗುತ್ತಿಗೆಗೆ ಭೂಮಿ ಹುಡುಕುತ್ತಿದ್ದೀರಾ?",
    },
    "cross.to_invest": {
        "en": "Want to fund a cycle rather than take land on yourself?",
        "kn": "ಭೂಮಿ ತೆಗೆದುಕೊಳ್ಳುವ ಬದಲು ಒಂದು ಚಕ್ರಕ್ಕೆ ಹಣ ಹಾಕಬೇಕೆ?",
    },
    "field.stage": {"en": "Stage", "kn": "ಹಂತ"},
    "field.parcel": {"en": "Parcel", "kn": "ಜಮೀನು"},
    "field.crop_or_animal": {"en": "Crop or animal", "kn": "ಬೆಳೆ ಅಥವಾ ಪ್ರಾಣಿ"},
    "field.all_kinds": {"en": "All three", "kn": "ಮೂರೂ"},
    "stage.open": {"en": "Open", "kn": "ತೆರೆದಿರುವುದು"},
    "stage.growing": {"en": "Under way", "kn": "ನಡೆಯುತ್ತಿರುವುದು"},
    "stage.sold": {"en": "Sold", "kn": "ಮಾರಾಟವಾದದ್ದು"},
    "stage.any": {"en": "Any stage", "kn": "ಯಾವುದೇ ಹಂತ"},
}


def normalise_lang(value: str | None) -> str:
    return value if value in LANGS else DEFAULT_LANG


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: object) -> str:
    """Look up a string. An unknown key returns itself, loudly but harmlessly."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(DEFAULT_LANG, key)
    return text.format(**kwargs) if kwargs else text
