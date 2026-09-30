"""Render static/og.png, the 1200x630 image shown when a link is shared.

Social networks ignore SVG for link previews, so this draws a PNG with Pillow.
Run it after changing the wording or palette:  python scripts/make_og.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "static" / "og.png"
W, H = 1200, 630
BURG, BURG_HI, DEEP = (156, 21, 54), (190, 30, 71), (92, 11, 30)
GOLD, CREAM = (224, 169, 46), (255, 243, 240)

SERIF = ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf", "/Library/Fonts/Georgia Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
SANS = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def font(paths: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), DEEP)
    px = img.load()
    for y in range(H):                      # diagonal gradient, deep to brand
        for x in range(W):
            t = (x / W * 0.55 + y / H * 0.45)
            px[x, y] = tuple(int(DEEP[i] + (BURG_HI[i] - DEEP[i]) * t) for i in range(3))

    d = ImageDraw.Draw(img, "RGBA")
    for k, (a, w) in enumerate(((235, 7), (140, 5), (80, 4))):   # furrows
        y0 = 560 - k * 62
        pts = [(x, y0 - 70 * ((x / W) ** 1.6) + 26 * (1 - x / W) * (k + 1) / 3) for x in range(0, W + 1, 12)]
        d.line(pts, fill=CREAM + (a,), width=w, joint="curve")
    d.ellipse((930, 70, 1040, 180), fill=GOLD + (255,))          # sun

    d.text((80, 190), "Bhoomi Share", font=font(SERIF, 104), fill=CREAM)
    d.text((84, 330), "Five ways to work land and space", font=font(SERIF, 40), fill=(244, 207, 120))
    d.text((84, 388), "in Karnataka, district by district.", font=font(SERIF, 40), fill=(244, 207, 120))
    d.text((84, 70), "FARM  ·  FUND  ·  LICENCE", font=font(SANS, 24), fill=CREAM + (200,))
    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
