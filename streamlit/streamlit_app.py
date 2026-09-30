"""A Streamlit front door for Bhoomi Share.

Streamlit Community Cloud runs Streamlit scripts only. It cannot run the
FastAPI app itself, which needs its own web server and a database. So the real
site is hosted elsewhere (see ../DEPLOY.md: Render + Neon is free) and this page
is a front door to it: a short introduction and a button that opens the site.

It can also embed the site in a frame, but that is off by default because it
has a cost: browsers block third-party cookies inside a frame, so signing in
does not work in the embedded copy. Reading pages, the calculators, the ledger
and the map all work. To allow embedding, set on the real site:
    BHOOMI_FRAME_ANCESTORS=https://*.streamlit.app

Set the site's address in Streamlit's Secrets as:   SITE_URL = "https://your-site.example"
"""

import os

import streamlit as st

st.set_page_config(page_title="Bhoomi Share", page_icon="🌾", layout="centered")

SITE_URL = (st.secrets.get("SITE_URL") if hasattr(st, "secrets") else None) or os.environ.get("SITE_URL", "")
SITE_URL = SITE_URL.rstrip("/")

st.title("Bhoomi Share")
st.caption("Five ways to work land and space in Karnataka, district by district.")

st.markdown(
    """
**Land, money and hands, finally in one place.** Fund a crop season, back a livestock unit,
put a small space to work, take a share of a big parcel, or licence land you are not farming.
Every plan shows its costs, its split and its bad case.

- 🧮 **Ways to earn**: calculators that show the failed season, not just the good one
- 📒 **Farm ledger**: every plan gets an account that has to add up
- 📉 **Money-at-risk**: the chance a plan falls short, and which fix pays back first
- 🗺️ **Karnataka map**: where farming is strongest and which model fits each district

*Pre-launch. No money moves through the site. Example data is invented.*
"""
)

if not SITE_URL:
    st.warning(
        "Set `SITE_URL` in this app's Secrets to the address of the hosted site "
        "(see DEPLOY.md for the free Render + Neon setup)."
    )
else:
    c1, c2, c3 = st.columns(3)
    c1.link_button("Open the site", SITE_URL, type="primary", use_container_width=True)
    c2.link_button("Try the example farm", f"{SITE_URL}/ledger", use_container_width=True)
    c3.link_button("Ways to earn", f"{SITE_URL}/earn", use_container_width=True)

    with st.expander("Preview the site here (sign-in will not work inside a frame)"):
        st.components.v1.iframe(SITE_URL, height=720, scrolling=True)
        st.caption(
            "If this is blank, the site has not allowed framing yet: set "
            "BHOOMI_FRAME_ANCESTORS=https://*.streamlit.app on it."
        )
