"""Photograph uploads.

Every image is re-encoded before it is written to disk. That is not about file
size: a photo taken on a phone carries EXIF metadata including the GPS
coordinates of the field, and a landowner should not publish the exact location
of their land without meaning to. Re-encoding through a fresh image drops all of
it.
"""

from __future__ import annotations

import secrets
from pathlib import Path

from PIL import Image, UnidentifiedImageError

MAX_PHOTOS = 6
MAX_BYTES = 10 * 1024 * 1024          # 10 MB per file, before re-encoding
MAX_EDGE = 1600                        # longest side, in pixels
JPEG_QUALITY = 82

ACCEPTED = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
HEIC_HINTS = {"image/heic", "image/heif"}


class PhotoError(Exception):
    """Something a person should be told about, in words they can act on."""


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise PhotoError(message)


def save_upload(data: bytes, content_type: str, filename: str, root: Path, owner_kind: str) -> str:
    """Write one uploaded image and return its path relative to `root`."""
    ctype = (content_type or "").lower().split(";")[0].strip()
    suffix = Path(filename or "").suffix.lower()

    _check(
        ctype not in HEIC_HINTS and suffix not in {".heic", ".heif"},
        "iPhone HEIC photos are not supported yet. In Camera settings choose "
        "'Most Compatible', or share the photo to convert it to JPEG first.",
    )
    _check(
        ctype in ACCEPTED or suffix in {".jpg", ".jpeg", ".png", ".webp"},
        "That file is not a photo. JPEG, PNG or WebP only.",
    )
    _check(len(data) <= MAX_BYTES, "That photo is larger than 10 MB. Send a smaller one.")
    _check(len(data) > 0, "That file was empty.")

    import io

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise PhotoError("We could not read that image file.") from exc

    # A fresh RGB canvas: no EXIF, no GPS, no colour-profile surprises.
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        flat = Image.new("RGB", image.size, (255, 255, 255))
        flat.paste(image, mask=image.split()[-1])
        image = flat
    else:
        image = image.convert("RGB")

    image.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)

    rel_dir = Path(owner_kind)
    (root / rel_dir).mkdir(parents=True, exist_ok=True)
    rel_path = rel_dir / f"{secrets.token_hex(8)}.jpg"
    image.save(root / rel_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return str(rel_path)


def remove_file(root: Path, rel_path: str) -> None:
    """Best effort: a missing file is not worth failing a request over."""
    try:
        (root / rel_path).unlink(missing_ok=True)
    except OSError:
        pass
