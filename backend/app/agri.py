"""Where farming is strongest in Karnataka, and which model fits where.

This is deliberately *qualitative*. It is general background knowledge of
Karnataka's cropping patterns, sorted into three tiers, plus our own starting
view of which of the five models suits each district. It is not a statistic, not
a yield claim and not advice, and the map page says so. If you have district
figures you trust (net sown area, irrigated share, milk and sheep numbers from
the state agriculture and animal-husbandry departments), replace the tiers with
them: this module is the only place that needs to change.

Tiers
  3  Major cropland belt: large, continuous cropland; farming is the main use of land
  2  Mixed farming and plantations: crops alongside hills, plantations or fast-growing towns
  1  Coast, forest or city: limited open cropland, more plantation and small holdings
"""

from __future__ import annotations

TIERS = {
    3: "Major cropland belt",
    2: "Mixed farming and plantations",
    1: "Coast, forest or city",
}

# model slugs match app/content.py
FIT_LABEL = {
    "crop-plans": "Crop plans",
    "livestock": "Livestock units",
    "small-spaces": "Small spaces",
    "land-shares": "Land shares",
    "land-lease": "Leases",
}

# district: (tier, commonly grown, best-fit models in order, one-line reason)
DISTRICT_DATA: dict[str, tuple[int, str, tuple[str, ...], str]] = {
    # --- Belagavi division ---
    "Belagavi": (3, "Sugarcane, maize, cotton, groundnut, pulses", ("crop-plans", "livestock", "land-lease"),
                 "Canal and river irrigation, large holdings, strong dairy and sugar. Our pilot district."),
    "Bagalkote": (3, "Sugarcane, jowar, maize, sunflower, pomegranate", ("crop-plans", "land-shares", "land-lease"),
                  "Irrigated blocks on the Krishna system with parcels big enough for shares."),
    "Vijayapura": (2, "Grapes, lemon, pomegranate, jowar, sunflower", ("crop-plans", "land-shares", "livestock"),
                   "Semi-arid, with strong horticulture pockets; water is the thing to check first."),
    "Dharwad": (3, "Cotton, chilli, jowar, soybean, wheat", ("crop-plans", "small-spaces", "land-lease"),
                "Black-soil cropland next to the Hubballi-Dharwad city market."),
    "Gadag": (2, "Onion, jowar, cotton, sunflower, groundnut", ("crop-plans", "livestock", "land-lease"),
              "Dryland cropping where short-cycle crops and sheep and goat keeping both fit."),
    "Haveri": (3, "Maize, cotton, chilli, paddy, groundnut", ("crop-plans", "land-lease", "livestock"),
               "A cropland belt with a known chilli and maize economy."),
    "Uttara Kannada": (1, "Arecanut, paddy, cashew, spices", ("small-spaces", "crop-plans"),
                       "Forest and coast: small holdings, so small spaces suit better than large shares."),
    # --- Bengaluru division ---
    "Bengaluru Urban": (1, "Vegetables, flowers (peri-urban)", ("small-spaces",),
                        "Mostly built up; the opportunity is rooftops, sheds and fresh produce for a huge market."),
    "Bengaluru North": (2, "Ragi, vegetables, grapes, flowers", ("small-spaces", "livestock", "crop-plans"),
                        "Peri-urban farming close to the largest market in the state, with a dairy tradition."),
    "Bengaluru South": (2, "Silk cocoons, mango, coconut, ragi", ("small-spaces", "livestock", "crop-plans"),
                        "Sericulture and orchards on small holdings near Bengaluru."),
    "Chikkaballapura": (2, "Grapes, vegetables, ragi, silk, flowers", ("small-spaces", "crop-plans", "livestock"),
                        "Horticulture and sericulture close to Bengaluru; irrigation is largely from borewells."),
    "Chitradurga": (3, "Groundnut, maize, sunflower, onion", ("livestock", "crop-plans", "land-shares"),
                    "Large dryland holdings with a strong sheep tradition."),
    "Davanagere": (3, "Maize, paddy, arecanut, sunflower", ("crop-plans", "land-shares", "land-lease"),
                   "A maize and paddy belt with canal irrigation and good-sized parcels."),
    "Kolar": (2, "Tomato, mango, ragi, silk", ("small-spaces", "livestock", "crop-plans"),
              "Vegetables, orchards and dairy on small holdings within reach of Bengaluru."),
    "Shivamogga": (2, "Arecanut, paddy, sugarcane, maize", ("crop-plans", "small-spaces", "land-lease"),
                   "Malnad and plains: plantation crops alongside paddy."),
    "Tumakuru": (2, "Coconut, ragi, groundnut, arecanut", ("livestock", "crop-plans", "small-spaces"),
                 "Mixed dryland and coconut country with sheep and dairy, and Bengaluru close by."),
    # --- Kalaburagi division ---
    "Ballari": (3, "Cotton, jowar, chilli, sunflower, paddy", ("crop-plans", "land-shares", "livestock"),
                "Large holdings and Tungabhadra canal irrigation; sheep rearing is common."),
    "Vijayanagara": (3, "Paddy, cotton, maize, chilli", ("crop-plans", "land-shares", "land-lease"),
                     "Carved out of Ballari in 2021 and shown with it on this map. Tungabhadra command area."),
    "Bidar": (3, "Tur, soybean, sugarcane, jowar", ("crop-plans", "land-shares", "land-lease"),
              "Plateau cropland with pulses and oilseeds."),
    "Kalaburagi": (3, "Tur (pigeon pea), jowar, bengal gram, cotton", ("crop-plans", "land-shares", "land-lease"),
                   "The pulse bowl of the state: big parcels and a strong crop tradition."),
    "Koppal": (2, "Paddy, maize, jowar, groundnut", ("crop-plans", "livestock", "land-lease"),
               "Canal-irrigated paddy alongside dryland cropping."),
    "Raichur": (3, "Paddy, cotton, sunflower, tur", ("crop-plans", "land-shares", "livestock"),
                "Tungabhadra and Krishna canal country with large parcels."),
    "Yadgir": (3, "Cotton, tur, paddy, jowar", ("crop-plans", "land-shares", "land-lease"),
               "Black-soil cropland with pulses and cotton."),
    # --- Mysuru division ---
    "Chamarajanagara": (2, "Banana, turmeric, sugarcane, maize", ("crop-plans", "livestock", "land-lease"),
                        "Dry-belt cash crops next to Mysuru and Tamil Nadu markets."),
    "Chikkamagaluru": (2, "Coffee, arecanut, pepper, paddy", ("small-spaces", "crop-plans"),
                       "Plantation hills: long-cycle crops fit plantations, while small spaces suit short cycles."),
    "Dakshina Kannada": (1, "Arecanut, coconut, rubber, cashew, paddy", ("small-spaces", "crop-plans"),
                         "Coastal small holdings and a large urban market in Mangaluru."),
    "Hassan": (2, "Potato, coffee, coconut, paddy, ragi", ("crop-plans", "livestock", "small-spaces"),
               "Mixed farming with a dairy tradition between the plains and the ghats."),
    "Kodagu": (2, "Coffee, pepper, cardamom, paddy", ("small-spaces", "land-lease"),
               "Plantation country; land is precious and usually already under a crop."),
    "Mandya": (3, "Sugarcane, paddy, ragi, coconut", ("crop-plans", "livestock", "land-lease"),
               "Cauvery canal irrigation and intensive farming with a strong dairy network."),
    "Mysuru": (3, "Paddy, ragi, tobacco, sugarcane, cotton", ("crop-plans", "small-spaces", "livestock"),
               "Good water, a big city market and plenty of small-scale producers."),
    "Udupi": (1, "Paddy, coconut, arecanut, cashew", ("small-spaces", "crop-plans"),
              "Coastal small holdings."),
}


def tier_of(district: str) -> int:
    return DISTRICT_DATA[district][0]


def for_map(district: str) -> dict:
    tier, crops, fit, why = DISTRICT_DATA[district]
    return {
        "tier": tier,
        "tier_label": TIERS[tier],
        "crops": crops,
        "fit": [{"slug": s, "label": FIT_LABEL[s]} for s in fit],
        "why": why,
    }
