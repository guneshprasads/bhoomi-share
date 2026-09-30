/* "Ways to earn": role tabs and live calculators.
   Every number comes from /api/simulate, the same Python the tests cover, so the
   page cannot drift from the maths. With JS off the page still shows all four
   explanations and a worked example rendered by the server. */
(function () {
  'use strict';

  var LANG = (document.documentElement.lang || 'en').slice(0, 2);
  var KN = LANG === 'kn';
  var D = window.BHOOMI_DEFAULTS || {};

  var T = {
    strong: KN ? 'ಉತ್ತಮ ಋತು' : 'Strong season',
    expected: KN ? 'ನಿರೀಕ್ಷಿತ' : 'As planned',
    weak: KN ? 'ದುರ್ಬಲ ಋತು' : 'Weak season',
    failed: KN ? 'ವಿಫಲ ಋತು' : 'Failed season',
    sale: KN ? 'ಮಾರಾಟ' : 'sale',
    back: KN ? 'ಮರಳುವುದು' : 'back',
    putIn: KN ? 'ಹಾಕಿದ್ದು' : 'Put in',
    expSale: KN ? 'ನಿರೀಕ್ಷಿತ ಮಾರಾಟ' : 'expected sale',
    breakeven: KN ? 'ಸಮತೋಲನ ಮಾರಾಟ' : 'break-even sale',
    keep: KN ? 'ನಿಮ್ಮ ಪಾಲು' : 'You keep',
    perSeason: KN ? 'ಋತುವಿಗೆ' : 'Per season',
    perYear: KN ? 'ವರ್ಷಕ್ಕೆ' : 'Per year',
    netYear: KN ? 'ಖರ್ಚು ನಂತರ ವರ್ಷಕ್ಕೆ' : 'Per year after upkeep',
    perAcre: KN ? 'ಎಕರೆಗೆ' : 'per acre',
    total: KN ? 'ಒಟ್ಟು' : 'total',
    costAcre: KN ? 'ಎಕರೆಗೆ ವೆಚ್ಚ (ಒಳಸುರಿ + ಬಾಡಿಗೆ)' : 'Cost per acre (inputs + rent)',
    breakRev: KN ? 'ಸಮತೋಲನಕ್ಕೆ ಬೇಕಾದ ಆದಾಯ' : 'Revenue per acre you need just to break even',
    ofExpected: KN ? 'ನಿರೀಕ್ಷೆಯ' : 'of what you expect',
    unpaid: KN ? 'ನಿಮ್ಮ ದುಡಿಮೆಗೆ ಏನೂ ಸಿಗುವುದಿಲ್ಲ' : 'Your labour goes unpaid',
    termNote: KN ? 'ಪರವಾನಗಿ ನಿಗದಿತ ಅವಧಿಯದು; ನವೀಕರಿಸಿದರೆ ಮಾತ್ರ ಈ ವರ್ಷದ ಬಾಡಿಗೆ ಮುಂದುವರಿಯುತ್ತದೆ.'
      : 'A licence has a fixed term. This is what one year pays if it is renewed.',
    growerNote: KN ? 'ನಿಮ್ಮ ಸಮಯ ಮತ್ತು ದುಡಿಮೆಯ ವೆಚ್ಚವನ್ನು ಇದರಲ್ಲಿ ಎಣಿಸಿಲ್ಲ.' : 'Your own time and labour are not counted in these figures.'
  };

  function inr(n) {
    n = Math.round(n);
    var neg = n < 0; n = Math.abs(n);
    var s = String(n);
    if (s.length > 3) {
      var tail = s.slice(-3), head = s.slice(0, -3), parts = [];
      while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2); }
      if (head) { parts.unshift(head); }
      s = parts.join(',') + ',' + tail;
    }
    return (neg ? '-' : '') + s;
  }
  function rupee(n) { return '₹' + inr(n); }
  function sign(n) { return n > 0 ? '+' : ''; }

  /* ---- control definitions -------------------------------------------- */
  var M = function (k, label, min, max, step, unit) { return { k: k, label: label, min: min, max: max, step: step, unit: unit || 'inr' }; };
  var FIELDS = {
    crop: [
      M('cost', 'Budget: the costs the plan lists', 10000, 2000000, 5000),
      M('sale', 'Expected sale value', 10000, 4000000, 5000),
      M('investor_pct', 'Investor share of what is left', 0, 100, 5, 'pct')
    ],
    livestock: [
      M('cost', 'Budget: animals, feed, shed, vet', 25000, 3000000, 10000),
      M('sale', 'Expected sale value', 25000, 6000000, 10000),
      M('investor_pct', 'Investor share of what is left', 0, 100, 5, 'pct')
    ],
    space: [
      M('setup', 'One-time setup (racks, spawn, fittings)', 0, 500000, 5000),
      M('batches', 'Batches the plan covers', 1, 24, 1, 'n'),
      M('batch_cost', 'Cost of each batch', 1000, 100000, 500),
      M('batch_sale', 'What each batch sells for', 1000, 200000, 500),
      M('investor_pct', 'Investor share of what is left', 0, 100, 5, 'pct')
    ],
    shares: [
      M('total_units', 'Shares in the parcel', 10, 200, 1, 'n'),
      M('unit_price', 'Value of one share', 5000, 100000, 1000),
      M('units_held', 'Shares you hold', 1, 200, 1, 'n'),
      M('sale', 'Expected sale value of the cycle', 100000, 20000000, 50000),
      M('investor_pct', 'Funders’ share of what is left', 0, 100, 5, 'pct')
    ],
    grower: [
      M('cost', 'Budget your funder covers', 10000, 2000000, 5000),
      M('sale', 'Expected sale value', 10000, 4000000, 5000),
      M('grower_pct', 'Your share of what is left', 0, 100, 5, 'pct')
    ],
    landowner: [
      M('acres', 'Area you licence out (acres)', 0.5, 50, 0.5, 'ac'),
      M('rent_per_acre', 'Rent per acre per season', 0, 50000, 500),
      M('seasons', 'Seasons per year', 1, 3, 1, 'n'),
      M('upkeep_per_acre', 'Your yearly upkeep per acre (tax, bunds)', 0, 10000, 100)
    ],
    farmer: [
      M('acres', 'Area you farm (acres)', 0.5, 50, 0.5, 'ac'),
      M('revenue_per_acre', 'Expected revenue per acre', 5000, 200000, 1000),
      M('inputs_per_acre', 'Inputs per acre (seed, water, labour)', 1000, 120000, 500),
      M('rent_per_acre', 'Rent per acre', 0, 50000, 500)
    ]
  };

  function defaultsFor(group, model) {
    if (group === 'grower') {
      var c = D.crop || {};
      return { cost: c.cost, sale: c.sale, grower_pct: 100 - (c.investor_pct || 70) };
    }
    return Object.assign({}, D[model] || D[group] || {});
  }
  function kindFor(group, model) { return group === 'investor' ? model : (group === 'grower' ? 'crop' : group); }

  function fmt(f, v) {
    if (f.unit === 'pct') { return v + '%'; }
    if (f.unit === 'n') { return String(v); }
    if (f.unit === 'ac') { return v + ' ac'; }
    return rupee(v);
  }

  /* ---- renderers -------------------------------------------------------- */
  function label(key) { return T[key]; }

  function rFunded(r) {
    var h = '<div class="res"><p class="res__sum">' + T.putIn + ' <b>' + rupee(r.cost) + '</b> · ' + T.expSale +
      ' <b>' + rupee(r.expected_sale) + '</b> · ' + T.breakeven + ' <b>' + rupee(r.breakeven_sale) + '</b></p>';
    r.scenarios.forEach(function (s) {
      h += '<div class="res__row"><div class="res__name">' + label(s.key) + '<small>' + T.sale + ' ' + rupee(s.sale) + '</small></div>' +
        '<div class="res__get">' + T.back + ' ' + rupee(s.you_get_back) + '</div>' +
        '<div class="res__net ' + (s.you_net < 0 ? 'neg' : 'pos') + '">' + sign(s.you_net) + inr(s.you_net) +
        ' <small>(' + sign(s.you_return_pct) + s.you_return_pct + '%)</small></div></div>';
    });
    return h + '</div>';
  }
  function rGrower(r) {
    var h = '<div class="res"><p class="res__sum">' + T.putIn + ' <b>' + rupee(r.cost) + '</b> (' + (KN ? 'ನಿಮ್ಮ ಹಣಕಾಸುದಾರ' : 'your funder') + ') · ' +
      T.expSale + ' <b>' + rupee(r.expected_sale) + '</b></p>';
    r.scenarios.forEach(function (s) {
      h += '<div class="res__row"><div class="res__name">' + label(s.key) + '<small>' + T.sale + ' ' + rupee(s.sale) + '</small></div>' +
        '<div class="res__get">' + T.keep + '</div>' +
        '<div class="res__net ' + (s.grower_take > 0 ? 'pos' : 'neg') + '">' + (s.grower_take > 0 ? '+' + inr(s.grower_take) : '0') +
        (s.grower_take === 0 ? ' <small>' + T.unpaid + '</small>' : '') + '</div></div>';
    });
    return h + '<p class="res__note">' + T.growerNote + '</p></div>';
  }
  function rLandowner(r) {
    return '<div class="res res--big"><div class="big"><span>' + T.perSeason + '</span><b>' + rupee(r.per_season) + '</b></div>' +
      '<div class="big"><span>' + T.perYear + '</span><b>' + rupee(r.per_year) + '</b></div>' +
      '<div class="big big--hi"><span>' + T.netYear + '</span><b>' + rupee(r.net_per_year) + '</b></div>' +
      '<p class="res__note">' + T.termNote + '</p></div>';
  }
  function rFarmer(r) {
    var h = '<div class="res"><p class="res__sum">' + T.costAcre + ' <b>' + rupee(r.cost_per_acre) + '</b></p>';
    r.scenarios.forEach(function (s) {
      h += '<div class="res__row"><div class="res__name">' + label(s.key) + '<small>' + rupee(s.revenue_per_acre) + ' ' + T.perAcre + '</small></div>' +
        '<div class="res__get">' + rupee(s.profit_per_acre) + ' ' + T.perAcre + '</div>' +
        '<div class="res__net ' + (s.profit_total < 0 ? 'neg' : 'pos') + '">' + sign(s.profit_total) + inr(s.profit_total) + ' <small>' + T.total + '</small></div></div>';
    });
    h += '<p class="res__note">' + T.breakRev + ': <b>' + rupee(r.breakeven_revenue_per_acre) + '</b>' +
      (r.breakeven_vs_expected_pct ? ' (' + r.breakeven_vs_expected_pct + '% ' + T.ofExpected + ')' : '') + '</p></div>';
    return h;
  }
  var RENDER = { funded: rFunded, shares: rFunded, space: rFunded, landowner: rLandowner, farmer: rFarmer };

  /* ---- calculators ------------------------------------------------------ */
  function Calc(root) {
    var group = root.getAttribute('data-kind-group');
    var fieldsEl = root.querySelector('[data-fields]');
    var outEl = root.querySelector('[data-out]');
    var modelSel = root.querySelector('[data-model]');
    var model = modelSel ? modelSel.value : null;
    var values = {};
    var timer = null, seq = 0;

    function fieldKey() { return group === 'investor' ? model : group; }

    function build() {
      var kind = group === 'investor' ? model : group;
      values = defaultsFor(group, group === 'investor' ? model : null);
      var defs = FIELDS[kind];
      fieldsEl.innerHTML = '';
      defs.forEach(function (f) {
        var v = values[f.k];
        var wrap = document.createElement('div');
        wrap.className = 'f';
        var id = 'f-' + group + '-' + f.k;
        wrap.innerHTML = '<div class="f__top"><label for="' + id + '">' + f.label + '</label><output data-o></output></div>' +
          '<input type="range" id="' + id + '" min="' + f.min + '" max="' + f.max + '" step="' + f.step + '" value="' + v + '">';
        var range = wrap.querySelector('input');
        var o = wrap.querySelector('[data-o]');
        function show() { o.textContent = fmt(f, parseFloat(range.value)); range.style.setProperty('--p', ((range.value - f.min) / (f.max - f.min) * 100) + '%'); }
        show();
        range.addEventListener('input', function () {
          values[f.k] = parseFloat(range.value);
          if (f.k === 'total_units') { clampHeld(); }
          show(); schedule();
        });
        fieldsEl.appendChild(wrap);
      });
      schedule(true);
    }

    function clampHeld() {
      if (!('units_held' in values)) { return; }
      var held = fieldsEl.querySelector('#f-' + group + '-units_held');
      if (!held) { return; }
      held.max = values.total_units;
      if (parseFloat(held.value) > values.total_units) { held.value = values.total_units; values.units_held = values.total_units; }
      held.dispatchEvent(new Event('input'));
    }

    function schedule(now) {
      window.clearTimeout(timer);
      timer = window.setTimeout(run, now ? 0 : 120);
    }

    function run() {
      var kind = kindFor(group, model);
      var p = Object.assign({}, values);
      if (group === 'grower') { p.investor_pct = 100 - p.grower_pct; delete p.grower_pct; }
      var qs = Object.keys(p).map(function (k) { return encodeURIComponent(k) + '=' + encodeURIComponent(p[k]); }).join('&');
      var my = ++seq;
      fetch('/api/simulate/' + kind + '?' + qs, { headers: { 'Accept': 'application/json' } })
        .then(function (res) { return res.json().then(function (j) { return { ok: res.ok, j: j }; }); })
        .then(function (x) {
          if (my !== seq) { return; }
          if (!x.ok) { outEl.innerHTML = '<p class="res__err">' + (x.j.error || 'Check the numbers.') + '</p>'; return; }
          var r = x.j;
          var html = group === 'grower' ? rGrower(r) : (RENDER[r.kind] || rFunded)(r);
          outEl.innerHTML = html;
        })
        .catch(function () { outEl.innerHTML = '<p class="res__err">Could not reach the calculator. Try again.</p>'; });
    }

    if (modelSel) {
      modelSel.addEventListener('change', function () { model = modelSel.value; build(); });
    }
    build();
  }

  document.querySelectorAll('.calc').forEach(Calc);

  /* ---- tabs ------------------------------------------------------------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.panel2'));

  function select(role, focus) {
    if (!role || !document.getElementById(role)) { role = 'investor'; }
    tabs.forEach(function (t) {
      var on = t.getAttribute('data-role') === role;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      if (on && focus) { t.focus(); }
    });
    document.documentElement.classList.add('tabbed');
    panels.forEach(function (p) { p.classList.toggle('is-active', p.id === role); });
    if (history.replaceState) { history.replaceState(null, '', '#' + role); }
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { select(t.getAttribute('data-role')); });
    t.addEventListener('keydown', function (e) {
      var n = null;
      if (e.key === 'ArrowRight') { n = tabs[(i + 1) % tabs.length]; }
      if (e.key === 'ArrowLeft') { n = tabs[(i - 1 + tabs.length) % tabs.length]; }
      if (n) { e.preventDefault(); select(n.getAttribute('data-role'), true); }
    });
  });
  document.querySelectorAll('[data-jump]').forEach(function (b) {
    b.addEventListener('click', function () { select(b.getAttribute('data-jump')); window.scrollTo({ top: document.querySelector('.tabs').offsetTop - 90, behavior: 'smooth' }); });
  });
  window.addEventListener('hashchange', function () { select(location.hash.slice(1)); });
  select(location.hash.slice(1));
})();
