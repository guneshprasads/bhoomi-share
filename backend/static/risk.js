/* Money-at-risk: one plan simulated, its fixes compared, the whole holding ranked. */
(function () {
  'use strict';
  var L = window.BhoomiLedger, inr = L.inr, esc = L.esc;
  var $ = function (id) { return document.getElementById(id); };
  var S = { ledger: null, plan: null, assume: null, fixes: {}, catalog: {}, res: null };
  var timer = null, seq = 0;

  var ASSUME = [
    ['yield_cv', 'How much yield varies season to season', 0.05, 0.6, 0.01, 'pct'],
    ['price_vol', 'How much the sale price swings', 0, 0.5, 0.01, 'pct'],
    ['p_fail', 'Chance of a badly failed season', 0, 0.4, 0.01, 'pct'],
    ['fail_factor', 'Yield in a failed season, vs normal', 0.05, 0.7, 0.05, 'pct']
  ];
  // the one setting worth exposing for each fix: [key, label, min, max, step, format]
  var FIXSET = {
    drip: ['cost_per_unit', 'Drip irrigation: cost per acre', 0, 20000, 500, 'inr'],
    insurance: ['premium_rate', 'Insurance: premium, share of cover', 0.01, 0.12, 0.005, 'pct1'],
    contract: ['price_discount', 'Assured buyer: discount to expected price', 0, 0.2, 0.01, 'pct'],
    seed: ['yield_uplift', 'Better seed: yield gain', 0, 0.2, 0.01, 'pct'],
    vet: ['cost_per_unit', 'Vet plan: cost per head', 0, 1500, 50, 'inr'],
    climate: ['cost_per_unit', 'Climate control: cost per batch', 0, 6000, 250, 'inr']
  };

  function fmt(v, f) { return f === 'inr' ? inr(v) : (f === 'pct1' ? (v * 100).toFixed(1) + '%' : Math.round(v * 100) + '%'); }
  function sl(id, label, val, min, max, step, f) {
    return '<div class="f"><div class="f__top"><label for="' + id + '">' + label + '</label><output>' + fmt(val, f) + '</output></div>' +
      '<input type="range" id="' + id + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + val + '" style="--p:' + ((val - min) / (max - min) * 100) + '%"></div>';
  }

  /* ---- plan selector -------------------------------------------------------- */
  function renderSel() {
    $('planSel').innerHTML = S.ledger.plans.map(function (p) {
      return '<button class="chip' + (p.id === S.plan.id ? ' is-on' : '') + '" data-id="' + esc(p.id) + '">' + esc(p.name.split(' · ')[0]) + '</button>';
    }).join('');
  }
  $('planSel').addEventListener('click', function (e) {
    var b = e.target.closest('[data-id]'); if (!b) { return; }
    S.plan = S.ledger.plans.filter(function (p) { return p.id === b.getAttribute('data-id'); })[0];
    S.fixes = {}; renderSel(); run();
  });

  /* ---- assumptions ---------------------------------------------------------- */
  function renderAssume() {
    var h = '<h3>Change the assumptions <span class="muted" style="font-weight:400;font-size:.8rem">(all assumed: nothing here is measured)</span></h3>';
    ASSUME.forEach(function (a) { h += sl('as-' + a[0], a[1], S.assume[a[0]], a[2], a[3], a[4], 'pct'); });
    $('assume').innerHTML = h;
    ASSUME.forEach(function (a) {
      var el = $('as-' + a[0]);
      el.addEventListener('input', function () {
        S.assume[a[0]] = parseFloat(el.value);
        el.style.setProperty('--p', ((el.value - el.min) / (el.max - el.min) * 100) + '%');
        el.parentNode.querySelector('output').textContent = fmt(S.assume[a[0]], 'pct');
        schedule();
      });
    });
  }

  function schedule() { window.clearTimeout(timer); timer = window.setTimeout(run, 160); }

  /* ---- the run ------------------------------------------------------------------ */
  function run() {
    var my = ++seq;
    L.post('/api/risk', { plan: S.plan, assumptions: S.assume, fixes: S.fixes }).then(function (r) {
      if (my !== seq) { return; }
      S.res = r; renderRisk(r); renderFixes(r); renderTrust(r);
    }).catch(function (e) { $('kpis').innerHTML = '<p class="merr" style="grid-column:1/-1">' + esc(e.message) + '</p>'; });
    L.post('/api/holding', { plans: S.ledger.plans, assumptions: S.assume }).then(function (h) { if (my === seq) { renderHold(h); } });
  }

  function renderRisk(r) {
    $('h1title').textContent = r.plan.name.split(' · ')[0] + ': will the sale cover the costs?';
    $('h1sub').textContent = 'Budget ' + inr(r.cost) + ' · expected sale ' + inr(r.expected_revenue) + ' · ' + r.runs.toLocaleString('en-IN') + ' simulated seasons.';
    var b = r.base;
    $('kpis').innerHTML =
      '<div class="kpi"><b>' + L.short(r.expected_revenue) + '</b><span>expected sale</span><small>against a budget of ' + L.short(r.cost) + '</small></div>' +
      '<div class="kpi"><b class="' + (b.p_short > 0.2 ? 'hot' : '') + '">' + Math.round(b.p_short * 100) + '%</b><span>chance the sale falls short of the costs</span><small>if nothing changes</small></div>' +
      '<div class="kpi"><b>' + L.short(b.expected_shortfall) + '</b><span>expected shortfall per season</span><small>average over all ' + r.runs.toLocaleString('en-IN') + ' runs</small></div>' +
      '<div class="kpi"><b class="hot">' + L.short(b.bad_case) + '</b><span>bad case (1 season in 20)</span><small>95th percentile: the money-at-risk number</small></div>';
    hist(r);
  }

  function hist(r) {
    var bins = r.histogram, W = 900, H = 260, pl = 10, pr = 10, pt = 14, pb = 34;
    var lo = bins[0].from, hi = bins[bins.length - 1].to, max = Math.max.apply(null, bins.map(function (b) { return b.share; })) * 1.12;
    var x = L.scale(lo, hi, pl, W - pr), y = L.scale(0, max, H - pb, pt);
    var g = '';
    bins.forEach(function (b) {
      var x0 = x(b.from), w = Math.max(1, x(b.to) - x0 - 1.5), neg = (b.from + b.to) / 2 < 0;
      g += '<rect x="' + x0 + '" y="' + y(b.share) + '" width="' + w + '" height="' + (H - pb - y(b.share)) + '" rx="2.5" fill="' + (neg ? 'var(--rose)' : 'var(--burgundy)') + '" opacity="' + (neg ? 0.85 : 0.78) + '"><title>' + inr(b.from) + ' to ' + inr(b.to) + ': ' + (b.share * 100).toFixed(1) + '% of seasons</title></rect>';
    });
    if (lo < 0 && hi > 0) {
      g += '<line x1="' + x(0) + '" x2="' + x(0) + '" y1="' + pt + '" y2="' + (H - pb) + '" stroke="var(--text)" stroke-width="1.6" stroke-dasharray="5 4"/>' +
        '<text x="' + (x(0) + 6) + '" y="' + (pt + 10) + '" font-size="11" font-weight="700" fill="var(--text)">break-even</text>' +
        '<text x="' + (x(0) - 6) + '" y="' + (pt + 24) + '" text-anchor="end" font-size="10.5" fill="var(--rose)">sale falls short</text>' +
        '<text x="' + (x(0) + 6) + '" y="' + (pt + 24) + '" font-size="10.5" fill="var(--burgundy)">sale covers the costs</text>';
    }
    [['P10', r.base.p10_profit], ['median', r.base.p50_profit], ['P90', r.base.p90_profit]].forEach(function (m) {
      var px = x(Math.min(Math.max(m[1], lo), hi));
      g += '<line x1="' + px + '" x2="' + px + '" y1="' + (H - pb) + '" y2="' + (H - pb + 7) + '" stroke="var(--text-soft)"/><text x="' + px + '" y="' + (H - 8) + '" text-anchor="middle" font-size="10" fill="var(--text-soft)">' + m[0] + ' ' + L.short(m[1]) + '</text>';
    });
    g += '<line x1="' + pl + '" x2="' + (W - pr) + '" y1="' + (H - pb) + '" y2="' + (H - pb) + '" stroke="var(--line)"/>';
    $('hist').innerHTML = L.svg(W, H, g, 'hist');
  }

  /* ---- the fixes -------------------------------------------------------------------- */
  function renderFixes(r) {
    var maxNet = Math.max.apply(null, r.options.map(function (o) { return Math.abs(o.net_benefit); })) || 1;
    var h = '<table><thead><tr><th>Option</th><th>Chance short</th><th>Expected shortfall</th><th>Bad case</th><th>Cost</th><th>Net benefit / season</th></tr></thead><tbody>';
    r.options.forEach(function (o) {
      h += '<tr' + (o.key === r.best ? ' class="best"' : '') + '><td>' + esc(o.label) + (o.blurb ? '<small>' + esc(o.blurb) + '</small>' : '') + '</td>' +
        '<td>' + Math.round(o.p_short * 100) + '%</td><td>' + L.short(o.expected_shortfall) + '</td><td>' + L.short(o.bad_case) + '</td>' +
        '<td>' + (o.cost ? L.short(o.cost) : '–') + '</td>' +
        '<td class="' + (o.net_benefit > 0 ? 'pos' : (o.net_benefit < 0 ? 'neg' : '')) + '"><b>' + (o.key === 'none' ? '–' : (o.net_benefit > 0 ? '+' : '') + L.short(o.net_benefit)) + '</b>' +
        (o.key !== 'none' ? '<div style="height:5px;border-radius:9px;margin-top:5px;margin-left:auto;width:' + Math.max(4, Math.abs(o.net_benefit) / maxNet * 100) + '%;background:' + (o.net_benefit > 0 ? 'var(--leaf)' : 'var(--rose)') + '"></div>' : '') + '</td></tr>';
    });
    $('opts').innerHTML = h + '</tbody></table>';
    var v = $('verdict'); v.className = 'verdict' + (r.best ? '' : ' no');
    v.innerHTML = '<b>' + (r.best ? 'Pays back.' : 'No fix pays back here.') + '</b> ' + esc(r.verdict);
    $('h2title').textContent = r.plan.name.split(' · ')[0] + ': which fix pays back?';

    // fix settings
    var g = '';
    r.options.filter(function (o) { return o.key !== 'none'; }).forEach(function (o) {
      var set = FIXSET[o.key]; if (!set) { return; }
      var cat = S.catalog[o.key] || {}, cur = (S.fixes[o.key] || {})[set[0]];
      if (cur == null) { cur = cat[set[0]] != null ? cat[set[0]] : set[2]; }
      g += sl('fx-' + o.key, set[1], cur, set[2], set[3], set[4], set[5]);
    });
    $('fixgrid').innerHTML = g;
    r.options.filter(function (o) { return o.key !== 'none'; }).forEach(function (o) {
      var set = FIXSET[o.key], el = $('fx-' + o.key); if (!set || !el) { return; }
      el.addEventListener('input', function () {
        S.fixes[o.key] = S.fixes[o.key] || {}; S.fixes[o.key][set[0]] = parseFloat(el.value);
        el.style.setProperty('--p', ((el.value - el.min) / (el.max - el.min) * 100) + '%');
        el.parentNode.querySelector('output').textContent = fmt(parseFloat(el.value), set[5]);
        schedule();
      });
    });
  }

  /* ---- the holding ---------------------------------------------------------------------- */
  function renderHold(h) {
    var t = h.totals;
    var s = '<table><thead><tr><th>Plan</th><th>Budget</th><th>Trust</th><th>Chance short</th><th>Expected shortfall</th><th>Bad case</th><th class="l" style="text-align:left">Best fix</th><th>Net benefit</th></tr></thead><tbody>';
    h.rows.forEach(function (r) {
      if (r.skipped) { s += '<tr><td class="l">' + esc(r.name) + '</td><td colspan="7" style="text-align:left" class="muted">Not enough in the ledger to simulate.</td></tr>'; return; }
      s += '<tr class="' + (r.id === S.plan.id ? 'cur' : '') + '"><td class="l"><a data-id="' + esc(r.id) + '">' + esc(r.name.split(' · ')[0]) + '</a></td><td>' + L.short(r.cost) + '</td><td>' + r.trust + '</td>' +
        '<td>' + Math.round(r.p_short * 100) + '%</td><td>' + L.short(r.expected_shortfall) + '</td><td>' + L.short(r.bad_case) + '</td>' +
        '<td class="l">' + (r.best_fix ? esc(r.best_fix) : '<span class="muted">none pays back</span>') + '</td><td class="' + (r.net_benefit > 0 ? 'pos' : '') + '">' + (r.net_benefit > 0 ? '+' + L.short(r.net_benefit) : '–') + '</td></tr>';
    });
    s += '<tr class="tot"><td class="l">Holding</td><td>' + L.short(t.cost) + '</td><td></td><td></td><td>' + L.short(t.expected_shortfall) + '</td><td>' + L.short(t.bad_case_sum) + '</td><td class="l">' + L.short(t.after_fixes) + ' expected after best fixes</td><td class="pos">+' + L.short(t.net_benefit) + '</td></tr></tbody></table>';
    $('hold').innerHTML = s;
  }
  $('hold').addEventListener('click', function (e) {
    var a = e.target.closest('a[data-id]'); if (!a) { return; }
    S.plan = S.ledger.plans.filter(function (p) { return p.id === a.getAttribute('data-id'); })[0]; S.fixes = {};
    renderSel(); run(); window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  /* ---- trust ---------------------------------------------------------------------------- */
  function renderTrust(r) {
    var rec = r.reconciliation, W = 640, H = 70 + 46 * rec.sources.length;
    if (!rec.sources.length) { $('srcplot').innerHTML = '<p class="muted">No yield figures to reconcile.</p>'; return; }
    var all = rec.sources.map(function (s) { return [s.mean - 2 * s.sd, s.mean + 2 * s.sd]; }).concat([[rec.mean - 2 * rec.sd, rec.mean + 2 * rec.sd]]);
    var lo = Math.max(0, Math.min.apply(null, all.map(function (a) { return a[0]; })) * 0.95), hi = Math.max.apply(null, all.map(function (a) { return a[1]; })) * 1.05;
    var x = L.scale(lo, hi, 190, W - 20), g = '', colours = { claim: 'var(--gold)', history: 'var(--burgundy)', benchmark: 'var(--text-faint)' };
    rec.sources.forEach(function (s, i) {
      var y = 26 + i * 46;
      g += '<text x="0" y="' + (y + 4) + '" font-size="12" fill="var(--text-soft)">' + esc(s.name) + '</text>' +
        '<line x1="' + x(s.mean - 1.96 * s.sd) + '" x2="' + x(s.mean + 1.96 * s.sd) + '" y1="' + y + '" y2="' + y + '" stroke="' + colours[s.kind] + '" stroke-width="3" stroke-linecap="round" opacity=".55"/>' +
        '<circle cx="' + x(s.mean) + '" cy="' + y + '" r="6.5" fill="' + colours[s.kind] + '"/>' +
        '<text x="' + x(s.mean) + '" y="' + (y - 11) + '" text-anchor="middle" font-size="10.5" fill="var(--text)">' + s.mean + '</text>';
    });
    var yr = 26 + rec.sources.length * 46;
    g += '<line x1="190" x2="' + (W - 20) + '" y1="' + (yr - 24) + '" y2="' + (yr - 24) + '" stroke="var(--line)"/>' +
      '<text x="0" y="' + (yr + 4) + '" font-size="12.5" font-weight="700" fill="var(--text)">Reconciled</text>' +
      '<line x1="' + x(rec.mean - 1.96 * rec.sd) + '" x2="' + x(rec.mean + 1.96 * rec.sd) + '" y1="' + yr + '" y2="' + yr + '" stroke="var(--leaf)" stroke-width="5" stroke-linecap="round"/>' +
      '<path d="M' + x(rec.mean) + ',' + (yr - 9) + ' l9,9 l-9,9 l-9,-9 z" fill="var(--leaf)"/>' +
      '<text x="' + x(rec.mean) + '" y="' + (yr - 14) + '" text-anchor="middle" font-size="11" font-weight="700" fill="var(--leaf)">' + rec.mean + '</text>';
    $('srcplot').innerHTML = L.svg(W, H, g, 'srcplot');
    var word = rec.agreement <= 1 ? 'Sources agree' : (rec.agreement <= 2 ? 'Sources roughly agree' : 'Sources disagree');
    $('trustside').innerHTML = L.ring(rec.trust, 92) + '<b style="font-size:1.05rem;color:var(--text)">' + rec.trust + '/100 trust</b>' +
      '<p style="font-size:.85rem;margin:.4rem 0 0">' + word + '.<br>Largest gap: ' + rec.agreement + '× the two sources’ combined error.<br>Reconciled yield ' + rec.mean + ' ±' + rec.rel_error_95 + '% (95%).</p>';
    $('h4title').textContent = r.plan.name.split(' · ')[0] + ': one best estimate from ' + rec.sources.length + ' source' + (rec.sources.length === 1 ? '' : 's');
    var pv = r.provenance;
    $('prov').innerHTML = [['Data', pv.data], ['Model', pv.model], ['Assumed', pv.assumed]].map(function (b) {
      return '<div class="card"><h3>' + b[0] + '</h3><ul>' + b[1].map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div>';
    }).join('');
  }

  /* ---- go ----------------------------------------------------------------------------------- */
  Promise.all([L.current(), L.example()]).then(function (a) {
    S.ledger = a[0]; S.catalog = a[1].fixes; S.assume = Object.assign({}, a[1].assumptions);
    $('srcLabel').textContent = S.ledger.source === 'import' ? 'your file' : 'example holding';
    S.plan = S.ledger.plans[0]; renderSel(); renderAssume(); run();
  });
})();
