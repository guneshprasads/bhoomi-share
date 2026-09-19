# Bhoomi Share

A two-sided agricultural site, built as one FastAPI app that serves both the
pages and the JSON behind them.

1. **Season plans.** A grower posts one crop on one named parcel for one season,
   costed. People read the plan and register interest against it. When the
   harvest sells, proceeds split the way the agreement says.
2. **Land on offer.** Owners who are not farming their land list it; farmers who
   want more land find it and write to the owner. The agreement is a fixed-term
   licence to cultivate, drafted for the state the land sits in.

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
| `/seasons`, `/seasons/{id}` | Season plans, filterable; the plan, the budget maths, the season log |
| `/land`, `/land/{id}` | Parcels on offer, filterable by district, size and irrigation |
| `/how-it-works`, `/fine-print` | The two flows end to end; the law that shapes them |
| `/signup`, `/login` | Accounts. Roles: investor, grower, landowner, farmer |
| `/dashboard` | Your parcels, the farmers asking about them, your plans, what you back |
| `/dashboard/listings/new`, `/dashboard/seasons/new` | Create and edit, with `/edit` and `/delete` under the same paths |
| `/admin` | Waitlist, accounts, plans and listings. Admin accounts only |
| `/api/docs` | Generated API reference |

## API

| Method | Path | Who |
|---|---|---|
| `GET` | `/api/health` | public |
| `POST` | `/api/waitlist` | public — what the landing-page form posts |
| `GET` | `/api/listings`, `/api/seasons` | public, read-only |
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
    security.py      scrypt password hashing, session helpers, roles
    schemas.py       pydantic models for the JSON API
    templating.py    Jinja setup, ₹ formatting, flash messages
    deps.py          login/admin dependencies, typed 403 and 404
    seed.py          demo content for an empty database
    routers/         pages, auth, land, seasons, dashboard, admin_pages, api
  templates/         Jinja pages; base.html holds the shell
  static/            styles.css (the whole design system), app.js, icon
  tests/             38 tests
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
- **Draft** listings and plans are visible only to the account that owns them.
- **Ownership is checked on every write** — editing someone else's parcel or
  posting to someone else's season log is a 403.
- Passwords are scrypt hashes (stdlib, nothing to compile). Sessions are signed
  cookies, `SameSite=Lax`, 30 days; set `BHOOMI_COOKIE_SECURE=1` behind HTTPS.

## Data

SQLite at `BHOOMI_DB` (default `backend/bhoomi.sqlite3`): `user`, `listing`,
`inquiry`, `season`, `pledge`, `season_update`, `waitlist`, `submission`. Back it
up by copying the file.

It holds people's phone numbers. Keep it off git — `.gitignore` already does —
and off shared drives.

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q
```

Covers the waitlist API (phone normalisation, update-on-repeat, each validation
message, honeypot, rate limit, token auth) and the site (every public page,
signup and login rules, listing and plan lifecycles, search filters, draft
privacy, inquiries, pledges including self-pledge and withdrawal, season-log
permissions, admin access).

## Not built, on purpose

- **No payments, escrow or wallet.** Interest is a record, not a transaction.
- **No KYC, no title verification.** Ask for the 7/12 or RTC and read it.
- **No notifications.** Nobody is emailed or messaged; you read the dashboard.
- **No licence generation.** The agreement is drafted and signed on paper.

The first two wait on counsel. Until then this is a pilot on fifteen acres with
a website attached.
