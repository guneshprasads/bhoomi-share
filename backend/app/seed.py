"""Demo content so a fresh database is not an empty site.

Runs once, only when there are no accounts at all, and only when
BHOOMI_SEED_DEMO is on. Everything it writes is made up except the shape of it,
which is the pilot on our own 15 acres.
"""

from __future__ import annotations

import logging
from pathlib import Path

from . import db
from .security import hash_password

log = logging.getLogger("bhoomi.seed")

DEMO_PASSWORD = "bhoomi-pilot"


def seed_if_empty(db_path: Path) -> bool:
    with db.closing_conn(db_path) as conn:
        if db.one(conn, "SELECT COUNT(*) AS n FROM user")["n"]:
            return False

        pw = hash_password(DEMO_PASSWORD)

        gunesh = db.create_user(
            conn, name="Gunesh Prasad", email="gunesh@example.com", phone="9876500001",
            password_hash=pw, roles="grower,landowner", district="Belagavi",
            state="Karnataka", is_admin=True,
        )
        shalini = db.create_user(
            conn, name="Shalini Desai", email="shalini@example.com", phone="9876500002",
            password_hash=pw, roles="landowner", district="Satara", state="Maharashtra",
        )
        asha = db.create_user(
            conn, name="Asha Patil", email="asha@example.com", phone="9876500003",
            password_hash=pw, roles="farmer,grower", district="Belagavi", state="Karnataka",
        )
        ravi = db.create_user(
            conn, name="Ravi Kulkarni", email="ravi@example.com", phone="9876500004",
            password_hash=pw, roles="investor", district="Pune", state="Maharashtra",
        )

        db.create_listing(conn, gunesh, {
            "title": "3 acres with a borewell, off the Nipani road",
            "survey_no": "215", "district": "Belagavi", "state": "Karnataka", "acres": 3.0,
            "water_source": "Borewell", "water_hours": "6 hours a week, shared",
            "soil": "Black cotton, medium deep", "road_access": "Cart track, 400 m from the tar road",
            "last_crop": "Tur, two seasons ago", "term_months": 11, "rent_per_acre": 18000,
            "share_terms": "", "status": "open",
            "notes": "Part of our own 15 acres. We are not farming this parcel this year and "
                     "would rather it was cropped than left fallow. Bunds need a day's work. "
                     "Residue stays on the field.",
        })
        db.create_listing(conn, shalini, {
            "title": "5.5 acres, canal water, near Phaltan",
            "survey_no": "88/2", "district": "Satara", "state": "Maharashtra", "acres": 5.5,
            "water_source": "Canal", "water_hours": "Rotational, 8 hours a fortnight",
            "soil": "Medium black", "road_access": "On the tar road",
            "last_crop": "Sugarcane, ratoon removed", "term_months": 11, "rent_per_acre": None,
            "share_terms": "One third of the crop; owner pays the water charges", "status": "open",
            "notes": "My family has moved to Pune and nobody is farming it. I want it written "
                     "down properly this time — the last arrangement was a handshake and it "
                     "went badly for both of us. No sugarcane.",
        })
        db.create_listing(conn, shalini, {
            "title": "2 acres, rain-fed, behind the village school",
            "survey_no": "91", "district": "Satara", "state": "Maharashtra", "acres": 2.0,
            "water_source": "Rain-fed", "water_hours": "", "soil": "Light, murmad",
            "road_access": "Village road", "last_crop": "Bajra", "term_months": 11,
            "rent_per_acre": 7000, "share_terms": "", "status": "matched",
            "notes": "Small, honest piece of land. Suits bajra or a pulse. In talks with a "
                     "farmer from the next village.",
        })

        chana = db.create_season(conn, gunesh, {
            "parcel_label": "BS-04, the lower field", "survey_no": "212/3",
            "district": "Belagavi", "state": "Karnataka", "acres": 3.2, "crop": "Chana (gram)",
            "season_label": "Rabi 2026", "sowing_window": "Mid-October to early November",
            "input_budget": 96000, "expected_quintals": 26, "expected_price": 5400,
            "investor_pct": 70, "grower_pct": 30, "status": "open",
            "plan_note": "Same parcel we grew chana on in 2024, which gave 8.4 quintals an acre. "
                         "Budget covers certified seed, one basal dose, two sprays, three "
                         "irrigations off the borewell and harvest labour. The 26 quintals "
                         "assumes an ordinary year; 2023 gave us 19 on the same ground.",
        })
        tur = db.create_season(conn, gunesh, {
            "parcel_label": "BS-02, the upper field", "survey_no": "212/1",
            "district": "Belagavi", "state": "Karnataka", "acres": 2.4, "crop": "Tur (pigeon pea)",
            "season_label": "Kharif 2026", "sowing_window": "First week of June",
            "input_budget": 62000, "expected_quintals": 14, "expected_price": 7200,
            "investor_pct": 60, "grower_pct": 40, "status": "growing",
            "plan_note": "Long-duration tur, intercropped with a short pulse on the borders. "
                         "This one is already in the ground and funded from our own pocket — "
                         "it is here so you can watch a season run before you back one.",
        })
        db.create_season(conn, asha, {
            "parcel_label": "Leased parcel, Sy. 88/2", "survey_no": "88/2",
            "district": "Satara", "state": "Maharashtra", "acres": 5.5, "crop": "Jowar",
            "season_label": "Rabi 2026", "sowing_window": "Late September",
            "input_budget": 78000, "expected_quintals": 33, "expected_price": 3100,
            "investor_pct": 65, "grower_pct": 35, "status": "open",
            "plan_note": "I farm 4 acres of my own and want to take on the canal parcel next to "
                         "it. Jowar because the water is rotational and I know what it does "
                         "with eight hours a fortnight.",
        })

        db.upsert_pledge(conn, chana, ravi, 40000, "Happy to go higher if the pool has room.")
        db.upsert_pledge(conn, chana, shalini, 25000, "")

        db.add_season_update(conn, tur, "Sowed 2.4 acres on the 12th. Seed rate a little high "
                                        "on the western end where the drill blocked.", 18500)
        db.add_season_update(conn, tur, "First weeding done by hand, four labourers for two days. "
                                        "No pest pressure worth spraying yet.", 27000)

        db.create_inquiry(conn, 2, asha,
                          "I farm 4 acres next to this parcel and I can manage the canal "
                          "rotation. Happy to take it for 11 months and sign properly. "
                          "Can we talk this week?")
        conn.commit()

    log.info("Seeded demo content. Log in as gunesh@example.com / %s", DEMO_PASSWORD)
    return True
