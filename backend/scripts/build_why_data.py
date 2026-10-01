"""Fetch the public data behind the /why page and save it as static/data/why.json.

Run it to refresh the numbers:   python scripts/build_why_data.py
The output is committed, so the running site needs no network for it, and every
figure on the page can be traced to a source named in the file.

Sources
  * World Bank, World Development Indicators (api.worldbank.org), for India:
      FP.CPI.TOTL.ZG  inflation, consumer prices (annual %)
      SL.AGR.EMPL.ZS  employment in agriculture (% of total employment)
      NV.AGR.TOTL.ZS  agriculture, forestry and fishing, value added (% of GDP)
  * FAO, FAOSTAT "Consumer Price Indices", India, Food price inflation (year on
    year, %, monthly), served by DBnomics (api.db.nomics.world/v22/series/FAO/CP/6121.100.23014)
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "static" / "data" / "why.json"
FROM_YEAR = 2010


def get(url: str):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def wb(indicator: str) -> dict[str, float]:
    d = get(f"https://api.worldbank.org/v2/country/IND/indicator/{indicator}?format=json&date={FROM_YEAR}:2030&per_page=100")
    return {x["date"]: round(x["value"], 3) for x in d[1] if x["value"] is not None}


def main() -> int:
    infl, emp, gdp = wb("FP.CPI.TOTL.ZG"), wb("SL.AGR.EMPL.ZS"), wb("NV.AGR.TOTL.ZS")
    fao = get("https://api.db.nomics.world/v22/series/FAO/CP/6121.100.23014?observations=1")["series"]["docs"][0]
    food = [[p, round(v, 3)] for p, v in zip(fao["period"], fao["value"]) if v is not None and int(p[:4]) >= FROM_YEAR]

    years = sorted(set(infl) & set(emp) & set(gdp))
    data = {
        "retrieved": date.today().isoformat(),
        "from_year": FROM_YEAR,
        "food_inflation_monthly": food,                       # [["2010-01", 17.2], ...]
        "annual": [{"year": int(y), "cpi_inflation": infl[y], "agri_employment": emp[y], "agri_gdp_share": gdp[y]} for y in years],
        "sources": [
            {"label": "World Bank, World Development Indicators: India", "url": "https://data.worldbank.org/country/india",
             "series": ["Inflation, consumer prices (annual %)", "Employment in agriculture (% of total employment)",
                        "Agriculture, forestry, and fishing, value added (% of GDP)"]},
            {"label": "FAO, FAOSTAT: Consumer Price Indices (India, food price inflation, year on year)",
             "url": "https://www.fao.org/faostat/en/#data/CP",
             "series": ["Food price inflation, monthly"], "note": "Served via DBnomics; this dataset ends in September 2023."},
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB): {len(food)} monthly points to {food[-1][0]}, {len(years)} years {years[0]}-{years[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
