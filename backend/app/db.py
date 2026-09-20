"""SQLite storage for the whole site.

Still stdlib sqlite3: this is a pilot whose entire dataset fits in a file we can
copy off the box. Every query lives here so the routers stay readable.

One table holds all three funded things — a crop season, a livestock unit, and a
big parcel split into units — separated by `project.kind`. They share an owner, a
parcel, a budget, a split and a set of photographs; only a handful of columns
differ, and keeping them together means one set of queries, one meter, one card.
"""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

# A parcel this size or larger may be offered as units.
BIG_LAND_ACRES = 5.0
DEFAULT_MAX_INVESTORS = 20

KINDS = ("crop", "livestock", "shares")
ANIMALS = ("Sheep", "Goat", "Dairy cattle", "Poultry", "Other")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    phone         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    roles         TEXT NOT NULL DEFAULT '',
    district      TEXT NOT NULL DEFAULT '',
    taluk         TEXT NOT NULL DEFAULT '',
    is_admin      INTEGER NOT NULL DEFAULT 0,
    tour_done     INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS listing (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id       INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    title          TEXT NOT NULL,
    survey_no      TEXT NOT NULL DEFAULT '',
    district       TEXT NOT NULL,
    taluk          TEXT NOT NULL DEFAULT '',
    acres          REAL NOT NULL,
    water_source   TEXT NOT NULL DEFAULT '',
    water_hours    TEXT NOT NULL DEFAULT '',
    soil           TEXT NOT NULL DEFAULT '',
    road_access    TEXT NOT NULL DEFAULT '',
    last_crop      TEXT NOT NULL DEFAULT '',
    suitable_crops TEXT NOT NULL DEFAULT '',
    term_months    INTEGER NOT NULL DEFAULT 11,
    rent_per_acre  INTEGER,
    share_terms    TEXT NOT NULL DEFAULT '',
    notes          TEXT NOT NULL DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'open',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inquiry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id  INTEGER NOT NULL REFERENCES listing(id) ON DELETE CASCADE,
    sender_id   INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    message     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'new',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id          INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    kind              TEXT NOT NULL,
    title             TEXT NOT NULL,
    parcel_label      TEXT NOT NULL DEFAULT '',
    survey_no         TEXT NOT NULL DEFAULT '',
    district          TEXT NOT NULL,
    taluk             TEXT NOT NULL DEFAULT '',
    acres             REAL NOT NULL,
    budget            INTEGER NOT NULL,
    expected_revenue  INTEGER NOT NULL DEFAULT 0,
    investor_pct      INTEGER NOT NULL DEFAULT 70,
    grower_pct        INTEGER NOT NULL DEFAULT 30,
    plan_note         TEXT NOT NULL DEFAULT '',
    status            TEXT NOT NULL DEFAULT 'open',

    -- crop
    crop              TEXT NOT NULL DEFAULT '',
    season_label      TEXT NOT NULL DEFAULT '',
    sowing_window     TEXT NOT NULL DEFAULT '',
    expected_quintals REAL NOT NULL DEFAULT 0,
    expected_price    INTEGER NOT NULL DEFAULT 0,

    -- livestock
    animal            TEXT NOT NULL DEFAULT '',
    herd_size         INTEGER NOT NULL DEFAULT 0,
    cycle_months      INTEGER NOT NULL DEFAULT 0,
    shed              TEXT NOT NULL DEFAULT '',
    water             TEXT NOT NULL DEFAULT '',
    fodder            TEXT NOT NULL DEFAULT '',

    -- shares
    unit_price        INTEGER NOT NULL DEFAULT 0,
    total_units       INTEGER NOT NULL DEFAULT 0,
    max_investors     INTEGER NOT NULL DEFAULT 20,

    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pledge (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    investor_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    amount      INTEGER NOT NULL,
    units       INTEGER NOT NULL DEFAULT 0,
    note        TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'interest',
    created_at  TEXT NOT NULL,
    UNIQUE (project_id, investor_id)
);

CREATE TABLE IF NOT EXISTS project_update (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    spend      INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS photo (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_kind TEXT NOT NULL,            -- 'listing' or 'project'
    owner_id   INTEGER NOT NULL,
    path       TEXT NOT NULL,
    caption    TEXT NOT NULL DEFAULT '',
    sort       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS waitlist (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    phone      TEXT NOT NULL UNIQUE,
    role       TEXT NOT NULL,
    place      TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS submission (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_hash    TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS submission_ip_time ON submission (ip_hash, created_at);
CREATE INDEX IF NOT EXISTS listing_status ON listing (status, district);
CREATE INDEX IF NOT EXISTS project_kind_status ON project (kind, status, district);
CREATE INDEX IF NOT EXISTS pledge_project ON pledge (project_id);
CREATE INDEX IF NOT EXISTS inquiry_listing ON inquiry (listing_id);
CREATE INDEX IF NOT EXISTS photo_owner ON photo (owner_kind, owner_id, sort);
"""


# --------------------------------------------------------------------------- #
# plumbing
# --------------------------------------------------------------------------- #

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return utcnow().isoformat()


def hash_ip(ip: str, salt: str) -> str:
    """We never store a raw IP; the hash only exists to count submissions."""
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:32]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def closing_conn(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


# Columns added after the first release. CREATE TABLE IF NOT EXISTS will not add
# them to a database that already exists, so they are applied in place — this
# database holds real accounts and is never to be rebuilt from scratch.
ADDED_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("user", "tour_done", "INTEGER NOT NULL DEFAULT 0"),
)


def migrate(conn: sqlite3.Connection) -> list[str]:
    applied = []
    for table, column, spec in ADDED_COLUMNS:
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {spec}")
            applied.append(f"{table}.{column}")
    return applied


def init_db(db_path: Path) -> None:
    with closing_conn(db_path) as conn:
        conn.executescript(SCHEMA)
        migrate(conn)
        conn.commit()


def one(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def all_rows(conn: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params))


# --------------------------------------------------------------------------- #
# users
# --------------------------------------------------------------------------- #

def create_user(
    conn: sqlite3.Connection,
    *,
    name: str,
    email: str,
    phone: str,
    password_hash: str,
    roles: str,
    district: str,
    taluk: str = "",
    is_admin: bool = False,
) -> int:
    cur = conn.execute(
        """INSERT INTO user (name, email, phone, password_hash, roles, district, taluk,
                             is_admin, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, email.lower(), phone, password_hash, roles, district, taluk,
         1 if is_admin else 0, now_iso()),
    )
    return int(cur.lastrowid)


def user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return one(conn, "SELECT * FROM user WHERE email = ?", (email.lower(),))


def user_by_id(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return one(conn, "SELECT * FROM user WHERE id = ?", (user_id,))


def user_by_phone(conn: sqlite3.Connection, phone: str) -> sqlite3.Row | None:
    return one(conn, "SELECT * FROM user WHERE phone = ?", (phone,))


def mark_tour_done(conn: sqlite3.Connection, user_id: int, done: bool = True) -> None:
    conn.execute("UPDATE user SET tour_done = ? WHERE id = ?", (1 if done else 0, user_id))


def update_profile(
    conn: sqlite3.Connection, user_id: int, *, name: str, roles: str, district: str, taluk: str
) -> None:
    conn.execute(
        "UPDATE user SET name = ?, roles = ?, district = ?, taluk = ? WHERE id = ?",
        (name, roles, district, taluk, user_id),
    )


# --------------------------------------------------------------------------- #
# photos
# --------------------------------------------------------------------------- #

def add_photo(
    conn: sqlite3.Connection, owner_kind: str, owner_id: int, path: str, caption: str = ""
) -> int:
    row = one(
        conn,
        "SELECT COALESCE(MAX(sort), -1) + 1 AS next FROM photo WHERE owner_kind = ? AND owner_id = ?",
        (owner_kind, owner_id),
    )
    cur = conn.execute(
        """INSERT INTO photo (owner_kind, owner_id, path, caption, sort, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (owner_kind, owner_id, path, caption, int(row["next"]) if row else 0, now_iso()),
    )
    return int(cur.lastrowid)


def photos_for(conn: sqlite3.Connection, owner_kind: str, owner_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        "SELECT * FROM photo WHERE owner_kind = ? AND owner_id = ? ORDER BY sort, id",
        (owner_kind, owner_id),
    )


def photo_count(conn: sqlite3.Connection, owner_kind: str, owner_id: int) -> int:
    row = one(
        conn,
        "SELECT COUNT(*) AS n FROM photo WHERE owner_kind = ? AND owner_id = ?",
        (owner_kind, owner_id),
    )
    return int(row["n"]) if row else 0


def photo_by_id(conn: sqlite3.Connection, photo_id: int) -> sqlite3.Row | None:
    return one(conn, "SELECT * FROM photo WHERE id = ?", (photo_id,))


def delete_photo(conn: sqlite3.Connection, photo_id: int) -> bool:
    return conn.execute("DELETE FROM photo WHERE id = ?", (photo_id,)).rowcount > 0


def delete_photos_for(conn: sqlite3.Connection, owner_kind: str, owner_id: int) -> list[str]:
    """Delete the rows and hand back the paths so the caller can unlink files."""
    paths = [r["path"] for r in photos_for(conn, owner_kind, owner_id)]
    conn.execute("DELETE FROM photo WHERE owner_kind = ? AND owner_id = ?", (owner_kind, owner_id))
    return paths


def cover_photos(conn: sqlite3.Connection, owner_kind: str, ids: Sequence[int]) -> dict[int, str]:
    """First photo per owner, for cards. One query instead of N."""
    if not ids:
        return {}
    marks = ",".join("?" for _ in ids)
    rows = all_rows(
        conn,
        f"""SELECT owner_id, path FROM photo
            WHERE owner_kind = ? AND owner_id IN ({marks})
            ORDER BY owner_id, sort, id""",
        (owner_kind, *ids),
    )
    cover: dict[int, str] = {}
    for r in rows:
        cover.setdefault(int(r["owner_id"]), r["path"])
    return cover


# --------------------------------------------------------------------------- #
# listings (land offered on a fixed-term licence)
# --------------------------------------------------------------------------- #

LISTING_COLUMNS = (
    "title", "survey_no", "district", "taluk", "acres", "water_source", "water_hours",
    "soil", "road_access", "last_crop", "suitable_crops", "term_months",
    "rent_per_acre", "share_terms", "notes", "status",
)


def create_listing(conn: sqlite3.Connection, owner_id: int, data: dict[str, Any]) -> int:
    cols = ", ".join(LISTING_COLUMNS)
    marks = ", ".join("?" for _ in LISTING_COLUMNS)
    cur = conn.execute(
        f"INSERT INTO listing (owner_id, {cols}, created_at, updated_at) "
        f"VALUES (?, {marks}, ?, ?)",
        (owner_id, *(data.get(c) for c in LISTING_COLUMNS), now_iso(), now_iso()),
    )
    return int(cur.lastrowid)


def update_listing(conn: sqlite3.Connection, listing_id: int, data: dict[str, Any]) -> None:
    sets = ", ".join(f"{c} = ?" for c in LISTING_COLUMNS)
    conn.execute(
        f"UPDATE listing SET {sets}, updated_at = ? WHERE id = ?",
        (*(data.get(c) for c in LISTING_COLUMNS), now_iso(), listing_id),
    )


def listing_by_id(conn: sqlite3.Connection, listing_id: int) -> sqlite3.Row | None:
    return one(
        conn,
        """SELECT l.*, u.name AS owner_name, u.district AS owner_district
           FROM listing l JOIN user u ON u.id = l.owner_id WHERE l.id = ?""",
        (listing_id,),
    )


def search_listings(
    conn: sqlite3.Connection,
    *,
    district: str = "",
    max_acres: float | None = None,
    min_acres: float | None = None,
    water_only: bool = False,
    status: str = "open",
    limit: int = 60,
) -> list[sqlite3.Row]:
    sql = [
        """SELECT l.*, u.name AS owner_name FROM listing l
           JOIN user u ON u.id = l.owner_id WHERE 1 = 1"""
    ]
    params: list[Any] = []
    if status:
        sql.append("AND l.status = ?")
        params.append(status)
    if district:
        sql.append("AND l.district = ?")
        params.append(district)
    if min_acres is not None:
        sql.append("AND l.acres >= ?")
        params.append(min_acres)
    if max_acres is not None:
        sql.append("AND l.acres <= ?")
        params.append(max_acres)
    if water_only:
        sql.append("AND l.water_source != '' AND LOWER(l.water_source) != 'rain-fed'")
    sql.append("ORDER BY l.updated_at DESC LIMIT ?")
    params.append(limit)
    return all_rows(conn, " ".join(sql), params)


def listings_for_owner(conn: sqlite3.Connection, owner_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        """SELECT l.*, (SELECT COUNT(*) FROM inquiry i WHERE i.listing_id = l.id) AS inquiry_count
           FROM listing l WHERE l.owner_id = ? ORDER BY l.updated_at DESC""",
        (owner_id,),
    )


def delete_listing(conn: sqlite3.Connection, listing_id: int) -> bool:
    return conn.execute("DELETE FROM listing WHERE id = ?", (listing_id,)).rowcount > 0


# --------------------------------------------------------------------------- #
# inquiries
# --------------------------------------------------------------------------- #

def create_inquiry(conn: sqlite3.Connection, listing_id: int, sender_id: int, message: str) -> int:
    cur = conn.execute(
        "INSERT INTO inquiry (listing_id, sender_id, message, created_at) VALUES (?, ?, ?, ?)",
        (listing_id, sender_id, message, now_iso()),
    )
    return int(cur.lastrowid)


def inquiries_for_owner(conn: sqlite3.Connection, owner_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        """SELECT i.*, l.title AS listing_title, l.id AS listing_id,
                  u.name AS sender_name, u.phone AS sender_phone, u.district AS sender_district
           FROM inquiry i
           JOIN listing l ON l.id = i.listing_id
           JOIN user u ON u.id = i.sender_id
           WHERE l.owner_id = ? ORDER BY i.created_at DESC""",
        (owner_id,),
    )


def inquiries_by_sender(conn: sqlite3.Connection, sender_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        """SELECT i.*, l.title AS listing_title, l.district
           FROM inquiry i JOIN listing l ON l.id = i.listing_id
           WHERE i.sender_id = ? ORDER BY i.created_at DESC""",
        (sender_id,),
    )


def set_inquiry_status(conn: sqlite3.Connection, inquiry_id: int, owner_id: int, status: str) -> bool:
    return conn.execute(
        """UPDATE inquiry SET status = ? WHERE id = ? AND listing_id IN
           (SELECT id FROM listing WHERE owner_id = ?)""",
        (status, inquiry_id, owner_id),
    ).rowcount > 0


# --------------------------------------------------------------------------- #
# projects (crop / livestock / shares)
# --------------------------------------------------------------------------- #

PROJECT_COLUMNS = (
    "kind", "title", "parcel_label", "survey_no", "district", "taluk", "acres",
    "budget", "expected_revenue", "investor_pct", "grower_pct", "plan_note", "status",
    "crop", "season_label", "sowing_window", "expected_quintals", "expected_price",
    "animal", "herd_size", "cycle_months", "shed", "water", "fodder",
    "unit_price", "total_units", "max_investors",
)


def create_project(conn: sqlite3.Connection, owner_id: int, data: dict[str, Any]) -> int:
    cols = ", ".join(PROJECT_COLUMNS)
    marks = ", ".join("?" for _ in PROJECT_COLUMNS)
    cur = conn.execute(
        f"INSERT INTO project (owner_id, {cols}, created_at, updated_at) "
        f"VALUES (?, {marks}, ?, ?)",
        (owner_id, *(data.get(c) for c in PROJECT_COLUMNS), now_iso(), now_iso()),
    )
    return int(cur.lastrowid)


def update_project(conn: sqlite3.Connection, project_id: int, data: dict[str, Any]) -> None:
    sets = ", ".join(f"{c} = ?" for c in PROJECT_COLUMNS)
    conn.execute(
        f"UPDATE project SET {sets}, updated_at = ? WHERE id = ?",
        (*(data.get(c) for c in PROJECT_COLUMNS), now_iso(), project_id),
    )


PROJECT_SELECT = """
SELECT p.*, u.name AS owner_name, u.district AS owner_home_district,
       COALESCE((SELECT SUM(amount) FROM pledge pl
                 WHERE pl.project_id = p.id AND pl.status != 'withdrawn'), 0) AS pledged,
       COALESCE((SELECT SUM(units) FROM pledge pl
                 WHERE pl.project_id = p.id AND pl.status != 'withdrawn'), 0) AS units_taken,
       (SELECT COUNT(*) FROM pledge pl
        WHERE pl.project_id = p.id AND pl.status != 'withdrawn') AS backers
FROM project p JOIN user u ON u.id = p.owner_id
"""


def project_by_id(conn: sqlite3.Connection, project_id: int) -> sqlite3.Row | None:
    return one(conn, PROJECT_SELECT + " WHERE p.id = ?", (project_id,))


def search_projects(
    conn: sqlite3.Connection,
    *,
    kind: str = "",
    district: str = "",
    query: str = "",
    status: str = "open",
    limit: int = 60,
) -> list[sqlite3.Row]:
    sql = [PROJECT_SELECT, "WHERE 1 = 1"]
    params: list[Any] = []
    if kind:
        sql.append("AND p.kind = ?")
        params.append(kind)
    if status:
        sql.append("AND p.status = ?")
        params.append(status)
    if district:
        sql.append("AND p.district = ?")
        params.append(district)
    if query:
        sql.append("AND (LOWER(p.crop) LIKE ? OR LOWER(p.animal) LIKE ? OR LOWER(p.title) LIKE ?)")
        like = f"%{query.lower()}%"
        params.extend([like, like, like])
    sql.append("ORDER BY p.updated_at DESC LIMIT ?")
    params.append(limit)
    return all_rows(conn, " ".join(sql), params)


def projects_for_owner(conn: sqlite3.Connection, owner_id: int) -> list[sqlite3.Row]:
    return all_rows(conn, PROJECT_SELECT + " WHERE p.owner_id = ? ORDER BY p.updated_at DESC",
                    (owner_id,))


def delete_project(conn: sqlite3.Connection, project_id: int) -> bool:
    return conn.execute("DELETE FROM project WHERE id = ?", (project_id,)).rowcount > 0


# --------------------------------------------------------------------------- #
# pledges and project updates
# --------------------------------------------------------------------------- #

def upsert_pledge(
    conn: sqlite3.Connection,
    project_id: int,
    investor_id: int,
    amount: int,
    note: str,
    units: int = 0,
) -> str:
    existing = one(
        conn, "SELECT id FROM pledge WHERE project_id = ? AND investor_id = ?",
        (project_id, investor_id),
    )
    if existing:
        conn.execute(
            """UPDATE pledge SET amount = ?, units = ?, note = ?, status = 'interest',
                                 created_at = ? WHERE id = ?""",
            (amount, units, note, now_iso(), existing["id"]),
        )
        return "updated"
    conn.execute(
        """INSERT INTO pledge (project_id, investor_id, amount, units, note, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (project_id, investor_id, amount, units, note, now_iso()),
    )
    return "created"


def withdraw_pledge(conn: sqlite3.Connection, project_id: int, investor_id: int) -> bool:
    return conn.execute(
        "UPDATE pledge SET status = 'withdrawn' WHERE project_id = ? AND investor_id = ?",
        (project_id, investor_id),
    ).rowcount > 0


def pledge_for(conn: sqlite3.Connection, project_id: int, investor_id: int) -> sqlite3.Row | None:
    return one(
        conn,
        """SELECT * FROM pledge WHERE project_id = ? AND investor_id = ?
           AND status != 'withdrawn'""",
        (project_id, investor_id),
    )


def pledges_for_project(conn: sqlite3.Connection, project_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        """SELECT p.*, u.name AS investor_name, u.phone AS investor_phone
           FROM pledge p JOIN user u ON u.id = p.investor_id
           WHERE p.project_id = ? AND p.status != 'withdrawn' ORDER BY p.created_at DESC""",
        (project_id,),
    )


def pledges_by_investor(conn: sqlite3.Connection, investor_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        """SELECT p.*, pr.title, pr.kind, pr.crop, pr.animal, pr.parcel_label, pr.district,
                  pr.status AS project_status, pr.investor_pct, pr.budget,
                  pr.unit_price, pr.total_units, pr.id AS project_id
           FROM pledge p JOIN project pr ON pr.id = p.project_id
           WHERE p.investor_id = ? AND p.status != 'withdrawn' ORDER BY p.created_at DESC""",
        (investor_id,),
    )


def add_project_update(conn: sqlite3.Connection, project_id: int, body: str, spend: int | None) -> int:
    cur = conn.execute(
        "INSERT INTO project_update (project_id, body, spend, created_at) VALUES (?, ?, ?, ?)",
        (project_id, body, spend, now_iso()),
    )
    return int(cur.lastrowid)


def updates_for_project(conn: sqlite3.Connection, project_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        "SELECT * FROM project_update WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    )


# --------------------------------------------------------------------------- #
# waitlist
# --------------------------------------------------------------------------- #

def recent_submission_count(conn: sqlite3.Connection, ip_hash: str, hours: int = 1) -> int:
    since = (utcnow() - timedelta(hours=hours)).isoformat()
    row = one(
        conn,
        "SELECT COUNT(*) AS n FROM submission WHERE ip_hash = ? AND created_at >= ?",
        (ip_hash, since),
    )
    return int(row["n"]) if row else 0


def log_submission(conn: sqlite3.Connection, ip_hash: str) -> None:
    conn.execute(
        "INSERT INTO submission (ip_hash, created_at) VALUES (?, ?)", (ip_hash, now_iso())
    )


def upsert_waitlist(
    conn: sqlite3.Connection, *, name: str, phone: str, role: str, place: str
) -> tuple[str, sqlite3.Row]:
    """Insert, or refresh the row for that phone number.

    A repeat submission is not an error: people change their mind about which
    side they are on.
    """
    now = now_iso()
    existing = one(conn, "SELECT * FROM waitlist WHERE phone = ?", (phone,))
    if existing is None:
        conn.execute(
            """INSERT INTO waitlist (name, phone, role, place, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, phone, role, place, now, now),
        )
        status = "joined"
    else:
        conn.execute(
            "UPDATE waitlist SET name = ?, role = ?, place = ?, updated_at = ? WHERE phone = ?",
            (name, role, place, now, phone),
        )
        status = "updated"
    row = one(conn, "SELECT * FROM waitlist WHERE phone = ?", (phone,))
    assert row is not None
    return status, row


def list_waitlist(
    conn: sqlite3.Connection, *, role: str | None = None, limit: int = 500, offset: int = 0
) -> list[sqlite3.Row]:
    sql = "SELECT * FROM waitlist"
    params: list[Any] = []
    if role:
        sql += " WHERE role = ?"
        params.append(role)
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    return all_rows(conn, sql, params)


def count_by_role(conn: sqlite3.Connection) -> dict[str, int]:
    return {r["role"]: int(r["n"]) for r in
            conn.execute("SELECT role, COUNT(*) AS n FROM waitlist GROUP BY role")}


def delete_waitlist_entry(conn: sqlite3.Connection, entry_id: int) -> bool:
    return conn.execute("DELETE FROM waitlist WHERE id = ?", (entry_id,)).rowcount > 0


# --------------------------------------------------------------------------- #
# admin counts
# --------------------------------------------------------------------------- #

def site_counts(conn: sqlite3.Connection) -> dict[str, int]:
    tables = ("user", "listing", "project", "pledge", "inquiry", "waitlist")
    return {t: int(one(conn, f"SELECT COUNT(*) AS n FROM {t}")["n"]) for t in tables}
