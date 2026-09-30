"""The example holding used by the Ledger and Money-at-Risk pages.

Everything here is INVENTED for illustration. It is not the pilot's data and not
any real person's. It is shaped like a real holding (several plans of different
kinds, a few seasons of history, a district benchmark) so the tools have
something honest to chew on, and it deliberately contains the kind of mess real
ledgers have: a budget whose lines do not add up, a plan that never logged its
spending, a history that is too short to trust.

Money is in rupees, areas in acres (or head, for livestock, or rooms, for a
small space), prices per quintal or per head as the plan says.
"""

from __future__ import annotations

from typing import Any

HOLDING_NAME = "Example holding"
HOLDING_NOTE = "Invented for illustration: not the pilot's numbers and not a real person's."

# Each plan:
#   area / unit      how much is being worked (acres, head, rooms)
#   expected_yield   per unit of area, as the grower wrote it in the plan
#   expected_price   per yield_unit sold
#   costs            the plan's budget lines
#   stated_budget    the total the grower wrote down (may disagree with the lines)
#   spent            what the log says was spent so far (None = never logged)
#   history          past seasons on this plan's land: yield per unit area and price
#   benchmark        an assumed district figure: (mean yield per unit, sd)
PLANS: list[dict[str, Any]] = [
    {
        "id": "chana-212-3", "name": "Chana · Rabi 2026 · Sy. 212/3", "kind": "crop",
        "district": "Belagavi", "area": 3.2, "unit": "acres",
        "yield_unit": "quintals per acre", "price_unit": "rupees per quintal",
        "investor_pct": 70,
        "expected_yield": 8.0, "expected_price": 6250,
        "costs": [("Seed", "Seed", 12000), ("Fertiliser and crop protection", "Inputs", 28000),
                  ("Irrigation and power", "Water and power", 14000), ("Labour", "Labour", 34000),
                  ("Transport and sundries", "Other", 12000)],
        "stated_budget": 100000, "spent": 101500,
        "history": [(2021, 7.4, 5200), (2022, 8.6, 5400), (2023, 5.9, 5900), (2024, 8.1, 5600), (2025, 7.7, 6000)],
        "benchmark": (7.2, 1.6),
    },
    {
        "id": "tur-211", "name": "Tur · Kharif 2026 · Sy. 211", "kind": "crop",
        "district": "Belagavi", "area": 2.4, "unit": "acres",
        "yield_unit": "quintals per acre", "price_unit": "rupees per quintal",
        "investor_pct": 65,
        "expected_yield": 5.5, "expected_price": 8200,
        "costs": [("Seed", "Seed", 6500), ("Fertiliser and crop protection", "Inputs", 19500),
                  ("Labour", "Labour", 24000), ("Transport and sundries", "Other", 8000)],
        "stated_budget": 64000, "spent": None,                # never logged
        "history": [(2023, 4.1, 7600), (2024, 5.8, 8800)],    # short history
        "benchmark": (4.6, 1.3),
    },
    {
        "id": "jowar-214-1", "name": "Jowar · Rabi 2026 · Sy. 214/1", "kind": "crop",
        "district": "Belagavi", "area": 1.9, "unit": "acres",
        "yield_unit": "quintals per acre", "price_unit": "rupees per quintal",
        "investor_pct": 70,
        "expected_yield": 9.0, "expected_price": 3300,
        "costs": [("Seed", "Seed", 3800), ("Fertiliser and crop protection", "Inputs", 10200),
                  ("Labour", "Labour", 15500), ("Transport and sundries", "Other", 4500)],
        "stated_budget": 31000,                               # lines add to 34,000: off by +9.7%
        "spent": 33200,
        "history": [(2021, 8.2, 2900), (2022, 9.6, 3000), (2023, 6.8, 3300), (2024, 9.4, 3100), (2025, 8.8, 3250)],
        "benchmark": (8.0, 1.8),
    },
    {
        "id": "sheep-unit-hassan", "name": "Sheep unit · 9-month cycle", "kind": "livestock",
        "district": "Hassan", "area": 40, "unit": "head",
        "yield_unit": "sold per head kept", "price_unit": "rupees per head",
        "investor_pct": 60,
        "expected_yield": 0.9, "expected_price": 9500,
        "costs": [("Animals", "Animals", 140000), ("Feed and fodder", "Feed", 60000),
                  ("Shed repairs", "Other", 20000), ("Vet and vaccination", "Health", 15000),
                  ("Sundries", "Other", 15000)],
        "stated_budget": 250000, "spent": 243000,
        "history": [(2023, 0.86, 8800), (2024, 0.93, 9300), (2025, 0.88, 9700)],
        "benchmark": (0.88, 0.07),
    },
    {
        "id": "mushroom-mysuru", "name": "Oyster mushrooms · 6 batches", "kind": "space",
        "district": "Mysuru", "area": 6, "unit": "batches",
        "yield_unit": "kg per batch", "price_unit": "rupees per kg",
        "investor_pct": 60,
        "expected_yield": 100.0, "expected_price": 200,
        "costs": [("Racks and fittings (setup)", "Setup", 25000), ("Humidity and temperature control (setup)", "Setup", 15000),
                  ("Spawn", "Seed", 18000), ("Substrate", "Inputs", 21000), ("Labour and power", "Labour", 15000)],
        "stated_budget": 94000, "spent": 61000,
        "history": [(2025, 72.0, 190), (2025.5, 88.0, 210)],   # two early batches: the weak ones
        "benchmark": (95.0, 20.0),
    },
    {
        "id": "block-athani-22", "name": "22-acre block · one cycle of work", "kind": "shares",
        "district": "Belagavi", "area": 22, "unit": "acres",
        "yield_unit": "quintals per acre", "price_unit": "rupees per quintal",
        "investor_pct": 70,
        "expected_yield": 14.0, "expected_price": 8700,
        "costs": [("Inputs", "Inputs", 900000), ("Labour", "Labour", 600000),
                  ("Irrigation and power", "Water and power", 300000), ("Sundries", "Other", 200000)],
        "stated_budget": 2000000, "spent": 1720000,
        "history": [(2022, 13.5, 7900), (2023, 10.2, 8600), (2024, 14.8, 8300), (2025, 13.9, 8900)],
        "benchmark": (12.5, 2.6),
    },
]

# What the season's receipts actually were, for plans whose last cycle has sold.
# Used by the balance check: sale = costs repaid + funder's share + grower's share.
SETTLED: dict[str, dict[str, Any]] = {
    "jowar-214-1": {"season": 2025, "receipts": 53200, "repaid_to_funder": 34000, "funder_share": 13440, "grower_share": 5760},
    "chana-212-3": {"season": 2025, "receipts": 147500, "repaid_to_funder": 101500, "funder_share": 32200, "grower_share": 13800},
    "sheep-unit-hassan": {"season": 2025, "receipts": 318000, "repaid_to_funder": 243000, "funder_share": 45000, "grower_share": 30000},
}

# Assumptions the risk model starts from, all editable on the page. They are
# labelled "assumed" everywhere they appear.
DEFAULT_ASSUMPTIONS: dict[str, float] = {
    "yield_cv": 0.22,          # season-to-season spread in yield, as a fraction of the mean
    "price_vol": 0.14,         # spread in the price at sale
    "p_fail": 0.08,            # chance of a badly failed season (drought, pests, disease)
    "fail_factor": 0.30,       # yield in such a season, as a fraction of normal
    "rho": -0.25,              # yield and price tend to move against each other locally
}
