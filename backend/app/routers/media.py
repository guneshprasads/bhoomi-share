"""Serve uploaded photographs.

The file on disk is the fast path. When the host's disk is not permanent, the
bytes also live in the database (photo_blob); a request for a photograph that is
missing from disk is answered from there and the file is written back as a cache,
so a redeploy loses nothing.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, Response

from .. import db
from ..deps import NotFound, conn_dep
from ..security import settings_dep
from ..settings import Settings

router = APIRouter()

CACHE = "public, max-age=86400"


@router.get("/uploads/{rel_path:path}")
def photo(rel_path: str, conn: sqlite3.Connection = Depends(conn_dep),
          settings: Settings = Depends(settings_dep)):
    root = settings.uploads_dir.resolve()
    target = (root / rel_path).resolve()
    if root not in target.parents:                      # no ../ tricks
        raise NotFound("No such photograph.")

    if target.is_file():
        return FileResponse(target, media_type="image/jpeg", headers={"Cache-Control": CACHE})

    data = db.get_blob(conn, rel_path) if settings.photos_in_db else None
    if data is None:
        raise NotFound("No such photograph.")
    try:                                                # re-create the cache copy
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    except OSError:
        pass
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": CACHE})
