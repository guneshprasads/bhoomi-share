# Bhoomi Share

An agriculture site for **Karnataka** that connects people who have **land or space**, people who have **money**, and people who can **farm**, in five clear ways, all on paper, in **English and &#3221;&#3240;&#3277;&#3240;&#3233;**. It is **pre-launch**: no money moves through the site, and nothing on it is an offer to invest.

<a href="docs/screenshots/01-home.jpg"><img src="docs/screenshots/01-home.jpg" width="640" alt="Bhoomi Share home page"></a>

| If you are... | you can... |
|---|---|
| an **investor** | fund one crop, herd, batch cycle or share of a parcel, and see its bad case first |
| a **grower / keeper** | get a season funded and keep an agreed share |
| a **landowner** | licence idle land on a fixed-term agreement and earn rent |
| a **farmer** | find land by district, size and irrigation, and know your break-even before you sign |

The five models are **crop plans**, **livestock units**, **small spaces** (mushrooms, vermicompost, microgreens), **land shares** and **leases**. Every funded plan follows **one rule**: what the crop or animals sell for first repays the listed costs to whoever paid them; what is left is split by the agreed percentages; a failed season can return nothing. **No return is guaranteed.**

## How to read this README

1. **[Run it](#run-it-in-two-minutes)**: two commands and the site is on your screen.
2. **[A tour of every screen](#a-tour-of-every-screen)**: 41 screenshots, each explained: what you see, what to do, where it leads.
3. **[The flow for a new user](#the-flow-for-a-new-user)**: the journey from arriving to acting.
4. **[How it works underneath](#how-it-works)**, **[authentication](#authentication-and-authorization)**, the **[tutorial](#the-first-run-tutorial)** and **[deploying](#deploying)**.

## Run it in two minutes

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000        # then open http://127.0.0.1:8000
```

An empty database seeds itself with **demo accounts** (local use only; turn off with `BHOOMI_SEED_DEMO=0`). The password for every one is `bhoomi-pilot`:

| Email | Who they are |
|---|---|
| `ravi@example.com` | investor backing four plans (the dashboard in screens 32&ndash;33) |
| `shalini@example.com` | landowner with two parcels |
| `asha@example.com` | farmer looking for land |
| `gunesh@example.com` | grower and landowner, **admin** (screen 41) |

The Postgres option, every environment variable and hosting are covered in **[DEPLOY.md](DEPLOY.md)**.

## A tour of every screen

Every picture below is a real screenshot of the running site (click one to enlarge). They are taken from the **demo data** that a fresh local install seeds, so names and numbers are examples. Follow them in order: public pages first (no account needed), then what happens once you sign up.

### Part A: Public pages (no account needed)

These are open to anyone. Screens 1&ndash;4 are the front door; 5&ndash;9 explain the models and the money rule; 10&ndash;11 are the map; 12&ndash;22 are the example farm; 23&ndash;27 are the story pages.

<table>
<tr><td width="420" valign="top"><a href="docs/screenshots/01-home.jpg"><img src="docs/screenshots/01-home.jpg" width="400" alt="01-home"></a><br><br></td><td valign="top"><h4>1. Home page</h4><b>What you see</b><ul><li>The promise in one line: <i>Land, money and hands &mdash; finally in one place.</i> A pill says the site is <b>pre-launch</b>, piloted on the family's own 15 acres.</li><li>Two buttons: <b>Try the example farm</b> and <b>Try the earnings simulator</b>. Three reassurances under them: no money moves through the site, every plan shows its costs and split, English and &#3221;&#3240;&#3277;&#3240;&#3233;.</li><li>On the right, an <b>example plan card</b> (Chana, Rabi 2026, 3.2 acres in Belagavi): budget &#8377;1,00,000, expected sale &#8377;1,60,000, a 70/30 split bar, and the notes <i>costs repaid first</i> and <i>signed on paper</i>. It says it is illustrative.</li><li>The top bar holds the logo, quick links (Ways to earn, Invest, Land on offer, Farm ledger), the language switch, <b>Log in</b>, <b>Create an account</b> and <b>Menu</b>.</li></ul><b>What to do</b><ul><li>Click <b>Try the example farm</b> to see the whole product working on invented data (screens 12&ndash;22).</li><li>Switch to &#3221;&#3240;&#3277;&#3240;&#3233; at any time; every page follows and your choice is remembered.</li></ul><b>Where it leads</b><ul><li>Everything below on this page is explained in screens 2 and 3.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/02-home-check-predict-decide.jpg"><img src="docs/screenshots/02-home-check-predict-decide.jpg" width="400" alt="02-home-check-predict-decide"></a><br><br></td><td valign="top"><h4>2. Check. Predict. Decide.</h4><b>What you see</b><ul><li>Three numbered cards, each with a live figure computed by the real engine: <b>12 gaps flagged in 6 example plans</b>; <b>riskiest: 22-acre block, 28%</b>; <b>expected shortfall cut by 11%</b>.</li><li>A burgundy band: <b>&#8377;1,74,131</b> expected shortfall per season across the example farm, with the four biggest plans as bars. It is labelled <i>Example farm &middot; invented data</i>.</li></ul><b>What to do</b><ul><li>Click a card to jump to its page, or the band's button to open the example farm.</li></ul><b>Where it leads</b><ul><li><b>Check</b> &rarr; Farm ledger (screens 12&ndash;18). <b>Predict</b> and <b>Decide</b> &rarr; Money-at-risk (screens 19&ndash;22).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/03-home-five-models.jpg"><img src="docs/screenshots/03-home-five-models.jpg" width="400" alt="03-home-five-models"></a><br><br></td><td valign="top"><h4>3. The five models</h4><b>What you see</b><ul><li>One card per way to work land and space: <b>Crop plan</b>, <b>Livestock unit</b>, <b>Small space</b>, <b>Land shares</b>, <b>Lease</b>. Each shows how many are open right now (from the database) and its cycle length.</li><li>A row of chips underneath: <i>Browse what is open</i>.</li></ul><b>What to do</b><ul><li>Click a card to read how that model works, or a chip to see the live plans.</li></ul><b>Where it leads</b><ul><li>Cards open the model pages (screens 8&ndash;9); chips open the listings (screens 34&ndash;37).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/04-sidebar-menu.jpg"><img src="docs/screenshots/04-sidebar-menu.jpg" width="400" alt="04-sidebar-menu"></a><br><br></td><td valign="top"><h4>4. The sidebar menu</h4><b>What you see</b><ul><li>Press <b>Menu</b> (top right, on every page) and a panel slides in with every page, grouped: <b>Explore</b> (Home, Ways to earn, Farm ledger, Money-at-risk, How it works, Foresight 2036, The story, Stories, Karnataka map), <b>Models</b>, <b>Browse</b> and <b>Trust</b> (FAQ, fine print, About).</li><li>Each entry has a one-line description. At the bottom: <b>Create an account</b> / <b>Log in</b> and the language switch. When you are signed in these become your dashboard and <b>Log out</b>.</li></ul><b>What to do</b><ul><li>Click any entry. Press <b>Esc</b>, click the dimmed page or the &times; to close it. Focus stays inside the panel while it is open, so it works with a keyboard.</li></ul><b>Where it leads</b><ul><li>Every page of the site is reachable from here.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/05-earn-investor.jpg"><img src="docs/screenshots/05-earn-investor.jpg" width="400" alt="05-earn-investor"></a><br><br></td><td valign="top"><h4>5. Ways to earn (investor)</h4><b>What you see</b><ul><li>Four tabs: <b>Investor</b>, <b>Grower / keeper</b>, <b>Landowner</b>, <b>Farmer</b>. On the left, how the money reaches that person, what they need, and <b>what can go wrong</b>.</li><li>On the right, a live <b>calculator</b>: sliders for the budget (&#8377;1,00,000), expected sale (&#8377;1,60,000) and the investor's share (70%). Below them, four seasons: <b>Strong +&#8377;70,000</b>, <b>As planned +&#8377;42,000</b>, <b>Weak &minus;&#8377;4,000</b>, <b>Failed &minus;&#8377;1,00,000 (&minus;100%)</b>.</li><li>A yellow notice at the top of the page says these are examples, not forecasts.</li></ul><b>What to do</b><ul><li>Drag a slider and watch all four seasons change. Use the <b>Model</b> dropdown to switch between crop plan, livestock unit, small space and land shares (each has its own inputs).</li></ul><b>Where it leads</b><ul><li>The rule is the same everywhere: the sale first repays the costs, then the rest is split. The numbers come from the server (<code>/api/simulate</code>), so they always match the tests.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/06-earn-landowner.jpg"><img src="docs/screenshots/06-earn-landowner.jpg" width="400" alt="06-earn-landowner"></a><br><br></td><td valign="top"><h4>6. Ways to earn (landowner)</h4><b>What you see</b><ul><li>The same page with the <b>Landowner</b> tab open: area (4 acres), rent per acre per season (&#8377;8,000), seasons per year and yearly upkeep.</li><li>Result: <b>&#8377;32,000 per season</b>, <b>&#8377;64,000 per year</b> and the year after upkeep, with a note that a licence has a fixed term.</li></ul><b>What to do</b><ul><li>Change the sliders to test a rent. Open the <b>Farmer</b> tab to see a tenant's break-even: the revenue per acre needed just to cover inputs and rent.</li></ul><b>Where it leads</b><ul><li>The buttons on the left lead to <i>List your land</i> (screen 40) or <i>Search parcels</i> (screen 37).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/07-models-index.jpg"><img src="docs/screenshots/07-models-index.jpg" width="400" alt="07-models-index"></a><br><br></td><td valign="top"><h4>7. The five models compared</h4><b>What you see</b><ul><li>Headline: <i>Five models, one rule.</i> One card per model with how many are open and a one-line cycle (<i>one season</i>, <i>months</i>, <i>weeks per batch</i>&hellip;). Further down, a side-by-side comparison table of who funds, who works, size and the main risk.</li></ul><b>What to do</b><ul><li>Click <b>Read the model</b> on a card.</li></ul><b>Where it leads</b><ul><li>Opens that model's page (screen 8).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/08-model-page.jpg"><img src="docs/screenshots/08-model-page.jpg" width="400" alt="08-model-page"></a><br><br></td><td valign="top"><h4>8. A model page (small space)</h4><b>What you see</b><ul><li>A title, a one-line promise and a short summary. A <b>glance box</b> on the right: <i>cycle, who funds, who works, size, split</i>.</li><li>Under it, <b>How it works in four steps</b> with numbered markers, written for that model.</li></ul><b>What to do</b><ul><li><b>Browse what is open</b> shows live plans of this kind; <b>Try the earnings simulator</b> opens the matching calculator.</li></ul><b>Where it leads</b><ul><li>Scroll on for the budget and worked example (screen 9), then who it fits, risks stated plainly and a short FAQ.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/09-model-budget.jpg"><img src="docs/screenshots/09-model-budget.jpg" width="400" alt="09-model-budget"></a><br><br></td><td valign="top"><h4>9. An example budget and worked example</h4><b>What you see</b><ul><li>A stacked bar and list showing where an example <b>&#8377;94,000</b> budget goes (racks, climate control, spawn, substrate, labour).</li><li>A <b>worked example</b> card showing what the funder gets back in four seasons, including the failed one (&minus;&#8377;94,000), labelled <i>not a forecast</i>.</li></ul><b>What to do</b><ul><li>Read the failed-season line first. Click <b>Change the numbers</b> to try your own.</li></ul><b>Where it leads</b><ul><li>Opens the calculator on the Ways to earn page (screen 5).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/10-map-farming.jpg"><img src="docs/screenshots/10-map-farming.jpg" width="400" alt="10-map-farming"></a><br><br></td><td valign="top"><h4>10. Karnataka map</h4><b>What you see</b><ul><li>A <b>real interactive map</b> (OpenStreetMap background) with all 31 districts. Four layer buttons above it: <b>Farming landscape</b>, <b>Best-fit model</b>, <b>Open right now</b>, <b>Division</b>.</li><li>Here Belagavi is selected (black outline, pulsing pin for our pilot). The panel shows its division and farming tier, <b>what is commonly grown</b>, <b>which models fit best</b> (Crop plans first choice) and <b>open plans and parcels</b> in that district.</li><li>Darker burgundy means a major cropland belt; lighter means mixed farming and plantations; palest means coast, forest or city. The legend and a note say these tiers are <b>indicative, not statistics</b>.</li></ul><b>What to do</b><ul><li>Click any district. Scroll the wheel after the first click to zoom. Switch layers with the buttons. Open <b>Prefer a simple grid?</b> under the map for a keyboard-friendly diagram.</li></ul><b>Where it leads</b><ul><li>The <i>open plans</i> and <i>parcels to lease</i> boxes link to those listings filtered to that district; <b>Join the waitlist</b> is in the panel.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/11-map-best-fit.jpg"><img src="docs/screenshots/11-map-best-fit.jpg" width="400" alt="11-map-best-fit"></a><br><br></td><td valign="top"><h4>11. Map: best-fit model layer</h4><b>What you see</b><ul><li>The same map coloured by each district's first-choice model: burgundy crop plans across the cropland belt, gold livestock (sheep and dairy country), green small spaces on the coast and near cities.</li></ul><b>What to do</b><ul><li>Click a district to see why that model was suggested.</li></ul><b>Where it leads</b><ul><li>A starting view for planning the pilot, not advice; every plan states its own crop and water.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/12-ledger-top.jpg"><img src="docs/screenshots/12-ledger-top.jpg" width="400" alt="12-ledger-top"></a><br><br></td><td valign="top"><h4>12. Farm ledger &mdash; the example farm</h4><b>What you see</b><ul><li>Headline: <i>Every plan gets an account that has to add up.</i> A summary card: <b>6 plans</b>, an average trust score ring (<b>74</b>), <b>&#8377;25.4L</b> budgeted, <b>1 of 6</b> accounts that add up, <b>12 gaps</b> to look at.</li><li>An <b>Example data</b> notice (it is invented and deliberately messy). Chips to filter by plan, <b>Download CSV</b>, <b>Print / PDF</b>, and four tabs: Overview, Balance check, Seasons &amp; yield, Input costs.</li></ul><b>What to do</b><ul><li>Click <b>Import a ledger</b> to load your own file (screen 17), or use the chips to look at one plan.</li></ul><b>Where it leads</b><ul><li><b>Not reported is never read as zero</b>: that is the principle of the whole page.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/13-ledger-flows.jpg"><img src="docs/screenshots/13-ledger-flows.jpg" width="400" alt="13-ledger-flows"></a><br><br></td><td valign="top"><h4>13. Ledger overview: money in, money out</h4><b>What you see</b><ul><li>One card per plan with a flow diagram: on the left what the season brought in, on the right where it went: <b>costs repaid</b>, <b>funder's share</b>, <b>grower's share</b>. Hatched red would be money the file cannot account for.</li><li>A badge (<i>adds up</i> or <i>needs a look</i>), the place and size, whether the season is <i>settled</i> or <i>expected, not yet sold</i>, and a <b>trust score out of 100</b>.</li></ul><b>What to do</b><ul><li>Compare the cards. Filter to one plan with the chips.</li></ul><b>Where it leads</b><ul><li>Why a plan <i>needs a look</i> is explained on the next tab (screen 14).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/14-ledger-balance.jpg"><img src="docs/screenshots/14-ledger-balance.jpg" width="400" alt="14-ledger-balance"></a><br><br></td><td valign="top"><h4>14. Balance check</h4><b>What you see</b><ul><li>A table: one row per plan, four rules as columns (<b>budget adds up</b>, <b>spend logged</b>, <b>money in = out</b>, <b>enough seasons</b>), each cell <i>adds up</i> (green), <i>off</i> (red) or <i>not reported</i> (grey), with a trust ring per plan.</li><li>Below it, a <b>Needs a human</b> list in plain words, e.g. <i>Tur: lines total &#8377;58,000 but the plan says &#8377;64,000: off by &minus;9.4%. Allowed: &plusmn;5%.</i></li></ul><b>What to do</b><ul><li>Hover a cell for the detail. Fix what the list names, then re-import.</li></ul><b>Where it leads</b><ul><li>Every rule allows &plusmn;5%, like a water balance. Gaps are listed, never guessed.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/15-ledger-seasons.jpg"><img src="docs/screenshots/15-ledger-seasons.jpg" width="400" alt="15-ledger-seasons"></a><br><br></td><td valign="top"><h4>15. Seasons &amp; yield</h4><b>What you see</b><ul><li>For each plan, a bar per past season and three lines: what the <b>plan says</b> (gold), a <b>district benchmark</b> (assumed, grey) and the <b>reconciled</b> estimate (green), which weights each source by how precise it is.</li><li>A footer: the reconciled yield with its error band and whether the sources agree.</li></ul><b>What to do</b><ul><li>Look for plans with few bars: a short history means a wide, honest forecast band.</li></ul><b>Where it leads</b><ul><li>The reconciled yield is what the risk simulation starts from (screen 22).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/16-ledger-costs.jpg"><img src="docs/screenshots/16-ledger-costs.jpg" width="400" alt="16-ledger-costs"></a><br><br></td><td valign="top"><h4>16. Input costs</h4><b>What you see</b><ul><li>Three <b>price sliders</b> (inputs, labour, water and power, &minus;30% to +60%), a stacked bar of each plan's budget by category, and a table of totals.</li><li>It is labelled as planning values: replace them with real quotes.</li></ul><b>What to do</b><ul><li>Move a slider and watch every plan's budget change. Use it to see which plans are most exposed to a price rise.</li></ul><b>Where it leads</b><ul><li>Budgets here are the same ones checked on screen 14.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/17-ledger-import.jpg"><img src="docs/screenshots/17-ledger-import.jpg" width="400" alt="17-ledger-import"></a><br><br></td><td valign="top"><h4>17. Import a ledger</h4><b>What you see</b><ul><li>A dialog with <b>Import a file</b> (drop a .csv or click to choose), a <b>Paste CSV</b> tab, <b>Use the example farm's file</b>, and <b>Download the example as a template</b>. It says your file is read on the page and checked by the server, and is not stored or shared.</li></ul><b>What to do</b><ul><li>Download the template, edit it, and drop it back in. The layout is one CSV: <code>plan, record, label, value, season</code>, where <code>record</code> (meta, cost, spent, history, sale) says where each number goes.</li></ul><b>Where it leads</b><ul><li>On success the ledger replaces the example and carries over to Money-at-risk.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/18-ledger-import-issues.jpg"><img src="docs/screenshots/18-ledger-import-issues.jpg" width="400" alt="18-ledger-import-issues"></a><br><br></td><td valign="top"><h4>18. Import &mdash; problems reported, not hidden</h4><b>What you see</b><ul><li>A deliberately broken pasted file: each step ticked off, then a <b>Needs a human</b> box: <i>area is 'three', which is not a number; kept as not reported</i>, <i>cost line 'Labour' has no usable amount, skipped</i>, <i>record type 'weird' is not one of&hellip;; skipped</i>.</li></ul><b>What to do</b><ul><li>Fix the rows it names and read again. Use <b>Back to the example</b> on the page to reset.</li></ul><b>Where it leads</b><ul><li>The same problems also appear on the Balance check tab.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/19-risk-simulation.jpg"><img src="docs/screenshots/19-risk-simulation.jpg" width="400" alt="19-risk-simulation"></a><br><br></td><td valign="top"><h4>19. Money-at-risk: the simulation</h4><b>What you see</b><ul><li>Plan chips at the top choose the plan. Four figures for it: <b>expected sale &#8377;1.4L</b>, <b>14%</b> chance the sale falls short of the costs, <b>&#8377;5k</b> expected shortfall per season, <b>&#8377;54k bad case (1 season in 20)</b>.</li><li>A histogram of 2,000 simulated seasons with a dashed <b>break-even</b> line: left of it the sale did not cover the costs; ticks mark P10, median and P90. Below are four <b>assumption sliders</b>: yield spread, price swing, chance of a failed season, yield in a failed season.</li></ul><b>What to do</b><ul><li>Drag the assumptions to stress the plan. Everything here is assumed and says so.</li></ul><b>Where it leads</b><ul><li>It is a <b>simulation, not a forecast</b>; the same inputs always give the same numbers (it is seeded).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/20-risk-fixes.jpg"><img src="docs/screenshots/20-risk-fixes.jpg" width="400" alt="20-risk-fixes"></a><br><br></td><td valign="top"><h4>20. Which fix pays back?</h4><b>What you see</b><ul><li>A table comparing <b>Do nothing</b>, <b>Drip irrigation</b>, <b>Crop insurance</b>, <b>Assured buyer</b> and <b>Better seed</b>: chance short, expected shortfall, bad case, cost and <b>net benefit per season</b> with a green or red bar. The best option is highlighted.</li><li>A plain-words verdict: <i>Pays back. Better seed or stock pays back: it adds &#8377;7,112 of expected value for &#8377;4,800, 1.5&times; its cost, a net gain of &#8377;2,312 a season.</i></li></ul><b>What to do</b><ul><li>Open <b>Change the fixes' costs and effects</b> and replace the assumed prices with real quotes to see if the answer changes.</li></ul><b>Where it leads</b><ul><li>Drip irrigation is red here on purpose: on 3.2 acres it costs more than it saves.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/21-risk-holding.jpg"><img src="docs/screenshots/21-risk-holding.jpg" width="400" alt="21-risk-holding"></a><br><br></td><td valign="top"><h4>21. The whole holding</h4><b>What you see</b><ul><li><b>Where to act first</b>: every plan on one table (budget, trust, chance short, expected shortfall, bad case, best fix, net benefit) with a totals row: <b>&#8377;1.74L</b> expected shortfall, <b>&#8377;1.55L</b> after the best fixes.</li></ul><b>What to do</b><ul><li>Click a plan's name to jump up and analyse it.</li></ul><b>Where it leads</b><ul><li>This is the view a funder or lender asks for.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/22-risk-trust.jpg"><img src="docs/screenshots/22-risk-trust.jpg" width="400" alt="22-risk-trust"></a><br><br></td><td valign="top"><h4>22. Can we trust the starting number?</h4><b>What you see</b><ul><li>A dot plot of three sources of expected yield (the plan's own figure, the land's own seasons, a district benchmark) with error bars, and one <b>reconciled</b> estimate; a trust ring (<b>85/100</b>) and whether the sources agree.</li><li>Three cards spell out <b>what is data</b>, <b>what is model</b> and <b>what is assumed</b>.</li></ul><b>What to do</b><ul><li>Compare plans: when sources disagree the trust score falls and the forecast band widens.</li></ul><b>Where it leads</b><ul><li>The honest answer to &ldquo;why should I believe these numbers?&rdquo;</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/23-story.jpg"><img src="docs/screenshots/23-story.jpg" width="400" alt="23-story"></a><br><br></td><td valign="top"><h4>23. The story</h4><b>What you see</b><ul><li><i>Farm money is mostly guesswork. We put a number on it.</i> Beside it a card with the example farm's expected shortfall (<b>&#8377;1,74,131</b>) and the top plans. Below: the problem, Check/Predict/Decide with live figures, <b>outcomes per side</b> (funder, grower, landowner, farmer), an honest <b>&ldquo;Free while we prove it&rdquo;</b> business-model block, and what is data, model and assumed.</li></ul><b>What to do</b><ul><li>Read it top to bottom; it is the pitch.</li></ul><b>Where it leads</b><ul><li>Links out to the example farm and the foresight page.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/24-foresight.jpg"><img src="docs/screenshots/24-foresight.jpg" width="400" alt="24-foresight"></a><br><br></td><td valign="top"><h4>24. Foresight 2036</h4><b>What you see</b><ul><li>A trend curve for 2026&ndash;2036 with a draggable year (here <b>2030</b>) and the milestone for that year: <i>Risk is shown before money is asked for</i>. Below the fold: six drivers, milestones, opportunities and risks, the future we want, steps to get there.</li></ul><b>What to do</b><ul><li>Drag the slider or click a dot on the curve.</li></ul><b>Where it leads</b><ul><li>Labelled a <b>foresight exercise, not a forecast</b>: the curve shows a direction, not measured data.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/25-stories.jpg"><img src="docs/screenshots/25-stories.jpg" width="400" alt="25-stories"></a><br><br></td><td valign="top"><h4>25. Stories</h4><b>What you see</b><ul><li>Six illustrative people, one per side. Each has the situation, what they did, what they learned and a numbers table (for Ravi, a crop funder: +&#8377;70,000 strong, +&#8377;42,000 as planned, &minus;&#8377;4,000 weak, &minus;&#8377;1,00,000 failed).</li></ul><b>What to do</b><ul><li>Find the person closest to you.</li></ul><b>Where it leads</b><ul><li>They are labelled <b>illustrative, not real customers</b>; the numbers come from the same engine as the calculators.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/26-how-it-works.jpg"><img src="docs/screenshots/26-how-it-works.jpg" width="400" alt="26-how-it-works"></a><br><br></td><td valign="top"><h4>26. How it works</h4><b>What you see</b><ul><li>One funded season as <b>six phases</b> (plan posted, interest registered, agreement signed, season runs, harvest sells, proceeds split). Each phase has three boxes: what the <b>investor or grower</b> does, what the <b>site</b> does, and what is <b>on paper</b>.</li></ul><b>What to do</b><ul><li>Read the green <i>On paper</i> boxes: they show that the site never holds money or signs anything.</li></ul><b>Where it leads</b><ul><li>Further down: the other four models, what the site does and does not do, what it costs (nothing in the pilot) and where it runs.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/27-faq.jpg"><img src="docs/screenshots/27-faq.jpg" width="400" alt="27-faq"></a><br><br></td><td valign="top"><h4>27. FAQ</h4><b>What you see</b><ul><li><i>Straight answers, including the awkward ones.</i> A search box, a category list on the left and expandable questions in five groups (basics, money and returns, law and safety, working with land and plans, accounts and data).</li></ul><b>What to do</b><ul><li>Type a word to filter; open any question.</li></ul><b>Where it leads</b><ul><li>The answers match the fine-print page: no guaranteed return; a share is a share of one cycle's work, never of the land.</li></ul></td></tr>
</table>

### Part B: Creating an account



<table>
<tr><td width="420" valign="top"><a href="docs/screenshots/28-signup.jpg"><img src="docs/screenshots/28-signup.jpg" width="400" alt="28-signup"></a><br><br></td><td valign="top"><h4>28. Create an account</h4><b>What you see</b><ul><li>A form: name, email, phone, <b>district</b> (a list of the 31 Karnataka districts, not free text), optional taluk, <b>which side you are on</b> (Investor, Grower, Landowner, Farmer &mdash; pick as many as apply) and a password.</li></ul><b>What to do</b><ul><li>Fill it in and submit. Passwords need 8+ characters and must match.</li></ul><b>Where it leads</b><ul><li>You are signed in straight away and taken to your dashboard, where the tutorial runs once (screens 30&ndash;31).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/29-login.jpg"><img src="docs/screenshots/29-login.jpg" width="400" alt="29-login"></a><br><br></td><td valign="top"><h4>29. Log in</h4><b>What you see</b><ul><li>Email and password. A link to <i>Make one</i> if you have no account.</li></ul><b>What to do</b><ul><li>Sign in. After 10 wrong attempts in an hour from one connection you are asked to wait.</li></ul><b>Where it leads</b><ul><li>Lands on your dashboard (or the page you were trying to reach).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/30-tour-welcome.jpg"><img src="docs/screenshots/30-tour-welcome.jpg" width="400" alt="30-tour-welcome"></a><br><br></td><td valign="top"><h4>30. The first-run tutorial</h4><b>What you see</b><ul><li>The page dims and a spotlight frames the top of your dashboard. A card says <b>1 of 6 &middot; Welcome</b> and, above all, that <i>no money moves through this site</i>.</li></ul><b>What to do</b><ul><li>Press <b>Next</b>, or <b>Skip the tour</b>.</li></ul><b>Where it leads</b><ul><li>It runs once per account; replay it from <i>Show me around again</i> on the dashboard.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/31-tour-invest.jpg"><img src="docs/screenshots/31-tour-invest.jpg" width="400" alt="31-tour-invest"></a><br><br></td><td valign="top"><h4>31. Tutorial step 2</h4><b>What you see</b><ul><li>The spotlight moves to the <b>Invest</b> link: <i>Five ways to take part&hellip;</i>. Six steps in all: Welcome, Invest, Land on offer, Your plans, What you back, Your profile.</li></ul><b>What to do</b><ul><li><b>Next</b> and <b>Back</b> move between steps.</li></ul><b>Where it leads</b><ul><li>Whether you have seen it is stored on your account, so it follows you to other devices.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/32-dashboard.jpg"><img src="docs/screenshots/32-dashboard.jpg" width="400" alt="32-dashboard"></a><br><br></td><td valign="top"><h4>32. Your dashboard</h4><b>What you see</b><ul><li>Your name, place, phone and roles, with <b>Edit profile</b> and <b>Show me around again</b>. Buttons <b>List your land</b> and <b>Post a plan</b>. Five counters: parcels you list, farmers asking, plans posted, plans you back, total interest registered.</li><li>Sections below: <b>Your land</b>, <b>Farmers asking about your land</b>, <b>Your plans</b>.</li></ul><b>What to do</b><ul><li>Start from the buttons, or use the <i>+ Crop plan / Livestock unit / Small space / Land shares</i> links to post a particular kind.</li></ul><b>Where it leads</b><ul><li>Everything you own or follow is here; drafts are visible only to you.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/33-dashboard-backing.jpg"><img src="docs/screenshots/33-dashboard-backing.jpg" width="400" alt="33-dashboard-backing"></a><br><br></td><td valign="top"><h4>33. Plans you are backing</h4><b>What you see</b><ul><li>A table of every plan you have registered interest in: the plan, where, <b>your interest</b> (e.g. &#8377;30,000, or 6 shares &#8377;1,50,000) and its stage. A note: <i>Registered interest, not payment.</i></li></ul><b>What to do</b><ul><li>Click a plan to reread it or change your interest.</li></ul><b>Where it leads</b><ul><li>Nothing is owed by you and nothing to you until there is a signed deed for that season.</li></ul></td></tr>
</table>

### Part C: Plans and land

What a signed-in person does: browse plans, register interest, ask about a parcel, post their own.

<table>
<tr><td width="420" valign="top"><a href="docs/screenshots/34-invest-list.jpg"><img src="docs/screenshots/34-invest-list.jpg" width="400" alt="34-invest-list"></a><br><br></td><td valign="top"><h4>34. Invest: browse plans</h4><b>What you see</b><ul><li>A notice that nothing here takes money. Filters: <b>district</b>, <b>kind</b>, <b>crop or animal</b>, <b>stage</b>. Cards for each open plan (kind, title, where and who, key figures, and a <b>progress meter</b> of how much is spoken for).</li></ul><b>What to do</b><ul><li>Filter, then open a card.</li></ul><b>Where it leads</b><ul><li>Opens the plan (screen 35).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/35-project-detail.jpg"><img src="docs/screenshots/35-project-detail.jpg" width="400" alt="35-project-detail"></a><br><br></td><td valign="top"><h4>35. A plan</h4><b>What you see</b><ul><li>The facts (area, what it is used for, the space, water and power, plan length, budget, <b>split of proceeds</b>) and a box on the right: <b>&#8377;30,000 of &#8377;1,80,000 spoken for</b>, a progress bar and the <b>Register interest</b> form.</li></ul><b>What to do</b><ul><li>Enter an amount and an optional note, then <b>Register interest</b> (here shown as <i>Update my interest</i> with <i>Withdraw it</i>).</li></ul><b>Where it leads</b><ul><li>Interest is a message to the grower, not a payment; no pool opens until counsel has signed off the structure.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/36-project-interest.jpg"><img src="docs/screenshots/36-project-interest.jpg" width="400" alt="36-project-interest"></a><br><br></td><td valign="top"><h4>36. A plan: if it goes to plan</h4><b>What you see</b><ul><li><b>If it goes to plan</b>: expected revenue &#8377;3,60,000, less the budget, left to split, and each side's share. A reminder that these are the grower's estimates, not a forecast, and that a bad cycle splits the same way. Then <b>In their words</b>: the grower's own explanation.</li></ul><b>What to do</b><ul><li>Read the grower's words and check the budget line by line before registering interest.</li></ul><b>Where it leads</b><ul><li>The season log (updates on spend and progress) follows further down.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/37-land-list.jpg"><img src="docs/screenshots/37-land-list.jpg" width="400" alt="37-land-list"></a><br><br></td><td valign="top"><h4>37. Land on offer</h4><b>What you see</b><ul><li>Parcels whose owners are not farming them this year, all offered on a fixed-term licence. Filters: district, smallest and largest acres, <b>irrigated only</b>. Cards show acres, water, term, rent and what can be grown.</li></ul><b>What to do</b><ul><li>Filter, then <b>See the parcel</b>. Owners use <b>List your land</b>.</li></ul><b>Where it leads</b><ul><li>Opens the parcel (screen 38).</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/38-listing-detail.jpg"><img src="docs/screenshots/38-listing-detail.jpg" width="400" alt="38-listing-detail"></a><br><br></td><td valign="top"><h4>38. A parcel</h4><b>What you see</b><ul><li>Size, water, soil, road access, last crop, what can be grown, term, rent and terms, plus <b>From the owner</b> in their own words. On the right a box: <b>Ask about this parcel</b>.</li></ul><b>What to do</b><ul><li>Write what you would grow, what you can irrigate and when you want to start, then <b>Send to the owner</b>.</li></ul><b>Where it leads</b><ul><li>The owner sees your name, district and phone number. Nothing is agreed or signed through the site.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/39-post-plan.jpg"><img src="docs/screenshots/39-post-plan.jpg" width="400" alt="39-post-plan"></a><br><br></td><td valign="top"><h4>39. Post a plan</h4><b>What you see</b><ul><li>Choose the kind (crop plan, livestock unit, small space, land shares); the form then shows only the fields that kind needs. First block: name it, parcel, survey number, district, taluk, size. Further down: budget, expected sale, the split, photographs and your own words.</li></ul><b>What to do</b><ul><li>Fill in numbers you would defend to someone who has farmed: <i>a plan nobody believes is worse than no plan</i>.</li></ul><b>Where it leads</b><ul><li>Saved as a draft you can edit; publish when ready. A plan's kind cannot change after posting.</li></ul></td></tr>
<tr><td width="420" valign="top"><a href="docs/screenshots/40-list-land.jpg"><img src="docs/screenshots/40-list-land.jpg" width="400" alt="40-list-land"></a><br><br></td><td valign="top"><h4>40. List your land</h4><b>What you see</b><ul><li>The parcel form: description, size, survey number, district, taluk, then <b>what a farmer needs to know</b> (water, hours available, soil, road access, last crop, what can be grown), term, rent or crop share and photographs.</li></ul><b>What to do</b><ul><li>Fill in water and soil properly and add a couple of photographs: farmers decide on those first.</li></ul><b>Where it leads</b><ul><li>Photographs are re-encoded on upload, which strips the GPS location your phone writes into them.</li></ul></td></tr>
</table>

### Part D: Admin



<table>
<tr><td width="420" valign="top"><a href="docs/screenshots/41-admin.jpg"><img src="docs/screenshots/41-admin.jpg" width="400" alt="41-admin"></a><br><br></td><td valign="top"><h4>41. Admin</h4><b>What you see</b><ul><li>Admin accounts only. Six counters (accounts, parcels listed, plans posted, interests registered, messages sent, on the waitlist), the <b>waitlist</b> with a <b>Waitlist CSV</b> export, and a table of <b>accounts</b> with their sides and districts. A warning that these are people's phone numbers.</li></ul><b>What to do</b><ul><li>Review sign-ups and listings; export the waitlist.</li></ul><b>Where it leads</b><ul><li>Create the first admin with <code>python scripts/make_admin.py you@example.com</code> after signing up.</li></ul></td></tr>
</table>

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

## Run it: details

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
| `/why` | **Why it matters**: investor-facing page with two real-data charts (India food price inflation, FAO; agriculture's share of jobs vs output, World Bank), the gap, who might pay (hypotheses, none tested), milestones, risks and sources |
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
cd backend && .venv/bin/python -m pytest -q          # SQLite, 174 tests
BHOOMI_TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/dbname \
  .venv/bin/python -m pytest -q                      # the same suite on Postgres
```

CI (`.github/workflows/ci.yml`) runs both. They cover the waitlist API (phone normalisation, update-on-repeat, each validation
message, honeypot, rate limit, token auth) and the site: every public page,
signup and login rules, district normalisation including the two 2025 renames,
listing and plan lifecycles, search filters, draft privacy, inquiries, photo
upload with EXIF stripping and HEIC refusal, all three project kinds, share
arithmetic, the five-acre gate, the per-parcel people cap, small spaces
(square feet, the one-acre ceiling, editing, search by activity), in-place
schema migration, a from-scratch seed run, log permissions,
the language switch, the first-run tour (including that every step points at an
element the dashboard actually renders), and admin access.

Also covered: the earnings simulator, the ledger importer and balance rules, the risk simulation (determinism, fixes, reconciliation), the security headers and CSP nonces, login throttling and cross-site POST refusal, the sitemap, and photographs surviving a wiped disk.

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
