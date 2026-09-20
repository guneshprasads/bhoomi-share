# Bhoomi Share

An agricultural site for **Karnataka**, built as one FastAPI app that serves
both the pages and the JSON behind them. Four ways to work land:

1. **Crop plan.** A farmer posts one crop on one named parcel for one season,
   costed, with photographs. People read the plan and register interest against
   it. When the harvest sells, proceeds split the way the agreement says.
2. **Livestock unit.** Sheep, goat, dairy or poultry, run by someone who keeps
   animals. The investor funds the animals, feed and shed; the cycle is months
   rather than one harvest.
3. **Land shares.** A parcel of five acres or more divided into equal shares of
   a fixed rupee value. Your slice of the return matches the slice of the cost
   you covered. **The number of people per parcel is capped** — that cap is what
   keeps it out of collective-investment territory until counsel says otherwise.
4. **Lease.** Owners who are not farming their land list it; farmers who want
   more land find it and write to the owner. The agreement is a fixed-term
   licence to cultivate, drafted for Karnataka.

Every page is available in **English or ಕನ್ನಡ**, and all 31 Karnataka districts
are a list you pick from rather than a box you type into.

Pre-launch. **No money moves through this site and no agreement is executed by
it.** Registering interest in a plan is a message to a grower, not a
subscription — see `/fine-print`, which explains the SEBI and tenancy-law
reasons the product is shaped this way.

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
| `/` | The landing page: the pitch, the split, the fine print, the waitlist form |
| `/invest` | All three funded kinds in one list, filterable by kind and district |
| `/seasons`, `/livestock`, `/shares` | One kind each, same filters |
| `/projects/{id}` | The plan, the photographs, the budget maths, the log |
| `/land`, `/land/{id}` | Parcels on offer, filterable by district, size and irrigation |
| `/lang/kn`, `/lang/en` | Switch language; remembered in a cookie for a year |
| `/how-it-works`, `/fine-print` | The two flows end to end; the law that shapes them |
| `/signup`, `/login` | Accounts. Roles: investor, grower, landowner, farmer |
| `/dashboard` | Your parcels, the farmers asking about them, your plans, what you back |
| `/dashboard?tour=1` | Replays the first-run guided tour on demand |
| `/dashboard/listings/new` | List a parcel, with `/edit`, `/delete` and photo removal under the same path |
| `/dashboard/projects/new?kind=crop\|livestock\|shares` | Post a plan; the form shows only the fields that kind needs |
| `/admin` | Waitlist, accounts, plans and listings. Admin accounts only |
| `/api/docs` | Generated API reference |

## API

| Method | Path | Who |
|---|---|---|
| `GET` | `/api/health` | public |
| `POST` | `/api/waitlist` | public — what the landing-page form posts |
| `GET` | `/api/listings`, `/api/projects`, `/api/districts` | public, read-only |
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
  scripts/backup.py  consistent database snapshots, zip, or CSV per table
    routers/         pages, auth, land, projects, dashboard, admin_pages, api
  templates/         Jinja pages; base.html holds the shell, _browse.html the
                     four listing pages
  static/            styles.css (the whole design system), app.js, tour.js, icon
  uploads/           photographs (gitignored)
  tests/             65 tests
```

Server-rendered HTML with POST-then-redirect, and about 120 lines of JavaScript
for the mobile menu and the waitlist form. No build step and no front-end
framework: the site works with JS off apart from the waitlist, which falls back
to an in-page thank-you.

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

**SQLite**, one file: `backend/bhoomi.sqlite3`. No server, no container, no
credentials. Photographs are **not** in it — they are files under
`backend/uploads/`, referenced by path.

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
`submission`. One `project` table holds all three funded kinds, separated by
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
arithmetic, the five-acre gate, the per-parcel people cap, log permissions,
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
