"""The first-run guided tour.

Six steps over the dashboard, each pointing at one real thing on the page. It
runs once per account — the flag lives on the user row rather than in the
browser, so it does not reappear on a second device and does not vanish when
someone clears their browser.

A step whose target is not on the page (or is hidden, as the nav links are on a
phone) still shows: the tooltip centres itself and the spotlight is skipped.
That way the words are never lost, only the pointing.
"""

from __future__ import annotations

from typing import Any


def steps(lang: str = "en") -> list[dict[str, str]]:
    kn = lang == "kn"
    return [
        {
            "target": "[data-tour='head']",
            "title": "ಸ್ವಾಗತ." if kn else "Welcome.",
            "body": (
                "ಇದು ನಿಮ್ಮ ಪುಟ. ಇಲ್ಲಿಂದ ನೀವು ಭೂಮಿ ನೋಂದಾಯಿಸಬಹುದು, ಯೋಜನೆ ಪ್ರಕಟಿಸಬಹುದು, "
                "ಅಥವಾ ಬೇರೆಯವರ ಯೋಜನೆಗೆ ಆಸಕ್ತಿ ದಾಖಲಿಸಬಹುದು. ಮುಖ್ಯವಾದದ್ದು ಒಂದು: "
                "ಈ ತಾಣದಲ್ಲಿ ಯಾವ ಹಣವೂ ವರ್ಗಾವಣೆಯಾಗುವುದಿಲ್ಲ."
                if kn else
                "This is your page. From here you can list land, post a plan, or register "
                "interest in someone else's. One thing to know before anything else: "
                "no money moves through this site. Interest you record is a message, not a payment."
            ),
        },
        {
            "target": "[data-tour='invest']",
            "title": "ಐದು ದಾರಿ." if kn else "Five ways to take part.",
            "body": (
                "ಬೆಳೆ ಯೋಜನೆ, ಜಾನುವಾರು ಘಟಕ, ಅಣಬೆಯಂತಹ ಸಣ್ಣ ಜಾಗ, ದೊಡ್ಡ ಜಮೀನಿನ ಪಾಲುಗಳು, ಮತ್ತು ಗುತ್ತಿಗೆ. "
                "ಹೂಡಿಕೆ ಮಾಡುವವರು ಇಲ್ಲಿಂದ ಶುರು ಮಾಡಿ."
                if kn else
                "A crop season, a livestock unit, a small space for something like mushrooms, "
                "shares in a big parcel, or a straight lease. If you have money to put in "
                "rather than land, start here."
            ),
        },
        {
            "target": "[data-tour='land']",
            "title": "ನಿಮ್ಮ ಭೂಮಿ." if kn else "Your land.",
            "body": (
                "ಈ ವರ್ಷ ನೀವು ಸಾಗುವಳಿ ಮಾಡದ ಜಮೀನು ಇದ್ದರೆ ಇಲ್ಲಿ ನೋಂದಾಯಿಸಿ — ಫೋಟೋ, ನೀರು, "
                "ಮಣ್ಣು, ಮತ್ತು ಎಷ್ಟು ಅವಧಿಗೆ. ರೈತರು ನಿಮಗೆ ಇಲ್ಲಿಂದಲೇ ಬರೆಯುತ್ತಾರೆ."
                if kn else
                "Land you are not farming this year goes here — photographs, water, soil, and "
                "the term you want. Farmers write to you through it, and you see their number "
                "when they do. Listing it creates no tenancy."
            ),
        },
        {
            "target": "[data-tour='plans']",
            "title": "ನಿಮ್ಮ ಯೋಜನೆಗಳು." if kn else "Your plans.",
            "body": (
                "ಒಂದು ಚಕ್ರದ ಖರ್ಚು ಲೆಕ್ಕ ಹಾಕಿ ಯೋಜನೆ ಬರೆಯಿರಿ — ಬೆಳೆ, ಜಾನುವಾರು, ಸಣ್ಣ ಜಾಗ (ಉದಾ. ಅಣಬೆ), ಅಥವಾ "
                "ಐದು ಎಕರೆಗಿಂತ ದೊಡ್ಡ ಜಮೀನಾದರೆ ಪಾಲುಗಳಾಗಿ."
                if kn else
                "Write a plan for one cycle, costed: a crop season, a livestock unit, a small "
                "space such as a 30 by 40 site for mushrooms, or — if the parcel is five acres "
                "or more — the same thing divided into shares several people can take a piece of."
            ),
        },
        {
            "target": "[data-tour='backing']",
            "title": "ನೀವು ಬೆಂಬಲಿಸಿದವು." if kn else "What you are backing.",
            "body": (
                "ನೀವು ಆಸಕ್ತಿ ದಾಖಲಿಸಿದ ಯೋಜನೆಗಳು ಇಲ್ಲಿ ಕಾಣಿಸುತ್ತವೆ. ಯಾವಾಗ ಬೇಕಾದರೂ "
                "ಹಿಂಪಡೆಯಬಹುದು — ಅದು ಬದ್ಧತೆಯಲ್ಲ."
                if kn else
                "Plans you register interest in show up here, with what you put against each one. "
                "You can change the amount or withdraw at any time — it binds nobody until there "
                "is a signed deed."
            ),
        },
        {
            "target": "[data-tour='profile']",
            "title": "ನಿಮ್ಮ ಜಿಲ್ಲೆ ಆರಿಸಿ." if kn else "Set your district.",
            "body": (
                "ಭೂಮಿ ಶೇರ್ ಕರ್ನಾಟಕದ 31 ಜಿಲ್ಲೆಗಳಲ್ಲಿ ಕೆಲಸ ಮಾಡುತ್ತದೆ. ನಿಮ್ಮ ಜಿಲ್ಲೆ ಆರಿಸಿದರೆ "
                "ಹತ್ತಿರದ ಜಮೀನು ಮೊದಲು ಕಾಣಿಸುತ್ತದೆ. ಭಾಷೆಯನ್ನೂ ಮೇಲ್ಗಡೆ ಬದಲಾಯಿಸಬಹುದು."
                if kn else
                "Bhoomi Share covers all 31 Karnataka districts. Setting yours puts land near you "
                "first, and tells growers where you are. You can switch between English and "
                "ಕನ್ನಡ at the top of any page."
            ),
        },
    ]


def payload(lang: str = "en") -> dict[str, Any]:
    kn = lang == "kn"
    return {
        "steps": steps(lang),
        "labels": {
            "next": "ಮುಂದೆ" if kn else "Next",
            "back": "ಹಿಂದೆ" if kn else "Back",
            "done": "ಆಯಿತು" if kn else "Got it",
            "skip": "ಬಿಟ್ಟುಬಿಡಿ" if kn else "Skip the tour",
            "of": "ರಲ್ಲಿ" if kn else "of",
            "title": "ಪರಿಚಯ" if kn else "Quick tour",
        },
    }
