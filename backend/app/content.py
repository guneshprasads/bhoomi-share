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


# --------------------------------------------------------------------------- #
# worked stories
# --------------------------------------------------------------------------- #

# Composite, illustrative people. They exist to make the arithmetic concrete;
# every page that shows them says so. Numbers come from the simulator so they
# can never disagree with the calculators.
STORIES: list[dict[str, Any]] = [
    {
        "slug": "ravi",
        "name": "Ravi",
        "role": "Investor",
        "role_kn": "ಹೂಡಿಕೆದಾರ",
        "place": "Bengaluru Urban",
        "model": "crop-plans",
        "sim_kind": "crop",
        "sim": {"cost": 100000, "sale": 160000, "investor_pct": 70},
        "situation": "Ravi works in IT and has a little money he will not need for a season. He has no land and no wish to farm, but he grew up around it and can read a budget.",
        "did": "He finds a chana plan on a 3.2-acre parcel in Belagavi, reads the costs line by line, looks at the photographs and the grower's log from earlier seasons, and registers interest for the whole budget. Counsel-reviewed paperwork follows; money never passes through the site.",
        "learned": "The return he can hope for is decent, but the failed season loses everything he put in. He funds only an amount he could lose, and he treats the break-even sale as the number that matters.",
    },
    {
        "slug": "manjula",
        "name": "Manjula",
        "role": "Grower",
        "role_kn": "ಬೆಳೆಗಾರ್ತಿ",
        "place": "Belagavi",
        "model": "crop-plans",
        "sim_kind": "crop",
        "sim": {"cost": 100000, "sale": 160000, "investor_pct": 70},
        "situation": "Manjula has three acres with canal water and thirty years of experience, but not the working capital for a full season of inputs.",
        "did": "She posts a costed plan with honest numbers, photographs of the field and the split she thinks is fair. She keeps the log up to date, including the week the rain came late.",
        "learned": "In a good season her share is the agreed 30% of what is left after costs. In a poor one it is zero. That is exactly why she puts real costs in the plan: an understated budget flatters the return on paper and hurts everyone at harvest.",
    },
    {
        "slug": "shalini",
        "name": "Shalini",
        "role": "Landowner",
        "role_kn": "ಭೂಮಾಲೀಕರು",
        "place": "Athani, Belagavi",
        "model": "land-lease",
        "sim_kind": "landowner",
        "sim": {"acres": 4, "rent_per_acre": 8000, "seasons": 2, "upkeep_per_acre": 0},
        "situation": "Shalini lives in the city and inherited four acres she cannot farm. For years a neighbour has used it on a handshake, which earns her little and protects neither of them.",
        "did": "She lists the parcel with its survey number, water hours and photographs, agrees a rent per acre per season with a farmer who wrote to her, and signs a fixed-term licence drafted for Karnataka, witnessed by two people.",
        "learned": "The land comes back to her on the licence's end date, with a record of how it was farmed. Renewal is a decision she makes again each time, not something that happens by default.",
    },
    {
        "slug": "asha",
        "name": "Asha",
        "role": "Farmer",
        "role_kn": "ರೈತ",
        "place": "Bagalkote",
        "model": "land-lease",
        "sim_kind": "farmer",
        "sim": {"acres": 3, "revenue_per_acre": 45000, "inputs_per_acre": 22000, "rent_per_acre": 8000},
        "situation": "Asha farms two acres of her own and can manage more, with her own inputs, if she can find good land with reliable water.",
        "did": "She searches parcels by district and irrigation, writes to an owner, and before signing works out her break-even: the revenue per acre she needs just to cover inputs and rent.",
        "learned": "The deal only works if a bad season is survivable. She asks for a rent she can carry even when the crop disappoints, and for a licence term long enough to see a second season.",
    },
    {
        "slug": "lakshmi",
        "name": "Lakshmi",
        "role": "Space host",
        "role_kn": "ಜಾಗದ ಮಾಲೀಕರು",
        "place": "Mysuru",
        "model": "small-spaces",
        "sim_kind": "space",
        "sim": {"setup": 40000, "batches": 6, "batch_cost": 9000, "batch_sale": 20000, "investor_pct": 60},
        "situation": "Lakshmi has a spare shed behind her house and has grown oyster mushrooms on a small scale. She needs racks, humidity control and the first batches' spawn.",
        "did": "She posts a plan that separates the one-time setup from each batch, states six batches, and is candid that the first batch or two are usually the weakest.",
        "learned": "A plan that promised identical yields every batch would have looked better on paper and been less honest. Her funder reads the failed-season line and decides knowing it.",
    },
    {
        "slug": "mahesh",
        "name": "Mahesh",
        "role": "Livestock keeper",
        "role_kn": "ಜಾನುವಾರು ಸಾಕಣೆದಾರ",
        "place": "Hassan",
        "model": "livestock",
        "sim_kind": "livestock",
        "sim": {"cost": 250000, "sale": 380000, "investor_pct": 60},
        "situation": "Mahesh has a shed, water and fodder, and years of experience with sheep, but not the capital to buy a larger flock.",
        "did": "His plan lists animals, feed, shed repairs and vet cover as separate lines, and states the loss he expects over a nine-month cycle.",
        "learned": "Animals die. Because the expected loss is written down, nobody is surprised, and the funder can judge whether the keeper is being realistic.",
    },
]


def story_with_numbers(story: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in story.items() if k != "sim"}
    out["result"] = simulator.run(story["sim_kind"], story["sim"])
    out["model_obj"] = get(story["model"])
    return out


# --------------------------------------------------------------------------- #
# FAQ
# --------------------------------------------------------------------------- #

FAQ_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("The basics", [
        ("What is Bhoomi Share?",
         "A site that connects people who have land or space, people who have money, and people who can farm, across Karnataka. There are five ways to work together: crop plans, livestock units, small spaces, land shares and leases. It is pre-launch and being proven on our own 15 acres first."),
        ("Is this live? Can I invest today?",
         "No. The site is pre-launch. No investment is being offered or accepted, no money moves through it, and no agreement is executed by it. You can read plans, use the calculators and join the waitlist."),
        ("Which districts does it cover?",
         "All 31 Karnataka districts are in the lists, but we open them one at a time after a full season of real numbers, starting with Belagavi, where our pilot is."),
        ("Is it available in Kannada?",
         "Yes. Every page can be read in English or Kannada, and the choice is remembered. Anything a person typed themselves, such as a listing's notes, is shown as they wrote it."),
    ]),
    ("Money and returns", [
        ("Is any return guaranteed?",
         "No. Crops fail, animals die and prices drop. A failed season can return nothing to the person who funded it. That is why every calculator and every model page shows the failed season next to the good one, and why we will not offer a guaranteed return."),
        ("How are the proceeds split?",
         "One rule for every funded plan: the sale first repays the listed costs to whoever paid them, then what is left is split by the percentages stated in the plan, for example 70/30. If the sale does not cover the costs, the funder gets back what there is and the grower gets nothing for their labour."),
        ("Why is the split often 70/30?",
         "It is what we run on our own land, not a rule. Every plan states its own split, agreed before work starts and written down."),
        ("Does money pass through the site?",
         "No. The site puts plans and parcels in front of people and passes on contact details. Any payment and any signature is between the people in the agreement."),
        ("Are the numbers on the earn page forecasts?",
         "No. The starting numbers are round examples you can change, and the page only shows what the agreement's arithmetic does with them. A real season can do worse than the worst case shown."),
        ("What does it cost to use?",
         "Nothing during the pilot. When there is a fee it will be stated on the how-it-works page before it applies to anyone."),
    ]),
    ("Law and safety", [
        ("Is this a Collective Investment Scheme under SEBI rules?",
         "Pooling money and managing it for a share of profits can resemble one. So pools are kept small, the number of people per plan is capped, each plan is its own arrangement, and counsel reviews the structure before any money moves. Land shares are capped hardest, because that model is the closest to the line. The fine print explains the reasoning."),
        ("Do I own part of the land if I take shares?",
         "No. A share is a share of one cycle's work, never of the land. No part of the survey number is transferred and nothing is registered in your name."),
        ("Why a licence and not a lease?",
         "In Karnataka, as in several states, a tenant who farms the same land continuously can build up occupancy or purchase rights. That is why landowners often refuse to write anything down. A short, fixed-term licence to cultivate, drafted for Karnataka, gives both sides paper without that risk, and renewal is a decision rather than a default."),
        ("Do you verify who owns the land?",
         "No. Ask for the RTC (pahani) and read it, the way you would anyway. The site does not verify title."),
        ("Is this legal advice?",
         "No. We are not your lawyers. Have your own adviser read any agreement before you sign it."),
    ]),
    ("Working with land and plans", [
        ("How does a grower get a plan funded?",
         "Post a costed plan: parcel, district and survey number, crop or animals, budget, expected sale, the split you want, and photographs. People can read it and register interest; the grower sees whether it is fundable."),
        ("Does registering interest commit me to anything?",
         "No. Registering interest is a message to the grower, not a subscription, and is not binding on you or on us."),
        ("What is a small space?",
         "A site, shed, terrace or room up to one acre, measured in square feet, used for something small and intensive like mushrooms, vermicompost or microgreens. A 30 by 40 site is 1,200 sq ft. Anything bigger is a farm and belongs under a crop plan or land shares."),
        ("Can a landowner also list land for farmers?",
         "Yes. List the parcel with its survey number, water source and hours, soil, road access and photographs. Farmers search by district and irrigation and write to you; you agree rent or a crop share and sign a fixed-term licence."),
    ]),
    ("Accounts and data", [
        ("What do you store about me?",
         "If you join the waitlist: your name, phone number, the side you are on and your district. If you make an account: that plus email, district, taluk, and a password stored as a salted hash. Photographs you upload are re-saved to remove the location metadata your phone adds."),
        ("Who can see my phone number?",
         "When you write to a landowner or register interest in a plan, that person sees your name, district and phone number. That is the point of writing. Nobody else does, and it is not sold or forwarded."),
        ("How do I delete my data?",
         "Ask us and we will delete it, without asking why."),
    ]),
]


def faq_flat() -> list[tuple[str, str]]:
    return [qa for _, items in FAQ_GROUPS for qa in items]


# --------------------------------------------------------------------------- #
# Foresight canvas: 2026-2036
# --------------------------------------------------------------------------- #

# A foresight exercise, not a forecast. It says what would have to happen for
# farm money to become more transparent in Karnataka, and what follows if it
# does. Drivers are real, public features of the landscape, stated without
# invented statistics.
FORESIGHT = {
    "drivers": [
        ("Groundwater and monsoon", "Many holdings depend on borewells, and rainfall has become less predictable. Water is the variable that most often decides a season."),
        ("Input and labour costs", "Seed, fertiliser and labour costs move faster than many farm-gate prices, which squeezes the margin a funder is relying on."),
        ("Digital markets", "e-NAM links regulated mandis online, and price information is easier to see than it was. Forward prices and assured buyers are becoming practical."),
        ("Crop insurance", "Schemes such as PMFBY exist, but many growers do not know the real cost and trigger of cover. Making it visible makes it comparable."),
        ("Absent owners, small holdings", "Land is increasingly held by people who do not farm it, in pieces too small to finance on their own."),
        ("Collective farming", "Farmer Producer Organisations and shared-risk arrangements are a stated policy direction, and need trustworthy records to work."),
    ],
    "milestones": [
        (2026, "The pilot season", "Our own 15 acres run every model with our own capital. A full season of numbers, including the parts that went badly, goes on the record."),
        (2027, "One district opens", "Belagavi opens first, on counsel-reviewed structures, with small capped pools and fixed-term licences."),
        (2028, "Every plan has an account", "No plan is shown without a ledger that has been checked: budget adds up, spending logged, money in equals money out."),
        (2030, "Risk is shown before money is asked for", "A funder sees the chance of a shortfall and the bad case before committing, and which fix would pay back."),
        (2032, "Public data replaces assumptions", "Mandi prices, weather and district yield records feed the simulation, so fewer of its numbers are assumed."),
        (2036, "A common, open record", "A shared, open farm-account format across Karnataka, so a grower's record travels with them and any lender can read it."),
    ],
    "opportunities": [
        ("Cheaper working capital where risk is visible", "When a funder can see the bad case, they can price it, and small growers stop paying for uncertainty."),
        ("Licences replace handshakes", "Owners who would never write anything down can let land be farmed on paper that protects both sides."),
        ("Reviewers verify instead of watch", "Extension workers and lenders move from chasing paperwork to checking the flagged gaps."),
    ],
    "risks": [
        ("False confidence in a model", "A simulation can look precise and be wrong. Every number must carry its assumptions, and humans must still decide."),
        ("One platform becomes the gatekeeper", "If one record format wins and is closed, small operators are locked in. Hence: open the format."),
        ("Shared weather, shared loss", "Plans in one district can fail together in one bad monsoon. Diversifying across districts and models matters."),
        ("Regulation moves", "Rules on collective investment and on tenancy can change. The structure has to be reviewed again each time."),
    ],
    "future": [
        "Every regulated farm arrangement has a checked account that any funder or lender can read.",
        "The bad case is shown as plainly as the good case, before any money moves.",
        "Growers carry their record from one season and one funder to the next.",
        "Specialists spend their time on the flagged exceptions, not on raw paperwork.",
    ],
    "steps": [
        ("Finish the pilot season", "Publish the numbers, including the failures."),
        ("Settle the structure with counsel", "Pools capped and small; licences fixed-term; nothing that looks like a public scheme."),
        ("Open one district", "Belagavi first. Learn from real plans before opening another."),
        ("Replace assumptions with data", "Wire in public price and weather data, and show which numbers moved from assumed to measured."),
        ("Open the ledger format", "So a record is portable and no single platform owns it."),
    ],
}


def product_numbers() -> dict[str, Any]:
    """Headline numbers for the example holding, from the same engine the pages use."""
    from . import ledger, risk

    plans = ledger.example_plans()
    h = risk.holding(plans)
    t = h["totals"]
    live = [r for r in h["rows"] if not r.get("skipped")]
    return {
        "holding": h, "totals": t, "plans_n": len(plans),
        "flagged": sum(len(c["flags"]) for c in ledger.check_holding(plans)),
        "cut": round((1 - t["after_fixes"] / t["expected_shortfall"]) * 100) if t["expected_shortfall"] else 0,
        "best": max(live, key=lambda r: r["expected_shortfall"]),
        "top": sorted(live, key=lambda r: -r["expected_shortfall"])[:4],
    }
