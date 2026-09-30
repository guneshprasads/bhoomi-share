"""Editorial content for the explanatory pages.

Kept as data, in one place, so a lawyer, an agronomist or a translator can read
and correct it without touching templates. Everything numeric here is an
*illustrative* example and is labelled that way on the page; none of it is market
data or a forecast.

Short strings carry a Kannada version (`*_kn`). Long prose is English: the
existing site already keeps long legal and agronomic prose in one language and
translates the headings and summaries, so a mistranslated paragraph cannot
change what an agreement means.
"""

from __future__ import annotations

from typing import Any

from . import db, simulator

# --------------------------------------------------------------------------- #
# the five models
# --------------------------------------------------------------------------- #

MODELS: dict[str, dict[str, Any]] = {
    "crop-plans": {
        "kind": "crop",
        "sim_kind": "crop",
        "i18n": "kind.crop",
        "browse": "/seasons",
        "glyph": "⚘",
        "tagline": "Fund one crop on one named parcel for one season.",
        "tagline_kn": "ಒಂದು ಹೊಲದಲ್ಲಿ, ಒಂದು ಋತುವಿನ, ಒಂದು ಬೆಳೆಗೆ ಹಣ ಹಾಕಿ.",
        "summary": "A grower posts the field with photographs and what it will grow. You fund seed, inputs, water and labour for the season and take an agreed share of what it sells for.",
        "cycle": "One season, roughly 4 to 6 months",
        "funds": "The investor: seed, inputs, water, labour",
        "works": "The grower, on their own or leased land",
        "size": "One named parcel, costed in the plan",
        "split": "Stated in each plan, for example 70/30",
        "steps": [
            ("A grower posts a plan", "Parcel, district and survey number, crop, sowing window, a costed input budget, the yield they expect, the split they want, and photographs of the field."),
            ("You read it and register interest", "With an amount. Nothing is paid and nothing is binding: it tells the grower whether the plan is fundable."),
            ("The season runs", "Sowing to harvest. The grower logs what was spent and what went in the ground, against the plan you read."),
            ("The harvest sells and proceeds split", "Mandi or contract sale, receipts shared. Costs come out first; what is left is divided as signed."),
        ],
        "costs": [
            ("Seed", 12000), ("Fertiliser and crop protection", 28000), ("Irrigation and power", 14000),
            ("Labour", 34000), ("Transport and sundries", 12000),
        ],
        "cost_note": "An illustrative budget for a 3-acre pulse crop. Real budgets vary by crop, soil and water, and every plan states its own.",
        "good_for": [
            "Someone who can read a budget and wants to back one specific field.",
            "A grower with land and skill but little working capital.",
        ],
        "not_for": [
            "Anyone who needs the money back before the harvest is sold.",
            "Anyone expecting a fixed return. Crops fail.",
        ],
        "risks": [
            ("Weather", "Rain that fails or arrives at the wrong week can cut a yield sharply."),
            ("Price", "A good harvest can still sell low at the mandi on the day."),
            ("Honest costs", "A plan that understates its costs flatters the return. Read the budget line by line."),
        ],
        "faq": [
            ("When do I get my money back?", "After the harvest sells. Proceeds first repay the listed costs to whoever paid them, then the rest is split. If the sale does not cover the costs you get back what there is."),
            ("Can I fund only part of a plan?", "Yes. You register interest with an amount, and the grower sees whether the plan is fundable. Pools are kept small and capped."),
        ],
    },
    "livestock": {
        "kind": "livestock",
        "sim_kind": "livestock",
        "i18n": "kind.livestock",
        "browse": "/livestock",
        "glyph": "✦",
        "tagline": "Back a herd or flock run by someone who keeps animals for a living.",
        "tagline_kn": "ಪ್ರಾಣಿ ಸಾಕುವುದನ್ನೇ ವೃತ್ತಿ ಮಾಡಿಕೊಂಡವರ ಘಟಕಕ್ಕೆ ಹಣ ಹಾಕಿ.",
        "summary": "Sheep, goat, dairy or poultry. The keeper does the work on their own land; you fund the animals, the feed and the shed. The cycle is months, not one harvest.",
        "cycle": "Months: about nine for a lamb crop, about eighteen for a dairy unit to reach a full lactation",
        "funds": "The investor: animals, feed, shed, vaccination",
        "works": "The keeper, on their own land",
        "size": "A herd or flock stated in the plan",
        "split": "Stated in each plan, for example 60/40",
        "steps": [
            ("The keeper posts a unit", "Animal, herd size, cycle length, shed, water and fodder, the budget and the split, with photographs."),
            ("You read the losses line first", "A plan that does not say what the keeper expects to lose is one you should not fund."),
            ("The cycle runs", "The keeper logs feed, health events and vet visits. The animals belong to the unit, not to you personally."),
            ("Animals or produce sell, proceeds split", "Costs come out first; the rest is divided as signed."),
        ],
        "costs": [
            ("Animals", 140000), ("Feed and fodder", 60000), ("Shed repairs", 20000),
            ("Vet and vaccination", 15000), ("Sundries", 15000),
        ],
        "cost_note": "An illustrative budget for a small unit. Vaccination and vet cover should always be a written line in the plan; ask if it is not.",
        "good_for": [
            "Someone comfortable with a longer cycle and with animal risk.",
            "A keeper with shed, water and fodder but not the capital for stock.",
        ],
        "not_for": [
            "Anyone who cannot tolerate losing animals to disease.",
            "Anyone who needs a quick return.",
        ],
        "risks": [
            ("Mortality", "Animals die. The plan should state the loss the keeper expects, and you should believe it or not fund it."),
            ("Disease", "An outbreak can affect the whole unit at once. Vaccination and vet cover belong in the budget."),
            ("Feed cost", "Fodder prices move. Ask where the feed comes from and what happens in a dry year."),
        ],
        "faq": [
            ("Do the animals belong to me?", "No. They belong to the unit, and the split is of what the cycle earns. You fund the cycle; you do not hold title to individual animals."),
            ("What if an animal dies?", "It is a cost of the cycle. That is why the plan states an expected loss, and why a bad cycle can return less than you put in."),
        ],
    },
    "small-spaces": {
        "kind": "space",
        "sim_kind": "space",
        "i18n": "kind.space",
        "browse": "/spaces",
        "glyph": "▦",
        "tagline": "You do not need a farm. A shed, a terrace or a 30 by 40 site is enough.",
        "tagline_kn": "ಹೊಲ ಬೇಕಿಲ್ಲ. ಶೆಡ್, ತಾರಸಿ ಅಥವಾ 30×40 ಜಾಗ ಸಾಕು.",
        "summary": "Mushrooms, vermicompost, microgreens. Whoever has the space runs it; you fund the setup and the first batches. Cycles are weeks, so a plan covers several batches.",
        "cycle": "Weeks per batch; the plan says how many batches it covers",
        "funds": "The investor: setup, then each batch",
        "works": "Whoever has the space",
        "size": "Up to one acre; a 30 by 40 site is 1,200 sq ft",
        "split": "Stated in each plan, for example 60/40",
        "steps": [
            ("The host posts a space", "Area in square feet, what it will be used for, structure, water, the setup cost, the cost and expected sale of each batch, and how many batches."),
            ("You fund setup and the first batches", "The budget should separate the one-time setup from each batch: racks, spawn, substrate, water, power, labour."),
            ("Batches run and are logged", "Because a batch is ready in weeks, you see results early. The first batches are usually the weakest."),
            ("Each batch sells, proceeds split", "Costs come out first; the rest is divided as signed."),
        ],
        "costs": [
            ("Racks and fittings (setup)", 25000), ("Humidity and temperature control (setup)", 15000),
            ("Six batches: spawn", 18000), ("Six batches: substrate", 21000), ("Six batches: labour and power", 15000),
        ],
        "cost_note": "An illustrative budget for a small oyster-mushroom room over six batches. Yield is the least certain number, so treat the expected sale with suspicion.",
        "good_for": [
            "Someone who wants a short cycle and early signal.",
            "A host with an unused shed or terrace and the skill to run it.",
        ],
        "not_for": [
            "Anyone who reads a plan promising the same yield every batch as reliable. It is not.",
        ],
        "risks": [
            ("Conditions", "Mushrooms are sensitive to temperature and humidity; a hot week can spoil a batch."),
            ("Yield", "The first batches are usually the worst, and yields vary by strain and skill."),
            ("Selling", "Fresh produce must sell fast. Ask who buys and at what price."),
        ],
        "faq": [
            ("How big can a small space be?", "Up to one acre, measured in square feet. Anything bigger is a farm and belongs under a crop plan or land shares."),
            ("Why several batches in one plan?", "Because each batch takes weeks, not a season. The plan states how many it covers so you can see the whole return."),
        ],
    },
    "land-shares": {
        "kind": "shares",
        "sim_kind": "shares",
        "i18n": "kind.shares",
        "browse": "/shares",
        "glyph": "◐",
        "tagline": "Take a slice of one cycle of work on a parcel of five acres or more.",
        "tagline_kn": "ಐದು ಎಕರೆ ಅಥವಾ ಹೆಚ್ಚಿನ ಜಮೀನಿನ ಒಂದು ಚಕ್ರದ ಕೆಲಸದ ಪಾಲು ಪಡೆಯಿರಿ.",
        "summary": "The owner states what a year of work on the block costs and what one share is worth. Take one share or ten; your claim on the split is your shares divided by all the shares. Places per parcel are capped.",
        "cycle": "One cycle of work on the block, stated in the plan",
        "funds": "Several funders, each in proportion to their shares",
        "works": "The owner or their farmer",
        "size": "Five acres or more, in equal shares of a fixed rupee value",
        "split": "Stated in each plan; your slice equals your shares over all shares",
        "steps": [
            ("The owner lists a parcel", "Survey number, acreage, the cost of a year's work, the value of one share and so the number of shares."),
            ("You reserve shares", "Reserving records interest and is not binding. The number of people per parcel is capped, and the page shows places left."),
            ("The cycle runs", "The block is worked and logged. No part of the survey number changes hands."),
            ("The cycle sells, proceeds split", "Costs come out first; the rest is divided in proportion to shares."),
        ],
        "costs": [
            ("Inputs", 900000), ("Labour", 600000), ("Irrigation and power", 300000), ("Sundries", 200000),
        ],
        "cost_note": "An illustrative year for a 22-acre block: twenty lakh in total, so 80 shares of twenty-five thousand rupees each.",
        "good_for": [
            "Someone who wants to back a larger parcel without funding all of it.",
            "An owner with a big block and a wish to spread the working capital.",
        ],
        "not_for": [
            "Anyone who thinks a share is a piece of the land. It is a share of one cycle's work, never of the land.",
        ],
        "risks": [
            ("Regulation", "This is the model closest to the line SEBI draws for collective investment schemes, which is why the pool is capped and counsel reviews it first."),
            ("Concentration", "You are exposed to one block and one cycle."),
            ("Liquidity", "There is no market for shares; your money is tied up until the cycle sells."),
        ],
        "faq": [
            ("Do I own part of the land?", "No. No part of the survey number is transferred and nothing is registered in your name. You hold a share of one cycle's work."),
            ("Why is the number of people capped?", "Pooling money from the public can resemble a Collective Investment Scheme. A hard cap per parcel, shown on the page, keeps this small. See the fine print."),
        ],
    },
    "land-lease": {
        "kind": "lease",
        "sim_kind": "landowner",
        "i18n": "kind.lease",
        "browse": "/land",
        "glyph": "▣",
        "tagline": "A fixed-term licence to cultivate, drafted for Karnataka.",
        "tagline_kn": "ಕರ್ನಾಟಕಕ್ಕಾಗಿ ಬರೆದ, ನಿಗದಿತ ಅವಧಿಯ ಸಾಗುವಳಿ ಪರವಾನಗಿ.",
        "summary": "Owners who are not farming their land list it; farmers who want more find it and write to the owner. The term ends on its date, and renewal is a decision.",
        "cycle": "A fixed term, typically one or a few seasons",
        "funds": "The farmer pays rent or a crop share to the owner",
        "works": "The farmer",
        "size": "Any parcel; searchable by district, size and irrigation",
        "split": "Rent per acre per season, or a share of the crop",
        "steps": [
            ("List or search", "Acreage, survey number, water source and hours, soil, road access, what was last grown, and photographs."),
            ("Agree on terms", "Rent per acre per season, or a share of the crop. Who pays for borewell power, who repairs the bunds, who keeps the residue, what happens if the rain fails."),
            ("Sign a proper licence", "A fixed-term licence drafted against Karnataka tenancy law, signed and witnessed. Deliberately not an open-ended tenancy."),
            ("Renew or move on", "At the end of the term the land comes back, with a record of how it was farmed. Renew if it went well; list it again if it did not."),
        ],
        "costs": [],
        "cost_note": "",
        "good_for": [
            "An owner who is not farming this year and would rather the land earned something.",
            "A farmer who has the skill and inputs but needs more acres.",
        ],
        "not_for": [
            "Anyone who wants an open-ended arrangement. A licence is fixed-term on purpose.",
        ],
        "risks": [
            ("Tenancy rights", "In Karnataka, as in several states, continuous cultivation can build occupancy or purchase rights. That is why the agreement is a short licence, and why renewal is a decision."),
            ("Title", "We do not verify title. Ask for the RTC (pahani) and read it."),
            ("The season", "Rent is only as good as the farmer's season. Agree in writing what happens when it fails."),
        ],
        "faq": [
            ("Is this a lease?", "It is a fixed-term licence to cultivate. The difference matters in Karnataka; the fine print explains why."),
            ("Does the site collect rent?", "No. The site puts parcel and farmer in touch. Money and signatures stay between the two of you."),
        ],
    },
}

ORDER = ("crop-plans", "livestock", "small-spaces", "land-shares", "land-lease")


def get(slug: str) -> dict[str, Any] | None:
    m = MODELS.get(slug)
    if m is None:
        return None
    return {"slug": slug, **m}


def cost_total(model: dict[str, Any]) -> int:
    return sum(v for _, v in model["costs"])


def worked_example(model: dict[str, Any]) -> dict[str, Any]:
    """The same arithmetic the calculators use, for this model's default inputs."""
    kind = model["sim_kind"]
    return simulator.run(kind, simulator.DEFAULTS[kind])


def open_counts(conn) -> dict[str, int]:
    counts = {k: len(db.search_projects(conn, kind=k, status="open", limit=99)) for k in db.KINDS}
    counts["lease"] = len(db.search_listings(conn, status="open", limit=99))
    return counts
