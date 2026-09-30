# Deploying Bhoomi Share

## First, what this app is

A **FastAPI** web app (Python) with server-rendered pages, plus a database. That
matters for hosting:

- **Streamlit Community Cloud cannot host it.** It only runs Streamlit scripts.
- Any host that runs a **Python web service or a Docker image** can. This repo
  ships a `Dockerfile`, so that is the most portable route.
- **Free hosts wipe their disk** whenever they redeploy or restart. So the
  database must be *outside* the host (hosted Postgres), and photographs are kept
  in that database too. Both are built in: set `DATABASE_URL` and it just works.

## The free path: Neon (database) + Render (web)

**1. Database: Neon.** Create a free project at neon.tech. Copy the
*pooled* connection string (it looks like
`postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require`).
That is your `DATABASE_URL`. The app creates its own tables on first start.

**2. Web: Render.** Push this repo to GitHub (it is already there), then in Render:
*New → Blueprint →* pick the repository. `render.yaml` sets everything up. Fill in
the two values it asks for:

| Variable | Value |
|---|---|
| `DATABASE_URL` | the Neon string from step 1 |
| `BHOOMI_SITE_URL` | your public URL, e.g. `https://bhoomi-share.onrender.com` |

The secrets (`BHOOMI_SECRET_KEY`, `BHOOMI_ADMIN_TOKEN`, `BHOOMI_IP_SALT`) are
generated for you. Render builds the Docker image, waits for `/healthz`, and goes
live.

**3. Make yourself an admin.** With `BHOOMI_SEED_DEMO=0` no demo accounts exist.
Sign up on the live site, then promote your account once, from your own machine:

```bash
cd backend
DATABASE_URL='<the Neon string>' .venv/bin/python scripts/make_admin.py you@example.com
```

**4. Check it.** Open `/healthz` (should say `{"ok":true,"db":"up"}`), `/karnataka`
(map and tiles load), `/earn` (calculators move), then sign up and post a test
listing with a photo, redeploy, and confirm the photo is still there.

## Other hosts

| Host | How |
|---|---|
| **Koyeb** | New service → GitHub → Dockerfile. Set the same env vars. Free instance available. |
| **Hugging Face Spaces** | New Space → *Docker*. Set `PORT=7860` and add `app_port: 7860` to a README front-matter. Free CPU tier. |
| **Fly.io / Railway** | Use the `Dockerfile` (or the `Procfile`). Both may need a card. |
| **Your own server** | `docker compose up --build` runs the app *and* a Postgres, as production would. |

## Environment variables

| Variable | What it does |
|---|---|
| `DATABASE_URL` | Postgres connection string. Unset = SQLite file (fine locally, not on free hosts). |
| `BHOOMI_SECRET_KEY` | Signs session cookies. **Required in production**; without it everyone is logged out on every restart. |
| `BHOOMI_ADMIN_TOKEN` | Guards the admin JSON API. Unset = those endpoints return 503. |
| `BHOOMI_IP_SALT` | Salt for the hashed IPs used in rate limiting. |
| `BHOOMI_COOKIE_SECURE` | `1` behind HTTPS (also turns on HSTS). The Dockerfile defaults it on. |
| `BHOOMI_SEED_DEMO` | `0` in production. `1` fills an empty database with demo accounts. |
| `BHOOMI_SITE_URL` | Public base URL, used for canonical links, the share image and the sitemap. |
| `BHOOMI_PHOTOS_IN_DB` | Store photographs in the database too. Default: on with Postgres. |
| `BHOOMI_TILE_URL`, `BHOOMI_TILE_ATTRIBUTION` | Map background. Default is OpenStreetMap's public server; see below. |
| `BHOOMI_DB_POOL` | Postgres connections kept open (default 5; keep small on free plans). |
| `BHOOMI_ALLOWED_ORIGINS` | Only if another site calls the JSON API from a browser. |
| `WEB_CONCURRENCY` | Worker processes (default 1, right for a free 512 MB instance). |

Generate secrets with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`.

## Free-tier things to know

- **Cold starts.** Free web services sleep when idle and take ~30 seconds to wake.
  Fine for a pilot. A paid instance removes it.
- **Map tiles.** OpenStreetMap's public tile server is for light use. If the site
  gets busy, switch to a provider with its own terms (MapTiler, Stadia, Mapbox) by
  setting `BHOOMI_TILE_URL` (and `BHOOMI_TILE_ATTRIBUTION`), with no code change.
  The Content-Security-Policy follows that setting automatically.
- **Backups.** Neon keeps a short history on the free plan. For your own copy:
  `pg_dump "$DATABASE_URL" > backup.sql`.
- **Boundaries data.** District outlines are DataMeet's Census 2011 boundaries
  (MIT). Regenerate with `scripts/build_geo.py` if you ever want to change them.

## Before you go live

This site describes a model that touches securities and tenancy law, and it says
so on the page. Ahead of any real money or land:

- [ ] Counsel has reviewed the structure and the agreements (the site already
      states it is pre-launch; change that copy only when it is true).
- [ ] You have a real contact route (an email address or phone) and have added it
      to the About page. The site deliberately invents none.
- [ ] A privacy notice you are happy with. The fine-print page already lists what
      is stored; have it checked against your actual practice.
- [ ] `BHOOMI_SEED_DEMO=0`, real secrets set, `BHOOMI_COOKIE_SECURE=1`.
- [ ] Submit `/sitemap.xml` to Google Search Console.
- [ ] Decide whether the farming-tier and best-fit data on `/karnataka` should be
      replaced with official district statistics (`app/agri.py` is the one place).
