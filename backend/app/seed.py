"""Demo content so a fresh database is not an empty site.

Runs once, only when there are no accounts at all, and only when
BHOOMI_SEED_DEMO is on. The people and the survey numbers are invented; the
districts, taluks, crops and prices are the kind you would actually see in
Karnataka.
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
            taluk="Chikkodi", is_admin=True,
        )
        shalini = db.create_user(
            conn, name="Shalini Desai", email="shalini@example.com", phone="9876500002",
            password_hash=pw, roles="landowner,investor", district="Belagavi", taluk="Athani",
        )
        asha = db.create_user(
            conn, name="Asha Patil", email="asha@example.com", phone="9876500003",
            password_hash=pw, roles="farmer,grower", district="Bagalkote", taluk="Mudhol",
        )
        ravi = db.create_user(
            conn, name="Ravi Kulkarni", email="ravi@example.com", phone="9876500004",
            password_hash=pw, roles="investor", district="Bengaluru Urban", taluk="Anekal",
        )
        lakshmi = db.create_user(
            conn, name="Lakshmi Gowda", email="lakshmi@example.com", phone="9876500006",
            password_hash=pw, roles="grower", district="Mysuru", taluk="Mysuru",
        )
        mahadev = db.create_user(
            conn, name="Mahadev Hugar", email="mahadev@example.com", phone="9876500005",
            password_hash=pw, roles="grower,farmer", district="Vijayapura", taluk="Indi",
        )

        # ---- land on offer -------------------------------------------------
        db.create_listing(conn, gunesh, {
            "title": "3 acres with a borewell, off the Nipani road",
            "survey_no": "215", "district": "Belagavi", "taluk": "Chikkodi", "acres": 3.0,
            "water_source": "Borewell", "water_hours": "6 hours a week, shared",
            "soil": "Black cotton, medium deep", "road_access": "Cart track, 400 m from the tar road",
            "last_crop": "Tur, two seasons ago", "suitable_crops": "Ragi, Jowar, Tur, Chana",
            "term_months": 11, "rent_per_acre": 18000, "share_terms": "", "status": "open",
            "notes": "Part of our own 15 acres. We are not farming this parcel this year and "
                     "would rather it was cropped than left fallow. Bunds need a day's work. "
                     "Residue stays on the field.",
        })
        db.create_listing(conn, shalini, {
            "title": "5.5 acres, canal water, near Athani",
            "survey_no": "88/2", "district": "Belagavi", "taluk": "Athani", "acres": 5.5,
            "water_source": "Canal", "water_hours": "Rotational, 8 hours a fortnight",
            "soil": "Medium black", "road_access": "On the tar road",
            "last_crop": "Sugarcane, ratoon removed",
            "suitable_crops": "Jowar, Maize, Onion, Vegetables",
            "term_months": 11, "rent_per_acre": None,
            "share_terms": "One third of the crop; owner pays the water charges", "status": "open",
            "notes": "My family has moved to Bengaluru and nobody is farming it. I want it "
                     "written down properly this time — the last arrangement was a handshake "
                     "and it went badly for both of us. No sugarcane.",
        })
        db.create_listing(conn, mahadev, {
            "title": "2 acres, rain-fed, behind the village school",
            "survey_no": "91", "district": "Vijayapura", "taluk": "Indi", "acres": 2.0,
            "water_source": "Rain-fed", "water_hours": "", "soil": "Light, murmad",
            "road_access": "Village road", "last_crop": "Bajra",
            "suitable_crops": "Jowar, Tur, Fodder",
            "term_months": 11, "rent_per_acre": 7000, "share_terms": "", "status": "matched",
            "notes": "Small, honest piece of land. Suits jowar or a pulse. In talks with a "
                     "farmer from the next village.",
        })

        # ---- crop plans ----------------------------------------------------
        chana = db.create_project(conn, gunesh, {
            "kind": "crop", "title": "Chana on BS-04, the lower field",
            "parcel_label": "BS-04, the lower field", "survey_no": "212/3",
            "district": "Belagavi", "taluk": "Chikkodi", "acres": 3.2,
            "budget": 96000, "expected_revenue": 140400,
            "investor_pct": 70, "grower_pct": 30, "status": "open",
            "crop": "Chana (gram)", "season_label": "Rabi 2026",
            "sowing_window": "Mid-October to early November",
            "expected_quintals": 26, "expected_price": 5400,
            "animal": "", "herd_size": 0, "cycle_months": 0, "shed": "", "water": "", "fodder": "",
            "unit_price": 0, "total_units": 0, "max_investors": 20,
            "plan_note": "Same parcel we grew chana on in 2024, which gave 8.4 quintals an acre. "
                         "Budget covers certified seed, one basal dose, two sprays, three "
                         "irrigations off the borewell and harvest labour. The 26 quintals "
                         "assumes an ordinary year; 2023 gave us 19 on the same ground.",
        })
        tur = db.create_project(conn, gunesh, {
            "kind": "crop", "title": "Tur on BS-02, the upper field",
            "parcel_label": "BS-02, the upper field", "survey_no": "212/1",
            "district": "Belagavi", "taluk": "Chikkodi", "acres": 2.4,
            "budget": 62000, "expected_revenue": 100800,
            "investor_pct": 60, "grower_pct": 40, "status": "growing",
            "crop": "Tur (pigeon pea)", "season_label": "Kharif 2026",
            "sowing_window": "First week of June",
            "expected_quintals": 14, "expected_price": 7200,
            "animal": "", "herd_size": 0, "cycle_months": 0, "shed": "", "water": "", "fodder": "",
            "unit_price": 0, "total_units": 0, "max_investors": 20,
            "plan_note": "Long-duration tur, intercropped with a short pulse on the borders. "
                         "This one is already in the ground and funded from our own pocket — "
                         "it is here so you can watch a cycle run before you back one.",
        })
        db.create_project(conn, asha, {
            "kind": "crop", "title": "Jowar on the leased canal parcel",
            "parcel_label": "Leased parcel, Sy. 88/2", "survey_no": "88/2",
            "district": "Belagavi", "taluk": "Athani", "acres": 5.5,
            "budget": 78000, "expected_revenue": 102300,
            "investor_pct": 65, "grower_pct": 35, "status": "open",
            "crop": "Jowar", "season_label": "Rabi 2026", "sowing_window": "Late September",
            "expected_quintals": 33, "expected_price": 3100,
            "animal": "", "herd_size": 0, "cycle_months": 0, "shed": "", "water": "", "fodder": "",
            "unit_price": 0, "total_units": 0, "max_investors": 20,
            "plan_note": "I farm 4 acres of my own and want to take on the canal parcel next to "
                         "it. Jowar because the water is rotational and I know what it does "
                         "with eight hours a fortnight.",
        })

        # ---- livestock -----------------------------------------------------
        sheep = db.create_project(conn, mahadev, {
            "kind": "livestock", "title": "Forty ewes on two acres of grazing",
            "parcel_label": "Home parcel", "survey_no": "104/2",
            "district": "Vijayapura", "taluk": "Indi", "acres": 2.0,
            "budget": 340000, "expected_revenue": 520000,
            "investor_pct": 60, "grower_pct": 40, "status": "open",
            "crop": "", "season_label": "", "sowing_window": "",
            "expected_quintals": 0, "expected_price": 0,
            "animal": "Sheep", "herd_size": 40, "cycle_months": 9,
            "shed": "Existing shed, 40 by 20 feet, tin roof",
            "water": "Borewell, year round", "fodder": "One acre of napier, rest grazed and bought in",
            "unit_price": 0, "total_units": 0, "max_investors": 20,
            "plan_note": "My family has kept sheep for three generations. Forty Deccani ewes and "
                         "two rams. Budget is the animals, nine months of feed, vaccination and "
                         "a helper. Lambs sell at Indi market; the ewes stay for the next cycle. "
                         "Losses happen — I lost four in 2024 to blue tongue — and that is in the "
                         "number I have given you, not hidden under it.",
        })
        db.create_project(conn, asha, {
            "kind": "livestock", "title": "Ten-cow dairy unit, Mudhol",
            "parcel_label": "Home parcel", "survey_no": "56",
            "district": "Bagalkote", "taluk": "Mudhol", "acres": 1.5,
            "budget": 620000, "expected_revenue": 890000,
            "investor_pct": 65, "grower_pct": 35, "status": "open",
            "crop": "", "season_label": "", "sowing_window": "",
            "expected_quintals": 0, "expected_price": 0,
            "animal": "Dairy cattle", "herd_size": 10, "cycle_months": 18,
            "shed": "To be built — costed in the budget",
            "water": "Borewell", "fodder": "Two acres of napier and maize silage",
            "unit_price": 0, "total_units": 0, "max_investors": 20,
            "plan_note": "Ten HF crosses, milk to the village society at the state rate. "
                         "Eighteen months covers the shed, the animals and the first lactation.",
        })

        # ---- a small space ---------------------------------------------------
        mushrooms = db.create_project(conn, lakshmi, {
            "kind": "space", "title": "Oyster mushrooms on a 30 by 40 site",
            "parcel_label": "Site 214, Vijayanagar 3rd stage", "survey_no": "",
            "district": "Mysuru", "taluk": "Mysuru", "acres": round(1200 / 43560, 4),
            "budget": 180000, "expected_revenue": 360000,
            "investor_pct": 60, "grower_pct": 40, "status": "open",
            "activity": "Mushroom", "area_sqft": 1200,
            "shed": "Empty 30 by 40 site with a tin shed over the back half",
            "water": "Corporation water and single-phase power",
            "cycle_months": 12,
            "plan_note": "I have grown oyster mushrooms in bags at home for two seasons, about "
                         "two hundred bags at a time, and lost roughly a third of the first "
                         "batch to contamination before I got the room right. The budget is "
                         "the racks, shade net and a fogger, then spawn, paddy straw and labour "
                         "for about five batches over the year. The revenue figure assumes I "
                         "sell fresh to two hotels and a vegetable shop at a little under two "
                         "hundred rupees a kilo, and that the first batch is a poor one.",
        })

        # ---- shares in a big parcel ----------------------------------------
        big = db.create_project(conn, shalini, {
            "kind": "shares", "title": "Twenty-two acres at Athani, in shares",
            "parcel_label": "The Athani block", "survey_no": "88/1, 88/3",
            "district": "Belagavi", "taluk": "Athani", "acres": 22.0,
            "budget": 2000000, "expected_revenue": 3100000,
            "investor_pct": 70, "grower_pct": 30, "status": "open",
            "crop": "", "season_label": "", "sowing_window": "",
            "expected_quintals": 0, "expected_price": 0,
            "animal": "", "herd_size": 0, "cycle_months": 0, "shed": "", "water": "", "fodder": "",
            "unit_price": 25000, "total_units": 80, "max_investors": 20,
            "plan_note": "Twenty-two contiguous acres on canal water, farmed as one block by a "
                         "team Asha leads. Maize and onion in rotation. Twenty lakh covers a "
                         "full year of inputs, labour, water charges and harvest. Eighty shares "
                         "of twenty-five thousand; at most twenty people, which is the cap that "
                         "keeps this out of collective-investment territory until counsel says "
                         "otherwise. You are buying a share of one year's work on the block, "
                         "not a piece of the land.",
        })

        # ---- interest and logs ---------------------------------------------
        db.upsert_pledge(conn, chana, ravi, 40000, "Happy to go higher if the pool has room.")
        db.upsert_pledge(conn, chana, shalini, 25000, "")
        db.upsert_pledge(conn, sheep, ravi, 60000, "Interested if the vet cover is written in.")
        db.upsert_pledge(conn, mushrooms, ravi, 30000, "Would like to see the first batch first.")
        db.upsert_pledge(conn, big, ravi, 6 * 25000, "Six shares.", units=6)

        db.add_project_update(conn, tur, "Sowed 2.4 acres on the 12th. Seed rate a little high "
                                         "on the western end where the drill blocked.", 18500)
        db.add_project_update(conn, tur, "First weeding done by hand, four labourers for two days. "
                                         "No pest pressure worth spraying yet.", 27000)

        db.create_inquiry(conn, 2, asha,
                          "I farm 4 acres next to this parcel and I can manage the canal "
                          "rotation. Happy to take it for 11 months and sign properly. "
                          "Can we talk this week?")
        conn.commit()

    log.info("Seeded demo content. Log in as gunesh@example.com / %s", DEMO_PASSWORD)
    return True
