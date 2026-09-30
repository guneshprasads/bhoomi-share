# Bhoomi Share

An agriculture site for **Karnataka** that connects people who have **land or
space**, people who have **money**, and people who can **farm**, in five clear ways,
all on paper, in **English and ಕನ್ನಡ**. It is **pre-launch**: no money moves
through the site, and nothing on it is an offer to invest.

| If you are... | you can... |
|---|---|
| an **investor** | fund one crop, herd, batch cycle or share of a parcel, and see its bad case first |
| a **grower / keeper** | get a season funded and keep an agreed share |
| a **landowner** | licence idle land on a fixed-term agreement and earn rent |
| a **farmer** | find land by district, size and irrigation, and know your break-even before you sign |

The five models: **crop plans**, **livestock units**, **small spaces** (mushrooms,
vermicompost, microgreens), **land shares** and **leases**. Every funded plan follows
**one rule**: what the crop or animals sell for first repays the listed costs to
whoever paid them; what is left is split by the agreed percentages; a failed season
can return nothing. No return is guaranteed.

## Contents

1. [How it works](#how-it-works)
2. [The flow for a new user](#the-flow-for-a-new-user)
3. [Authentication and authorization](#authentication-and-authorization)
4. [The first-run tutorial](#the-first-run-tutorial)
5. [The product pages: earn, models, map, ledger, risk](#the-product-pages)
6. [Quick start](#run-it) · [Pages](#pages) · [API](#api) · [Layout](#how-it-is-put-together) · [Data](#data--where-it-lives-and-how-to-take-a-copy) · [Tests](#tests)
7. [Deploying, including why Streamlit cannot host this](#deploying)

---

## How it works

```
  browser ──HTTP──▶  FastAPI app (one process)
                       ├─ pages      server-rendered Jinja HTML, English + Kannada
                       ├─ JSON API   /api/...  (waitlist, calculators, ledger, risk)
                       ├─ engines    simulator.py, ledger.py, risk.py  (pure Python, tested)
                       └─ db.py      every SQL query, written once
                                        ├─ SQLite file   (default, local)
                                        └─ Postgres      (DATABASE_URL, for hosting)
```

- **Server-rendered, no build step.** Pages are Jinja templates with a little
  vanilla JavaScript for the sidebar, calculators, map and ledger. Every page is
  readable with JavaScript off.
- **The maths lives on the server.** The earnings calculators, the ledger checks and
  the risk simulation are plain Python functions with tests, reached through JSON
  endpoints, so what the page shows can never drift from what the tests prove.
- **Two databases, one set of queries.** SQLite for the laptop, Postgres for a host.
  A small adapter (`db.PgConn`) handles the dialect differences.
- **The ledger and risk pages are stateless.** Your ledger stays in your browser
  (session storage); the server checks and simulates it and stores nothing.
- **Security by default.** Strict Content-Security-Policy with per-request nonces,
  cross-site POST refusal, login throttling, hashed passwords, signed cookies.

## The flow for a new user

**1. Arrive and look around (no account needed).**
`/` explains the idea and shows live counts. From there, without signing up, you can:
use the **calculators** at `/earn`, read the **five models** at `/models`, explore the
**Karnataka map** at `/karnataka`, try the **example farm** at `/ledger` and
`/ledger/risk`, read the **stories**, **FAQ** and **fine print**, and browse open plans
(`/invest`) and parcels (`/land`). Language switches between English and ಕನ್ನಡ at any time.

**2. Join the waitlist (optional).** The form on the home page takes a name, a phone
number, which side you are on and your district. It is how we tell you when your
district opens. Nothing is offered or charged.

**3. Create an account.** `/signup`: name, email, phone, district (picked from the 31
Karnataka districts), at least one side (investor, grower, landowner, farmer; you can
change it later) and a password of 8+ characters. You are signed in straight away.

**4. The tutorial runs once.** On your first visit to your dashboard a six-step guided
tour shows what each part is for. You can skip it, and replay it any time with
**"Show me around again"** (`/dashboard?tour=1`).

**5. Do what your side does.**

| Side | Steps |
|---|---|
| **Landowner** | *List your land* (survey number, water source and hours, soil, road access, photographs) → farmers search by district and irrigation and **write to you** → agree terms → sign a fixed-term licence **on paper** |
| **Grower / keeper** | *Post a plan* (pick the kind; the form shows only the fields it needs; budget, expected sale, split, photographs) → people read it and **register interest** → keep the season **log** up to date |
| **Investor** | Browse plans → read the budget, photographs and the grower's log → **register interest** with an amount (a message, not a payment) → see the risk on the ledger pages first |
| **Farmer** | Search parcels → **write to the owner** → work out your break-even on `/earn` before you sign |

**6. Nothing is binding here.** Registering interest or writing to an owner is a
message that passes on your name, district and phone number. Any agreement, payment
and signature happens **on paper, between the people involved**, never through the site.

**7. Admins** (a separate flag on the account) see the waitlist, accounts, plans and
listings at `/admin`.

## Authentication and authorization

**Authentication: who you are.**
- **Sign up / log in / log out** are real and work today: `/signup`, `/login`, `POST /logout`.
- Passwords are **scrypt** hashes (stdlib, salted, never stored in the clear).
- A login sets a **signed session cookie** (`SameSite=Lax`, 30 days, `Secure` when
  `BHOOMI_COOKIE_SECURE=1`). The cookie holds only your user id, signed with
  `BHOOMI_SECRET_KEY`.
- Wrong email or password gives one vague message (it does not say which was wrong).
- **Failed logins are throttled**: more than `BHOOMI_LOGIN_LIMIT` (default 10) per hour
  from one connection gets a `429`. Counting uses a salted hash, never the raw IP.
- **Cross-site POSTs are refused**: a state-changing request whose `Origin` is another
  site gets a `403`.
- The `next` parameter after login only ever redirects **inside this site**.

**Authorization: what you may do.**
- **Roles** (`investor`, `grower`, `landowner`, `farmer`) are choices about which
  sections to show you, not permissions to do anything special.
- **Ownership is checked on every write.** Editing someone else's parcel, plan or
  season log is a `403`. Drafts are visible only to their owner.
- **Admin** is a separate flag that opens `/admin`. With demo data off, create the
  first admin with `python scripts/make_admin.py you@example.com` after signing up.
- The admin **JSON API** uses a token (`X-Admin-Token`) instead of a session, and
  returns `503` rather than falling open if no token is configured.

**Not built yet (be aware before real users):** email verification, password reset,
two-factor sign-in, and server-side session revocation (a cookie stays valid until it
expires or you log out on that browser). These are the next sensible additions.

## The first-run tutorial

The guided tour **is still there and working.** It is a dimmed overlay with a
spotlight on one thing at a time, six steps, in whichever language you are reading:
Welcome, Invest, Land on offer, Your plans, What you back, Your profile.

- It runs **once**, the first time a new account opens its dashboard.
- Whether you have seen it is stored **on your account**, not in the browser, so it
  does not reappear on a second device or vanish when you clear cookies.
- Replay it with **"Show me around again"** on the dashboard (`/dashboard?tour=1`).
- A step whose target is hidden (the nav links on a phone) still shows its words,
  centred, without the spotlight.

## The product pages

| Page | What it does |
|---|---|
| `/earn` | Four calculators (investor, grower, landowner, farmer) that always show the **failed season** and a **break-even**. Numbers come from `/api/simulate`. |
| `/models` | The five models compared, and one page per model: steps, an example budget, a worked example, risks, FAQ. |
| `/karnataka` | An **interactive map** of all 31 districts (Leaflet + OpenStreetMap; boundaries from DataMeet's Census 2011 data). Four layers: farming landscape, best-fit model, open right now, division. The farming tiers are qualitative background, labelled indicative, not statistics. |
| `/ledger` | **Check.** Import a CSV (or use the example farm). Every plan gets an account checked against four balance rules (+/-5%): the budget adds up, spend was logged, money in equals money out, enough past seasons. A trust score 0-100. *Not reported* is never read as zero. |
| `/ledger/risk` | **Predict and decide.** A seeded 2,000-season simulation per plan: chance the sale falls short of the costs, expected shortfall, a one-in-twenty bad case. Six fixes compared on the same draws, ranked by net benefit. A whole-holding "where to act first" table and a three-source reconciliation of the expected yield. |
| `/story`, `/foresight` | The problem, the idea and outcomes per side; a 2026-2036 foresight canvas. |

The **example holding is invented** and labelled so everywhere. Risk outputs are
**simulations from stated assumptions, not forecasts**, and every assumption is shown
and editable.

---

## Run it

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # then edit it
set -a && . ./.env && set +a    # or direnv, or a systemd EnvironmentFile

uvicorn app.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000/>. An empty database seeds itself with demo
accounts, parcels and plans (turn that off with `BHOOMI_SEED_DEMO=0`). Every
seeded account uses the password **`bhoomi-pilot`**:

| Email | Who they are |
|---|---|
| `gunesh@example.com` | grower + landowner, **admin** |
| `shalini@example.com` | landowner with two parcels |
| `asha@example.com` | farmer looking for land |
| `ravi@example.com` | investor backing a plan |

Generate the two secrets before you deploy:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # BHOOMI_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # BHOOMI_ADMIN_TOKEN
```

## Pages

| Path | What it is |
|---|---|
| `/` | The landing page: hero, live counts, roles, the five models, scenario bars, open plans, FAQ teaser, waitlist |
| `/earn` | Ways to earn: role tabs and live calculators (investor, grower, landowner, farmer) |
| `/ledger` | Farm ledger: import a CSV or try the example farm; balance checks, trust scores, money flows, yields, input costs |
| `/ledger/risk` | Money-at-risk: per-plan simulation, fixes compared, whole-holding ranking, three-source trust |
| `/story`, `/foresight` | The problem, idea and outcomes; the 2026-2036 foresight canvas |
| `/models`, `/models/{slug}` | The five models compared, and one page per model |
| `/how-it-works` | One funded season as a six-phase journey |
| `/stories` | Six illustrative worked examples |
| `/karnataka` | Interactive district map: farming tiers, best-fit model, live activity |
| `/faq`, `/about` | Questions and answers; the pilot and the principles |
| `/sitemap.xml`, `/robots.txt`, `/healthz` | SEO files and a health check for the host |
| `/invest` | All three funded kinds in one list, filterable by kind and district |
| `/seasons`, `/livestock`, `/spaces`, `/shares` | One kind each, same filters |
| `/projects/{id}` | The plan, the photographs, the budget maths, the log |
| `/land`, `/land/{id}` | Parcels on offer, filterable by district, size and irrigation |
| `/lang/kn`, `/lang/en` | Switch language; remembered in a cookie for a year |
| `/fine-print` | The law that shapes the product |
| `/signup`, `/login` | Accounts. Roles: investor, grower, landowner, farmer |
| `/dashboard` | Your parcels, the farmers asking about them, your plans, what you back |
| `/dashboard?tour=1` | Replays the first-run guided tour on demand |
| `/dashboard/listings/new` | List a parcel, with `/edit`, `/delete` and photo removal under the same path |
| `/dashboard/projects/new?kind=crop\|livestock\|space\|shares` | Post a plan; the form shows only the fields that kind needs |
| `/admin` | Waitlist, accounts, plans and listings. Admin accounts only |
| `/api/docs` | Generated API reference |

## API

| Method | Path | Who |
|---|---|---|
| `GET` | `/api/health` | public |
| `POST` | `/api/waitlist` | public — what the landing-page form posts |
| `GET` | `/api/listings`, `/api/projects`, `/api/districts` | public, read-only |
| `GET` | `/api/simulate/{kind}` | public: the earnings calculators |
| `GET/POST` | `/api/ledger/example`, `/api/ledger/import`, `/api/risk`, `/api/holding` | public, stateless: nothing is stored |
| `GET` | `/api/admin/waitlist`, `/api/admin/waitlist.csv` | `X-Admin-Token` |
| `DELETE` | `/api/admin/waitlist/{id}` | `X-Admin-Token` |

```bash
curl -s localhost:8000/api/waitlist -H 'Content-Type: application/json' \
  -d '{"name":"Asha Patil","phone":"+91 98765 43210","role":"Farmer","place":"Belagavi, Karnataka"}'

curl -s localhost:8000/api/admin/waitlist -H "X-Admin-Token: $BHOOMI_ADMIN_TOKEN"
```

The admin **pages** authenticate with your logged-in account; the admin **API**
uses the token, so scripts do not need a session. With no token configured those
endpoints return 503 rather than falling open.

## How it is put together

```
backend/
  app/
    main.py          app assembly, middleware, error pages
    settings.py      environment → a frozen Settings object
    db.py            schema and every SQL query in the project
    karnataka.py     the 31 districts, their divisions, and old-name aliases
    i18n.py          English and Kannada strings, and t()
    tour.py          the six first-run tour steps, in both languages
    photos.py        upload validation, resizing, EXIF/GPS stripping
    security.py      scrypt password hashing, session helpers, roles
    schemas.py       pydantic models for the JSON API
    templating.py    Jinja setup, ₹ formatting, flash messages, language
    deps.py          login/admin dependencies, typed 403 and 404
    seed.py          demo content for an empty database
    simulator.py     the earnings maths behind /earn (tested; no money moves)
    ledger.py        CSV ledger import, balance rules, trust scores
    risk.py          seeded simulation, fixes compared, reconciliation, holding ranking
    example.py       the invented example holding (labelled as such everywhere)
    content.py       models, stories and FAQ as data
    agri.py          farming tiers and best-fit models per district (indicative)
    hardening.py    security headers, CSP nonces, caching
    routers/         pages, marketing, seo, media, auth, land, projects,
                     dashboard, admin_pages, api
  scripts/           backup.py, make_admin.py, build_geo.py, make_og.py
  templates/         Jinja pages; base.html holds the shell, _browse.html the
                     four listing pages
  static/            styles.css (legacy) + site.css (design system v2), per-page
                     css/js, vendor/leaflet, data/karnataka_districts.geojson
  uploads/           photographs (gitignored)
  tests/             170 tests, runnable on SQLite or Postgres
```

Server-rendered HTML with POST-then-redirect. A small amount of vanilla JavaScript
adds the sidebar menu, the calculators, the map and the waitlist form. No build
step and no front-end framework; every page is readable with JS off.

### Behaviour worth knowing

- **Phone is the identity** on the waitlist. `+91 98765 43210`, `098765 43210`
  and `9876543210` are the same person; a repeat submission updates the row.
- **Validation messages are written for a person**, because the page prints them
  verbatim: `{"error": "...", "fields": {"phone": "..."}}`.
- **Rate limit** of `BHOOMI_RATE_LIMIT` waitlist submissions per hour per IP,
  counted against a salted hash. Raw IPs are never stored.
- **Honeypot**: an off-screen `company` field. Filled in, the response looks
  normal and nothing is written.
- **Districts are canonical.** "Ramanagara" and "Bengaluru Rural" resolve to the
  names they were renamed to in 2025; "Belgaum", "Mysore" and the rest resolve
  too, so search finds the parcel however people type it.
- **Photographs are re-encoded on upload** to at most 1600px, which strips the
  EXIF metadata — including the GPS coordinates a phone writes into every photo.
  Six per listing, 10 MB each, JPEG/PNG/WebP; HEIC is refused with an
  explanation rather than failing silently.
- **A small space is stored in acres as well as square feet**, so every query
  and filter that already understands acres keeps working. Its structure, water
  and plan length reuse the `shed`, `water` and `cycle_months` columns, and its
  form fields are named `space_*` so they cannot collide with the livestock
  fieldset on the same page. Anything over one acre is refused and pointed at a
  crop plan or shares.
- **A share is a share of one cycle's work, not of the land.** Units follow from
  the budget (₹20,00,000 at ₹25,000 a share is 80 shares), only parcels of five
  acres and up may be offered this way, and both the share count and the
  per-parcel people cap are enforced server-side.
- **A project's kind cannot change after posting** — people have already read it
  as one thing.
- **A new account gets a guided tour** of the dashboard once: a dimmed overlay
  with a cut-out around one thing at a time, six steps, in whichever language
  they are reading. The "seen it" flag lives on the user row, not in the
  browser, so it does not reappear on a second device or vanish when someone
  clears their browser. A step whose target is hidden (the nav links, on a
  phone) still shows its words, centred, without the spotlight.
- **Draft** listings and plans are visible only to the account that owns them.
- **Ownership is checked on every write** — editing someone else's parcel or
  posting to someone else's season log is a 403.
- Passwords are scrypt hashes (stdlib, nothing to compile). Sessions are signed
  cookies, `SameSite=Lax`, 30 days; set `BHOOMI_COOKIE_SECURE=1` behind HTTPS.

## Data — where it lives and how to take a copy

**Two backends, one set of queries.** With no configuration the app uses **SQLite**,
one file: `backend/bhoomi.sqlite3` (no server, no container, no credentials) and
photographs are files under `backend/uploads/`. Set **`DATABASE_URL`** to a
Postgres connection string and it switches to **Postgres** instead; a small
adapter in `db.py` handles the dialect differences, so the query code is written
once. On Postgres, photographs are also stored in the database
(`BHOOMI_PHOTOS_IN_DB`, on by default there) because free hosts wipe the disk on
every deploy. The SQLite backup script below applies to the SQLite file only; for
Postgres use your provider's backups or `pg_dump`.

Columns added after the first release are applied in place by `db.migrate()` on
startup — **this database holds real accounts and is never rebuilt from
scratch**.

### Taking a copy

```bash
cd backend
.venv/bin/python scripts/backup.py                 # timestamped .sqlite3 snapshot
.venv/bin/python scripts/backup.py --with-photos   # one .zip: database + uploads/
.venv/bin/python scripts/backup.py --csv           # one .csv per table, for a spreadsheet
.venv/bin/python scripts/backup.py --to ~/Desktop  # write it somewhere else
```

Copies land in `backend/backups/` (gitignored).

**Do not just `cp bhoomi.sqlite3`.** The database runs in WAL mode, so recent
writes may still be sitting in `bhoomi.sqlite3-wal` when you copy; a plain copy
taken while the server is running can be missing the newest rows. The script
uses SQLite's own backup API, which is consistent either way.

### Opening it

- **DB Browser for SQLite** — free, macOS, click through tables and edit rows
- **TablePlus** / **DBeaver** — if you already use one
- `sqlite3 backend/bhoomi.sqlite3` on the command line: `.tables`, then plain SQL
- The CSVs from `--csv` open straight in Excel or Google Sheets

Anything you change in a copy stays in the copy. To change the live data, edit
`backend/bhoomi.sqlite3` itself with the server stopped.

SQLite at `BHOOMI_DB` (default `backend/bhoomi.sqlite3`): `user`, `listing`,
`inquiry`, `project`, `pledge`, `project_update`, `photo`, `waitlist`,
`submission`. One `project` table holds all four funded kinds, separated by
`project.kind`. Back it up by copying the file — and the `uploads/` directory
with it, since the photographs live there rather than in the database.

It holds people's phone numbers. Keep it off git — `.gitignore` already does —
and off shared drives.

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q
```

Covers the waitlist API (phone normalisation, update-on-repeat, each validation
message, honeypot, rate limit, token auth) and the site: every public page,
signup and login rules, district normalisation including the two 2025 renames,
listing and plan lifecycles, search filters, draft privacy, inquiries, photo
upload with EXIF stripping and HEIC refusal, all three project kinds, share
arithmetic, the five-acre gate, the per-parcel people cap, small spaces
(square feet, the one-acre ceiling, editing, search by activity), in-place
schema migration, a from-scratch seed run, log permissions,
the language switch, the first-run tour (including that every step points at an
element the dashboard actually renders), and admin access.

## Not built, on purpose

- **No payments, escrow or wallet.** Interest is a record, not a transaction.
- **No KYC, no title verification.** Ask for the 7/12 or RTC and read it.
- **No notifications.** Nobody is emailed or messaged; you read the dashboard.
- **No licence generation.** The agreement is drafted and signed on paper.
- **Kannada covers the interface, not every paragraph.** Navigation, forms,
  filters, buttons and the key notices are translated; the long prose on *how it
  works* and *the fine print* is still English. Have a Kannada speaker read the
  fine print before it goes public — a clumsy translation of a legal argument is
  worse than none.
- **Taluk is free text.** Districts are a fixed list; taluks are not, yet.

The first two wait on counsel. Until then this is a pilot on fifteen acres with
a website attached.


## Tests

```bash
cd backend && .venv/bin/python -m pytest -q          # SQLite
BHOOMI_TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/dbname \
  .venv/bin/python -m pytest -q                      # the same suite on Postgres
```

CI (`.github/workflows/ci.yml`) runs both.

## Deploying

See **[DEPLOY.md](DEPLOY.md)** for the step-by-step guide, every environment variable
and a go-live checklist.

**Can it be hosted free on Streamlit?** Not directly. Streamlit Community Cloud only
runs Streamlit scripts (one Python file that uses the `streamlit` library); it cannot
run this FastAPI app or its database. The free route that does work:

1. **Database:** a free Postgres from **Neon** (set as `DATABASE_URL`).
2. **Web app:** a free **Render** (or Koyeb / Hugging Face Spaces) service built from the
   included `Dockerfile` (`render.yaml` does most of it).
3. **Optional Streamlit front door:** `streamlit/streamlit_app.py` is a small Streamlit
   page that introduces the site and links to it. Deploy it on Streamlit Community Cloud
   with the main file `streamlit/streamlit_app.py` and a secret `SITE_URL = "https://your-site"`.
   It can also show the site in an embedded frame, but sign-in does not work inside a
   frame (browsers block third-party cookies), and it needs
   `BHOOMI_FRAME_ANCESTORS=https://*.streamlit.app` on the real site. Link out rather than embed.

Free hosts wipe their disk on every deploy, which is why the app stores data (and
photographs) in Postgres when `DATABASE_URL` is set.
