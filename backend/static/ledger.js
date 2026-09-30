/* Farm ledger page. The ledger lives in this browser (sessionStorage) so an
   imported file carries over to the Money-at-risk page; the server checks it. */
(function () {
  'use strict';
  var L = window.BhoomiLedger, inr = L.inr, esc = L.esc;
  var $ = function (id) { return document.getElementById(id); };
  var state = null, filter = 'all', tab = 'overview';
  var adj = { Inputs: 0, Labour: 0, 'Water and power': 0 };     // what-if cost changes, in percent

  var STATUS_ICON = { ok: '✓', off: '≠', missing: '–' };
  var STATUS_TEXT = { ok: 'adds up', off: 'off', missing: 'not reported' };

  function plans() { return filter === 'all' ? state.plans : state.plans.filter(function (p) { return p.id === filter; }); }
  function checkOf(id) { return state.checks.filter(function (c) { return c.id === id; })[0]; }
  function shortName(p) { return p.name.split(' · ')[0]; }

  /* ---- header summary ------------------------------------------------------ */
  function renderSummary() {
    var ps = state.plans, n = ps.length;
    var adds = state.checks.filter(function (c) { return c.badge === 'adds up'; }).length;
    var avg = Math.round(state.checks.reduce(function (s, c) { return s + c.trust; }, 0) / (n || 1));
    var budget = ps.reduce(function (s, p) { return s + L.costTotal(p); }, 0);
    var gaps = state.checks.reduce(function (s, c) { return s + c.flags.length; }, 0);
    $('summary').innerHTML =
      '<div class="lsum__top"><div><div class="lsum__n">' + n + '</div><div class="lsum__l">plans in this ledger</div></div>' + L.ring(avg, 76) + '</div>' +
      '<div class="lsum__row"><span>Budgeted in total</span><b>' + L.short(budget) + '</b></div>' +
      '<div class="lsum__row"><span>Accounts that add up</span><b>' + adds + ' of ' + n + '</b></div>' +
      '<div class="lsum__row"><span>Gaps to look at</span><b class="' + (gaps ? 'neg' : 'pos') + '">' + gaps + '</b></div>' +
      '<p class="lsum__note">Average trust score, out of 100.</p>';
    $('srcLabel').textContent = state.source === 'import' ? 'your file' : 'example holding';
    $('exNote').hidden = state.source === 'import';
    $('btnReset').hidden = state.source !== 'import';
  }

  function renderFilter() {
    var h = '<button class="chip' + (filter === 'all' ? ' is-on' : '') + '" data-f="all">All plans</button>';
    state.plans.forEach(function (p) { h += '<button class="chip' + (filter === p.id ? ' is-on' : '') + '" data-f="' + esc(p.id) + '">' + esc(shortName(p)) + '</button>'; });
    $('filter').innerHTML = h;
  }

  /* ---- overview: money flow (a two-column Sankey) --------------------------- */
  function flowFor(p) {
    var settled = state.settled && state.settled[p.id];
    if (settled) {
      var out = settled.repaid_to_funder + settled.funder_share + settled.grower_share;
      return { kind: 'settled', season: settled.season, receipts: settled.receipts,
               parts: [['Costs repaid', settled.repaid_to_funder, 'repaid'], ['Funder’s share', settled.funder_share, 'funder'], ['Grower’s share', settled.grower_share, 'grower']],
               unaccounted: Math.max(0, settled.receipts - out) };
    }
    var cost = L.costTotal(p), rev = (p.expected_yield || 0) * (p.area || 0) * (p.expected_price || 0);
    if (!rev) { return null; }
    var repaid = Math.min(rev, cost), surplus = Math.max(rev - cost, 0), ip = (p.investor_pct || 70) / 100;
    return { kind: 'expected', receipts: rev,
             parts: [['Costs repaid', repaid, 'repaid'], ['Funder’s share', surplus * ip, 'funder'], ['Grower’s share', surplus * (1 - ip), 'grower']], unaccounted: 0 };
  }

  function sankey(f) {
    var W = 360, H = 150, top = 12, bar = 12, gap = 6, avail = H - top - 12;
    var total = f.receipts, parts = f.parts.slice();
    if (f.unaccounted > 0) { parts.push(['Unaccounted', f.unaccounted, 'un']); }
    var scale = (avail - gap * (parts.length - 1)) / total;
    var leftH = total * scale;
    var lx = 70, rx = W - 100, y = top, ly = top + (avail - leftH) / 2, acc = 0, h = '';
    var col = { repaid: 'var(--burgundy-deep)', funder: 'var(--burgundy-hi)', grower: 'var(--gold-soft)', un: 'url(#hatch)' };
    parts.forEach(function (pt) {
      var ph = Math.max(pt[1] * scale, 1.5);
      var y0 = ly + acc * scale, y1 = y0 + pt[1] * scale, ty = y, by = y + ph;
      var cx = (lx + bar + rx) / 2;
      h += '<path d="M' + (lx + bar) + ',' + y0 + ' C' + cx + ',' + y0 + ' ' + cx + ',' + ty + ' ' + rx + ',' + ty + ' L' + rx + ',' + by + ' C' + cx + ',' + by + ' ' + cx + ',' + y1 + ' ' + (lx + bar) + ',' + y1 + ' Z" fill="' + col[pt[2]] + '" opacity="' + (pt[2] === 'un' ? 1 : 0.32) + '"' + (pt[2] === 'un' ? ' stroke="var(--rose)" stroke-width="1"' : '') + '/>';
      h += '<rect x="' + rx + '" y="' + ty + '" width="' + bar + '" height="' + ph + '" fill="' + (pt[2] === 'un' ? 'var(--rose)' : col[pt[2]]) + '" rx="2"/>';
      h += '<text x="' + (rx + bar + 6) + '" y="' + (ty + ph / 2 + 3) + '" font-size="9.5" fill="var(--text-soft)">' + esc(pt[0]) + '</text>';
      h += '<text x="' + (rx + bar + 6) + '" y="' + (ty + ph / 2 + 14) + '" font-size="9" fill="var(--text-faint)">' + L.short(pt[1]) + '</text>';
      y += ph + gap; acc += pt[1];
    });
    h = '<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="#fff"/><line x1="0" y1="0" x2="0" y2="5" stroke="var(--rose)" stroke-width="2"/></pattern></defs>' +
      '<rect x="' + lx + '" y="' + ly + '" width="' + bar + '" height="' + leftH + '" fill="var(--text)" rx="2"/>' +
      '<text x="' + (lx - 6) + '" y="' + (ly + leftH / 2 - 2) + '" text-anchor="end" font-size="9.5" fill="var(--text-soft)">' + (f.kind === 'settled' ? 'Receipts' : 'Expected') + '</text>' +
      '<text x="' + (lx - 6) + '" y="' + (ly + leftH / 2 + 10) + '" text-anchor="end" font-size="9" fill="var(--text-faint)">' + L.short(f.receipts) + '</text>' + h;
    return L.svg(W, H, h, 'sankey');
  }

  function renderFlows() {
    var h = '';
    plans().forEach(function (p) {
      var c = checkOf(p.id), f = flowFor(p);
      h += '<article class="card flowcard"><header><div><h3>' + esc(shortName(p)) + '</h3><p>' + esc(p.district || '') + ' &middot; ' + (p.area || '?') + ' ' + esc(p.unit || '') + ' &middot; ' + (L.KIND[p.kind] || p.kind) + '</p></div>' +
        '<span class="badge2 badge2--' + (c.badge === 'adds up' ? 'ok' : (c.badge === 'has gaps' ? 'miss' : 'off')) + '">' + esc(c.badge) + '</span></header>';
      h += f ? sankey(f) : '<p class="muted" style="padding:2rem 0">Not enough in the file to draw a money flow (needs an area, yield and price).</p>';
      h += '<footer><span>' + (f ? (f.kind === 'settled' ? 'Season ' + f.season + ' settled' : 'Expected, not yet sold') : '') + '</span><span>Trust <b>' + c.trust + '</b>/100</span></footer></article>';
    });
    $('flows').innerHTML = h || '<p class="muted">No plans to show.</p>';
  }

  /* ---- balance check -------------------------------------------------------- */
  function renderBalance() {
    var keys = [['budget', 'Budget adds up'], ['log', 'Spend logged'], ['settle', 'Money in = out'], ['history', 'Enough seasons']];
    var h = '<table><thead><tr><th>Plan</th>' + keys.map(function (k) { return '<th>' + k[1] + '</th>'; }).join('') + '<th>Trust</th></tr></thead><tbody>';
    plans().forEach(function (p) {
      var c = checkOf(p.id);
      h += '<tr><th scope="row">' + esc(shortName(p)) + '<small>' + esc(p.district || '') + '</small></th>';
      keys.forEach(function (k) {
        var x = c.checks.filter(function (q) { return q.key === k[0]; })[0];
        h += '<td><span class="pilltag pilltag--' + x.status + '" title="' + esc(x.detail) + '">' + STATUS_ICON[x.status] + ' ' + STATUS_TEXT[x.status] + '</span></td>';
      });
      h += '<td class="tc">' + L.ring(c.trust, 40) + '</td></tr>';
    });
    $('balance').innerHTML = h + '</tbody></table>';

    var n = '<h3>Needs a human</h3>';
    var any = false;
    plans().forEach(function (p) {
      checkOf(p.id).flags.forEach(function (f) { any = true; n += '<p class="flag"><b>' + esc(shortName(p)) + '.</b> ' + esc(f) + '</p>'; });
    });
    $('needs').innerHTML = any ? n : '<h3>Needs a human</h3><p class="muted">Nothing to flag: every account in view adds up.</p>';
    if (state.issues && state.issues.length) {
      $('needs').innerHTML += '<h3 style="margin-top:1.2rem">While reading the file</h3>' + state.issues.map(function (i) { return '<p class="flag">' + esc(i) + '</p>'; }).join('');
    }
  }

  /* ---- seasons & yield ------------------------------------------------------ */
  function renderSeasons() {
    var jobs = plans().map(function (p) {
      return L.post('/api/risk', { plan: p, runs: 400 }).then(function (r) { return { p: p, r: r }; }, function () { return { p: p, r: null }; });
    });
    $('seasons').innerHTML = '<p class="muted">Reconciling sources&hellip;</p>';
    Promise.all(jobs).then(function (rows) {
      $('seasons').innerHTML = rows.map(function (x) { return seasonCard(x.p, x.r); }).join('') || '<p class="muted">No plans to show.</p>';
    });
  }
  function seasonCard(p, r) {
    var hist = (p.history || []).map(function (h) { return [h[0], h[1]]; });
    var W = 380, H = 190, pl = 34, pr = 10, pt = 14, pb = 26;
    var vals = hist.map(function (h) { return h[1]; }).concat([p.expected_yield || 0, p.benchmark ? p.benchmark[0] : 0, r && r.reconciliation.mean || 0]);
    var max = Math.max.apply(null, vals) * 1.18 || 1;
    var y = L.scale(0, max, H - pb, pt), bw = hist.length ? Math.min(34, (W - pl - pr) / hist.length - 8) : 0;
    var g = '';
    [0, 0.5, 1].forEach(function (t) { var yy = y(max / 1.18 * t); g += '<line x1="' + pl + '" x2="' + (W - pr) + '" y1="' + yy + '" y2="' + yy + '" stroke="var(--line)" stroke-dasharray="3 4"/><text x="' + (pl - 5) + '" y="' + (yy + 3) + '" text-anchor="end" font-size="9" fill="var(--text-faint)">' + (max / 1.18 * t).toFixed(1) + '</text>'; });
    hist.forEach(function (h, i) {
      var x = pl + 6 + i * ((W - pl - pr) / hist.length);
      g += '<rect x="' + x + '" y="' + y(h[1]) + '" width="' + bw + '" height="' + (H - pb - y(h[1])) + '" rx="3" fill="var(--burgundy)" opacity=".85"/>' +
        '<text x="' + (x + bw / 2) + '" y="' + (H - 9) + '" text-anchor="middle" font-size="9" fill="var(--text-faint)">' + Math.floor(h[0]) + '</text>';
    });
    function line(v, colour, label, dash) { if (!v) { return ''; } var yy = y(v); return '<line x1="' + pl + '" x2="' + (W - pr) + '" y1="' + yy + '" y2="' + yy + '" stroke="' + colour + '" stroke-width="1.6"' + (dash ? ' stroke-dasharray="5 4"' : '') + '/><text x="' + (W - pr) + '" y="' + (yy - 4) + '" text-anchor="end" font-size="9" fill="' + colour + '">' + label + ' ' + v + '</text>'; }
    g += line(p.expected_yield, 'var(--gold)', 'plan says', true);
    if (p.benchmark) { g += line(p.benchmark[0], 'var(--text-faint)', 'benchmark (assumed)', true); }
    if (r && r.reconciliation.mean) { g += line(r.reconciliation.mean, 'var(--leaf)', 'reconciled', false); }
    var rec = r ? r.reconciliation : null;
    return '<article class="card seasoncard"><header><h3>' + esc(shortName(p)) + '</h3><p>' + esc(p.yield_unit || 'yield') + '</p></header>' +
      (hist.length ? L.svg(W, H, g, 'seasonchart') : '<p class="muted" style="padding:1.5rem 0">No past seasons in the file.</p>') +
      (rec && rec.mean ? '<footer><span>Reconciled <b>' + rec.mean + '</b> &plusmn;' + rec.rel_error_95 + '%</span><span>Sources agree: ' + (rec.agreement <= 1 ? 'yes' : (rec.agreement <= 2 ? 'roughly' : 'no')) + '</span></footer>' : '') + '</article>';
  }

  /* ---- input costs ----------------------------------------------------------- */
  function adjusted(cat, amt) { return amt * (1 + (adj[cat] || 0) / 100); }
  function renderCosts() {
    var w = '<h3>Change the unit costs</h3><div class="sliders">';
    Object.keys(adj).forEach(function (k) {
      w += '<div class="f"><div class="f__top"><label for="adj-' + esc(k) + '">' + esc(k) + ' price change</label><output>' + (adj[k] > 0 ? '+' : '') + adj[k] + '%</output></div>' +
        '<input type="range" id="adj-' + esc(k) + '" data-adj="' + esc(k) + '" min="-30" max="60" step="5" value="' + adj[k] + '"></div>';
    });
    $('whatif').innerHTML = w + '</div>';
    document.querySelectorAll('[data-adj]').forEach(function (el) {
      el.style.setProperty('--p', ((el.value - el.min) / (el.max - el.min) * 100) + '%');
      el.addEventListener('input', function () { adj[el.getAttribute('data-adj')] = parseFloat(el.value); renderCosts(); });
    });

    var cats = {}, totals = {};
    plans().forEach(function (p) {
      var t = 0;
      p.costs.forEach(function (c) { var a = adjusted(c[1], c[2]); cats[c[1]] = cats[c[1]] || {}; cats[c[1]][p.id] = (cats[c[1]][p.id] || 0) + a; t += a; });
      totals[p.id] = t;
    });
    var order = ['Inputs', 'Seed', 'Labour', 'Water and power', 'Animals', 'Feed', 'Health', 'Setup', 'Other'].filter(function (c) { return cats[c]; })
      .concat(Object.keys(cats).filter(function (c) { return ['Inputs', 'Seed', 'Labour', 'Water and power', 'Animals', 'Feed', 'Health', 'Setup', 'Other'].indexOf(c) < 0; }));
    var palette = ['var(--burgundy-deep)', 'var(--burgundy)', 'var(--burgundy-hi)', 'var(--gold-soft)', '#D9A0AD', '#B98C93', 'var(--leaf)', '#A9A0A1', '#D9C3BC'];
    var h = '<h3>Budget by category</h3>';
    var max = Math.max.apply(null, Object.keys(totals).map(function (k) { return totals[k]; })) || 1;
    plans().forEach(function (p) {
      h += '<div class="stackrow"><div class="stackrow__n">' + esc(shortName(p)) + '</div><div class="stackrow__bar" style="width:' + (totals[p.id] / max * 100) + '%">';
      order.forEach(function (c, i) { var v = (cats[c] || {})[p.id]; if (v) { h += '<i style="flex:' + v + ';background:' + palette[i % palette.length] + '" title="' + esc(c) + ': ' + inr(v) + '"></i>'; } });
      h += '</div><div class="stackrow__v">' + L.short(totals[p.id]) + '</div></div>';
    });
    h += '<ul class="legend2">' + order.map(function (c, i) { return '<li><i style="background:' + palette[i % palette.length] + '"></i>' + esc(c) + '</li>'; }).join('') + '</ul>';
    h += '<table class="mini" style="margin-top:1.2rem"><thead><tr><th>Category</th>' + plans().map(function (p) { return '<th class="r">' + esc(shortName(p)) + '</th>'; }).join('') + '</tr></thead><tbody>';
    order.forEach(function (c) { h += '<tr><td>' + esc(c) + '</td>' + plans().map(function (p) { var v = (cats[c] || {})[p.id]; return '<td class="r">' + (v ? inr(v) : '&ndash;') + '</td>'; }).join('') + '</tr>'; });
    h += '<tr class="tot"><td>Total</td>' + plans().map(function (p) { return '<td class="r">' + inr(totals[p.id] || 0) + '</td>'; }).join('') + '</tr></tbody></table>';
    $('costs').innerHTML = h;
  }

  /* ---- tabs, filter, actions --------------------------------------------------- */
  function render() {
    renderSummary(); renderFilter();
    if (tab === 'overview') { renderFlows(); }
    if (tab === 'balance') { renderBalance(); }
    if (tab === 'seasons') { renderSeasons(); }
    if (tab === 'costs') { renderCosts(); }
    $('csvpeek').textContent = (state.csv || '').split('\n').slice(0, 16).join('\n') + '\n…';
  }
  document.querySelectorAll('[data-tab]').forEach(function (b) {
    b.addEventListener('click', function () {
      tab = b.getAttribute('data-tab');
      document.querySelectorAll('[data-tab]').forEach(function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
      ['overview', 'balance', 'seasons', 'costs'].forEach(function (t) { $('tab-' + t).hidden = t !== tab; });
      render();
    });
  });
  $('filter').addEventListener('click', function (e) { var b = e.target.closest('[data-f]'); if (b) { filter = b.getAttribute('data-f'); render(); } });

  function download(name, text, type) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: type || 'text/csv' }));
    a.download = name; document.body.appendChild(a); a.click(); a.remove();
  }
  $('btnCsv').addEventListener('click', function () { download('bhoomi-ledger.csv', state.csv); });
  $('btnPrint').addEventListener('click', function () { window.print(); });
  $('btnReset').addEventListener('click', function () { L.clear(); boot(); });
  $('dlTemplate').addEventListener('click', function (e) { e.preventDefault(); L.example().then(function (ex) { download('bhoomi-ledger-example.csv', ex.csv); }); });

  /* ---- the import dialog --------------------------------------------------------- */
  var modal = $('modal');
  function openModal() { modal.hidden = false; $('msteps').innerHTML = ''; $('merr').hidden = true; $('missues').hidden = true; document.body.classList.add('modal-open'); }
  function closeModal() { modal.hidden = true; document.body.classList.remove('modal-open'); }
  $('btnImport').addEventListener('click', openModal);
  modal.addEventListener('click', function (e) { if (e.target.closest('[data-close]')) { closeModal(); } });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) { closeModal(); } });
  document.querySelectorAll('[data-m]').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('[data-m]').forEach(function (x) { x.classList.toggle('is-on', x === b); });
      $('m-file').hidden = b.getAttribute('data-m') !== 'file'; $('m-paste').hidden = b.getAttribute('data-m') !== 'paste';
    });
  });

  function steps(list) { $('msteps').innerHTML = list.map(function (s) { return '<li class="' + (s[1] ? 'done' : '') + '">' + esc(s[0]) + '</li>'; }).join(''); }
  function importText(text, label) {
    $('merr').hidden = true; $('missues').hidden = true;
    steps([['Opened ' + label, true], ['Reading every row by its record type…', false]]);
    L.post('/api/ledger/import', { csv: text }).then(function (res) {
      res.csv = text; res.source = 'import';
      steps([['Opened ' + label, true], ['Read ' + res.plans.length + ' plans', true], ['Checked every plan against the balance rules', true], ['Linked past seasons and budgets', true]]);
      if (res.issues.length) { $('missues').hidden = false; $('missues').innerHTML = '<li class="head">Needs a human</li>' + res.issues.slice(0, 12).map(function (i) { return '<li>' + esc(i) + '</li>'; }).join(''); }
      L.save(res); state = res; filter = 'all'; render();
      if (!res.issues.length) { window.setTimeout(closeModal, 700); }
    }).catch(function (err) { $('msteps').innerHTML = ''; $('merr').hidden = false; $('merr').textContent = err.message; });
  }
  $('useExample').addEventListener('click', function () { L.example().then(function (ex) { importText(ex.csv, 'the example farm’s file'); }); });
  $('readPaste').addEventListener('click', function () { importText($('paste').value, 'pasted text'); });
  function readFile(f) { var r = new FileReader(); r.onload = function () { importText(String(r.result), f.name); }; r.readAsText(f); }
  $('file').addEventListener('change', function () { if (this.files[0]) { readFile(this.files[0]); } });
  var drop = $('drop');
  ['dragover', 'dragenter'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('is-over'); }); });
  ['dragleave', 'drop'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('is-over'); }); });
  drop.addEventListener('drop', function (e) { if (e.dataTransfer.files[0]) { readFile(e.dataTransfer.files[0]); } });

  function boot() { L.current().then(function (s) { state = s; filter = 'all'; render(); }); }
  boot();
})();
