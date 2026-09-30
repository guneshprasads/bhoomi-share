#!/usr/bin/env python3
"""Promote an existing account to admin (or demote it).

    python scripts/make_admin.py you@example.com
    python scripts/make_admin.py you@example.com --remove

With BHOOMI_SEED_DEMO=0 (as in production) no demo admin exists, so the first
admin is made this way: sign up on the site normally, then run this once against
the same database (set DATABASE_URL, or BHOOMI_DB for the SQLite file).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402
from app.settings import get_settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("email")
    ap.add_argument("--remove", action="store_true", help="remove admin rights instead of granting them")
    args = ap.parse_args()

    target = get_settings().db_target
    db.init_db(target)
    with db.closing_conn(target) as conn:
        user = db.user_by_email(conn, args.email)
        if not user:
            print(f"No account with the email {args.email!r}. Sign up on the site first.")
            return 1
        conn.execute("UPDATE user SET is_admin = ? WHERE id = ?", (0 if args.remove else 1, user["id"]))
        conn.commit()
    print(f"{args.email} is {'no longer' if args.remove else 'now'} an admin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
