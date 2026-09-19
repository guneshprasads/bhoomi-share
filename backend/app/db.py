"""SQLite storage for the whole site.

Still stdlib sqlite3: this is a pre-launch pilot whose entire dataset fits in a
file we can copy off the box and hand to an accountant. Every query lives here
so the routers stay readable.
"""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

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
    state         TEXT NOT NULL DEFAULT '',
    is_admin      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS listing (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id      INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    survey_no     TEXT NOT NULL DEFAULT '',
    district      TEXT NOT NULL,
    state         TEXT NOT NULL,
    acres         REAL NOT NULL,
    water_source  TEXT NOT NULL DEFAULT '',
    water_hours   TEXT NOT NULL DEFAULT '',
    soil          TEXT NOT NULL DEFAULT '',
    road_access   TEXT NOT NULL DEFAULT '',
    last_crop     TEXT NOT NULL DEFAULT '',
    term_months   INTEGER NOT NULL DEFAULT 11,
    rent_per_acre INTEGER,
    share_terms   TEXT NOT NULL DEFAULT '',
    notes         TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'open',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inquiry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id  INTEGER NOT NULL REFERENCES listing(id) ON DELETE CASCADE,
    sender_id   INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    message     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'new',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS season (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    grower_id         INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    parcel_label      TEXT NOT NULL,
    survey_no         TEXT NOT NULL DEFAULT '',
    district          TEXT NOT NULL,
    state             TEXT NOT NULL,
    acres             REAL NOT NULL,
    crop              TEXT NOT NULL,
    season_label      TEXT NOT NULL,
    sowing_window     TEXT NOT NULL DEFAULT '',
    input_budget      INTEGER NOT NULL,
    expected_quintals REAL NOT NULL DEFAULT 0,
    expected_price    INTEGER NOT NULL DEFAULT 0,
    investor_pct      INTEGER NOT NULL DEFAULT 70,
    grower_pct        INTEGER NOT NULL DEFAULT 30,
    plan_note         TEXT NOT NULL DEFAULT '',
    status            TEXT NOT NULL DEFAULT 'open',
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pledge (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id   INTEGER NOT NULL REFERENCES season(id) ON DELETE CASCADE,
    investor_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    amount      INTEGER NOT NULL,
    note        TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'interest',
    created_at  TEXT NOT NULL,
    UNIQUE (season_id, investor_id)
);

CREATE TABLE IF NOT EXISTS season_update (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id  INTEGER NOT NULL REFERENCES season(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    spend      INTEGER,
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
CREATE INDEX IF NOT EXISTS season_status ON season (status, district);
CREATE INDEX IF NOT EXISTS pledge_season ON pledge (season_id);
CREATE INDEX IF NOT EXISTS inquiry_listing ON inquiry (listing_id);
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


def init_db(db_path: Path) -> None:
    with closing_conn(db_path) as conn:
        conn.executescript(SCHEMA)
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
    state: str,
    is_admin: bool = False,
) -> int:
    cur = conn.execute(
        """INSERT INTO user (name, email, phone, password_hash, roles, district, state,
                             is_admin, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, email.lower(), phone, password_hash, roles, district, state,
         1 if is_admin else 0, now_iso()),
    )
    return int(cur.lastrowid)


def user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return one(conn, "SELECT * FROM user WHERE email = ?", (email.lower(),))


def user_by_id(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return one(conn, "SELECT * FROM user WHERE id = ?", (user_id,))


def user_by_phone(conn: sqlite3.Connection, phone: str) -> sqlite3.Row | None:
    return one(conn, "SELECT * FROM user WHERE phone = ?", (phone,))


def update_profile(
    conn: sqlite3.Connection, user_id: int, *, name: str, roles: str, district: str, state: str
) -> None:
    conn.execute(
        "UPDATE user SET name = ?, roles = ?, district = ?, state = ? WHERE id = ?",
        (name, roles, district, state, user_id),
    )


# --------------------------------------------------------------------------- #
# listings
# --------------------------------------------------------------------------- #

LISTING_COLUMNS = (
    "title", "survey_no", "district", "state", "acres", "water_source", "water_hours",
    "soil", "road_access", "last_crop", "term_months", "rent_per_acre", "share_terms",
    "notes", "status",
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
        sql.append("AND (LOWER(l.district) LIKE ? OR LOWER(l.state) LIKE ?)")
        like = f"%{district.lower()}%"
        params.extend([like, like])
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
        """SELECT i.*, l.title AS listing_title, l.district, l.state
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
# seasons
# --------------------------------------------------------------------------- #

SEASON_COLUMNS = (
    "parcel_label", "survey_no", "district", "state", "acres", "crop", "season_label",
    "sowing_window", "input_budget", "expected_quintals", "expected_price",
    "investor_pct", "grower_pct", "plan_note", "status",
)


def create_season(conn: sqlite3.Connection, grower_id: int, data: dict[str, Any]) -> int:
    cols = ", ".join(SEASON_COLUMNS)
    marks = ", ".join("?" for _ in SEASON_COLUMNS)
    cur = conn.execute(
        f"INSERT INTO season (grower_id, {cols}, created_at, updated_at) "
        f"VALUES (?, {marks}, ?, ?)",
        (grower_id, *(data.get(c) for c in SEASON_COLUMNS), now_iso(), now_iso()),
    )
    return int(cur.lastrowid)


def update_season(conn: sqlite3.Connection, season_id: int, data: dict[str, Any]) -> None:
    sets = ", ".join(f"{c} = ?" for c in SEASON_COLUMNS)
    conn.execute(
        f"UPDATE season SET {sets}, updated_at = ? WHERE id = ?",
        (*(data.get(c) for c in SEASON_COLUMNS), now_iso(), season_id),
    )


SEASON_SELECT = """
SELECT s.*, u.name AS grower_name, u.district AS grower_district,
       COALESCE((SELECT SUM(amount) FROM pledge p
                 WHERE p.season_id = s.id AND p.status != 'withdrawn'), 0) AS pledged,
       (SELECT COUNT(*) FROM pledge p
        WHERE p.season_id = s.id AND p.status != 'withdrawn') AS backers
FROM season s JOIN user u ON u.id = s.grower_id
"""


def season_by_id(conn: sqlite3.Connection, season_id: int) -> sqlite3.Row | None:
    return one(conn, SEASON_SELECT + " WHERE s.id = ?", (season_id,))


def search_seasons(
    conn: sqlite3.Connection,
    *,
    district: str = "",
    crop: str = "",
    status: str = "open",
    limit: int = 60,
) -> list[sqlite3.Row]:
    sql = [SEASON_SELECT, "WHERE 1 = 1"]
    params: list[Any] = []
    if status:
        sql.append("AND s.status = ?")
        params.append(status)
    if district:
        sql.append("AND (LOWER(s.district) LIKE ? OR LOWER(s.state) LIKE ?)")
        like = f"%{district.lower()}%"
        params.extend([like, like])
    if crop:
        sql.append("AND LOWER(s.crop) LIKE ?")
        params.append(f"%{crop.lower()}%")
    sql.append("ORDER BY s.updated_at DESC LIMIT ?")
    params.append(limit)
    return all_rows(conn, " ".join(sql), params)


def seasons_for_grower(conn: sqlite3.Connection, grower_id: int) -> list[sqlite3.Row]:
    return all_rows(conn, SEASON_SELECT + " WHERE s.grower_id = ? ORDER BY s.updated_at DESC",
                    (grower_id,))


def delete_season(conn: sqlite3.Connection, season_id: int) -> bool:
    return conn.execute("DELETE FROM season WHERE id = ?", (season_id,)).rowcount > 0


# --------------------------------------------------------------------------- #
# pledges and season updates
# --------------------------------------------------------------------------- #

def upsert_pledge(
    conn: sqlite3.Connection, season_id: int, investor_id: int, amount: int, note: str
) -> str:
    existing = one(
        conn, "SELECT id FROM pledge WHERE season_id = ? AND investor_id = ?",
        (season_id, investor_id),
    )
    if existing:
        conn.execute(
            "UPDATE pledge SET amount = ?, note = ?, status = 'interest', created_at = ? WHERE id = ?",
            (amount, note, now_iso(), existing["id"]),
        )
        return "updated"
    conn.execute(
        "INSERT INTO pledge (season_id, investor_id, amount, note, created_at) VALUES (?, ?, ?, ?, ?)",
        (season_id, investor_id, amount, note, now_iso()),
    )
    return "created"


def withdraw_pledge(conn: sqlite3.Connection, season_id: int, investor_id: int) -> bool:
    return conn.execute(
        "UPDATE pledge SET status = 'withdrawn' WHERE season_id = ? AND investor_id = ?",
        (season_id, investor_id),
    ).rowcount > 0


def pledge_for(conn: sqlite3.Connection, season_id: int, investor_id: int) -> sqlite3.Row | None:
    return one(
        conn, "SELECT * FROM pledge WHERE season_id = ? AND investor_id = ?",
        (season_id, investor_id),
    )


def pledges_for_season(conn: sqlite3.Connection, season_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        """SELECT p.*, u.name AS investor_name, u.phone AS investor_phone
           FROM pledge p JOIN user u ON u.id = p.investor_id
           WHERE p.season_id = ? AND p.status != 'withdrawn' ORDER BY p.created_at DESC""",
        (season_id,),
    )


def pledges_by_investor(conn: sqlite3.Connection, investor_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        """SELECT p.*, s.parcel_label, s.crop, s.season_label, s.district, s.state,
                  s.status AS season_status, s.investor_pct, s.input_budget, s.id AS season_id
           FROM pledge p JOIN season s ON s.id = p.season_id
           WHERE p.investor_id = ? AND p.status != 'withdrawn' ORDER BY p.created_at DESC""",
        (investor_id,),
    )


def add_season_update(conn: sqlite3.Connection, season_id: int, body: str, spend: int | None) -> int:
    cur = conn.execute(
        "INSERT INTO season_update (season_id, body, spend, created_at) VALUES (?, ?, ?, ?)",
        (season_id, body, spend, now_iso()),
    )
    return int(cur.lastrowid)


def updates_for_season(conn: sqlite3.Connection, season_id: int) -> list[sqlite3.Row]:
    return all_rows(
        conn,
        "SELECT * FROM season_update WHERE season_id = ? ORDER BY created_at DESC",
        (season_id,),
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
    tables = ("user", "listing", "season", "pledge", "inquiry", "waitlist")
    return {t: int(one(conn, f"SELECT COUNT(*) AS n FROM {t}")["n"]) for t in tables}
