#!/usr/bin/env python3
"""Make a safe copy of the Bhoomi Share database.

    python3 scripts/backup.py                  -> a timestamped .sqlite3 snapshot
    python3 scripts/backup.py --with-photos    -> a .zip of that plus uploads/
    python3 scripts/backup.py --csv            -> one .csv per table, for a spreadsheet
    python3 scripts/backup.py --to ~/Desktop   -> write it somewhere else

Why not just copy the file? The database runs in WAL mode, so recent writes may
still be sitting in `bhoomi.sqlite3-wal` when you copy. A plain `cp` while the
server is running can hand you a snapshot missing the last few rows. SQLite's
own backup API, used below, is consistent whether or not the server is running.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sqlite3
import sys
import zipfile
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.settings import get_settings  # noqa: E402


def snapshot(source: Path, dest: Path) -> Path:
    """A consistent copy, even with the server mid-write."""
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    out = sqlite3.connect(dest)
    with out:
        src.backup(out)
    out.close()
    src.close()
    return dest


def dump_csv(source: Path, folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    written = []
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    for table in tables:
        rows = list(conn.execute(f"SELECT * FROM {table}"))
        path = folder / f"{table}.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if rows:
                writer.writerow(rows[0].keys())
                for r in rows:
                    writer.writerow(list(r))
            else:
                cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})")]
                writer.writerow(cols)
        written.append(path)
    conn.close()
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up the Bhoomi Share database.")
    parser.add_argument("--to", default=str(BACKEND / "backups"),
                        help="where to write (default: backend/backups)")
    parser.add_argument("--with-photos", action="store_true",
                        help="zip the snapshot together with uploads/")
    parser.add_argument("--csv", action="store_true",
                        help="also write one CSV per table")
    args = parser.parse_args()

    settings = get_settings()
    source = settings.db_path
    if not source.exists():
        print(f"No database at {source}")
        return 1

    dest_dir = Path(args.to).expanduser()
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")

    db_copy = snapshot(source, dest_dir / f"bhoomi-{stamp}.sqlite3")
    size = db_copy.stat().st_size / 1024
    print(f"database  {db_copy}  ({size:.0f} KB)")

    if args.csv:
        folder = dest_dir / f"bhoomi-{stamp}-csv"
        for path in dump_csv(source, folder):
            print(f"csv       {path}")

    if args.with_photos:
        archive = dest_dir / f"bhoomi-{stamp}.zip"
        uploads = settings.uploads_dir
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_copy, db_copy.name)
            if uploads.exists():
                for photo in sorted(uploads.rglob("*")):
                    if photo.is_file():
                        zf.write(photo, f"uploads/{photo.relative_to(uploads)}")
        print(f"archive   {archive}  ({archive.stat().st_size / 1024:.0f} KB, database + photos)")
        db_copy.unlink()

    print("\nThis file holds phone numbers and password hashes. Keep it off shared drives.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
