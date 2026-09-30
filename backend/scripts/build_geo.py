"""Build static/data/karnataka_districts.geojson from open district boundaries.

Source: DataMeet "maps" repository, Census of India 2011 district boundaries
(https://github.com/datameet/maps, MIT licence, (c) DataMeet India community).
The output is committed, so the running site needs no network for it.

    pip install pyshp        # build-time only, not needed to run the site
    python scripts/build_geo.py

What it does to the source:
  * keeps Karnataka's 30 outlines and renames them to this site's canonical
    names (Bangalore Rural -> Bengaluru North, Ramanagara -> Bengaluru South,
    matching app/karnataka.py);
  * simplifies the outlines (Douglas-Peucker) and rounds coordinates, taking a
    10 MB shapefile to under 100 KB;
  * keeps Vijayanagara inside Ballari. Vijayanagara was split from Ballari in
    2021 and these boundaries predate that, so the two share one outline and
    the page says so rather than drawing a guessed line through it.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist"
OUT = Path(__file__).resolve().parent.parent / "static" / "data" / "karnataka_districts.geojson"

# 2011 spellings -> this site's canonical names
RENAME = {
    "Bagalkot": "Bagalkote", "Bangalore": "Bengaluru Urban", "Bangalore Rural": "Bengaluru North",
    "Belgaum": "Belagavi", "Bellary": "Ballari", "Bijapur": "Vijayapura",
    "Chamrajnagar": "Chamarajanagara", "Chikmagalur": "Chikkamagaluru", "Gulbarga": "Kalaburagi",
    "Mysore": "Mysuru", "Ramanagara": "Bengaluru South", "Shimoga": "Shivamogga", "Tumkur": "Tumakuru",
}
SHARED = {"Ballari": ["Ballari", "Vijayanagara"]}
TOLERANCE = 0.0035  # degrees, roughly 400 m: invisible at state scale


def _dp(points: list[list[float]], tol: float) -> list[list[float]]:
    """Douglas-Peucker on an open polyline (iterative, to avoid recursion limits)."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = points[a], points[b]
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy)
        far, idx = 0.0, -1
        for i in range(a + 1, b):
            x0, y0 = points[i]
            d = (math.hypot(x0 - x1, y0 - y1) if norm == 0
                 else abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / norm)
            if d > far:
                far, idx = d, i
        if far > tol and idx != -1:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(points, keep) if k]


def _ring(ring: list[list[float]]) -> list[list[float]] | None:
    closed = ring[:-1] if ring[0] == ring[-1] else ring
    simple = _dp(closed + [closed[0]], TOLERANCE)[:-1]
    if len(simple) < 4:
        return None
    out = [[round(x, 4), round(y, 4)] for x, y in simple]
    return out + [out[0]]


def _geometry(geom: dict) -> dict:
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    kept = []
    for poly in polys:
        rings = [r for r in (_ring(r) for r in poly) if r]
        if rings:
            kept.append(rings)
    return {"type": "MultiPolygon", "coordinates": kept}


def main() -> int:
    try:
        import shapefile  # pyshp
    except ImportError:
        print("pip install pyshp first (build-time only)")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        for ext in ("shp", "dbf", "shx"):
            urllib.request.urlretrieve(f"{BASE}.{ext}", f"{tmp}/d.{ext}")
        reader = shapefile.Reader(f"{tmp}/d")
        features = []
        for rec, shp in zip(reader.records(), reader.shapes()):
            row = rec.as_dict()
            if "arnataka" not in str(row.get("ST_NM", "")):
                continue
            name = RENAME.get(row["DISTRICT"], row["DISTRICT"])
            features.append({
                "type": "Feature",
                "properties": {"name": name, "districts": SHARED.get(name, [name])},
                "geometry": _geometry(shp.__geo_interface__),
            })
    features.sort(key=lambda f: f["properties"]["name"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features},
                              separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, {len(features)} outlines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
