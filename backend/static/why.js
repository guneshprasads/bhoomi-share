/* Charts for /why. They read static/data/why.json (World Bank and FAO series),
   the same file the page's numbers are computed from. */
(function () {
  'use strict';
  var cfg = window.BHOOMI_WHY || {};
  var NS = 'http://www.w3.org/2000/svg';
  function svg(w, h, inner) {
    return '<svg xmlns="' + NS + '" viewBox="0 0 ' + w + ' ' + h + '" class="wsvg" role="img" preserveAspectRatio="xMidYMid meet">' + inner + '</svg>';
  }
  function scale(d0, d1, r0, r1) { return function (v) { return r0 + (v - d0) / ((d1 - d0) || 1) * (r1 - r0); }; }
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  function food(d) {
    var pts = d.food_inflation_monthly;               // [["2010-01", 14.9], ...]
    var W = 920, H = 320, pl = 44, pr = 16, pt = 22, pb = 34;
    var t = function (p) { var a = p.split('-'); return parseInt(a[0], 10) + (parseInt(a[1], 10) - 1) / 12; };
    var vals = pts.map(function (p) { return p[1]; });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var y0 = Math.floor(Math.min(lo, 0) / 5) * 5, y1 = Math.ceil(hi / 5) * 5 + 2;
    var x = scale(t(pts[0][0]), t(pts[pts.length - 1][0]), pl, W - pr), y = scale(y0, y1, H - pb, pt);
    var g = '';
    for (var v = y0; v <= y1; v += 5) {
      g += '<line x1="' + pl + '" x2="' + (W - pr) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="' + (v === 0 ? 'var(--text)' : 'var(--line)') + '" stroke-width="' + (v === 0 ? 1.4 : 1) + '" stroke-dasharray="' + (v === 0 ? '' : '3 5') + '"/>' +
        '<text x="' + (pl - 8) + '" y="' + (y(v) + 3) + '" text-anchor="end" font-size="10.5" fill="var(--text-faint)">' + v + '%</text>';
    }
    var first = parseInt(pts[0][0], 10), last = parseInt(pts[pts.length - 1][0], 10);
    for (var yr = first; yr <= last; yr += 2) {
      g += '<text x="' + x(yr) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="10.5" fill="var(--text-faint)">' + yr + '</text>';
    }
    var line = pts.map(function (p) { return x(t(p[0])).toFixed(1) + ',' + y(p[1]).toFixed(1); }).join(' ');
    g += '<polygon points="' + x(t(pts[0][0])) + ',' + y(0) + ' ' + line + ' ' + x(t(pts[pts.length - 1][0])) + ',' + y(0) + '" fill="var(--burgundy)" opacity=".10"/>';
    g += '<polyline points="' + line + '" fill="none" stroke="var(--burgundy)" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>';
    var hiP = pts.reduce(function (a, b) { return b[1] > a[1] ? b : a; }), loP = pts.reduce(function (a, b) { return b[1] < a[1] ? b : a; });
    function mark(p, label, dy) {
      var px = x(t(p[0])), py = y(p[1]);
      var m = p[0].split('-');
      return '<circle cx="' + px + '" cy="' + py + '" r="5.5" fill="#fff" stroke="var(--burgundy)" stroke-width="2.5"/>' +
        '<text x="' + px + '" y="' + (py + dy) + '" text-anchor="middle" font-size="12" font-weight="700" fill="var(--text)">' + label + ' ' + p[1].toFixed(1) + '%</text>' +
        '<text x="' + px + '" y="' + (py + dy + 13) + '" text-anchor="middle" font-size="10.5" fill="var(--text-faint)">' + MON[parseInt(m[1], 10) - 1] + ' ' + m[0] + '</text>';
    }
    g += mark(hiP, 'peak', -26) + mark(loP, 'low', 20);
    document.getElementById('foodChart').innerHTML = svg(W, H, g);
  }

  function shares(d) {
    var a = d.annual;
    var W = 920, H = 300, pl = 44, pr = 150, pt = 22, pb = 34;
    var x = scale(a[0].year, a[a.length - 1].year, pl, W - pr), y = scale(0, 60, H - pb, pt);
    var g = '';
    [0, 15, 30, 45, 60].forEach(function (v) {
      g += '<line x1="' + pl + '" x2="' + (W - pr) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="var(--line)" stroke-dasharray="3 5"/><text x="' + (pl - 8) + '" y="' + (y(v) + 3) + '" text-anchor="end" font-size="10.5" fill="var(--text-faint)">' + v + '%</text>';
    });
    a.forEach(function (r, i) { if (i % 3 === 0 || i === a.length - 1) { g += '<text x="' + x(r.year) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="10.5" fill="var(--text-faint)">' + r.year + '</text>'; } });
    function series(key, colour, label, dy) {
      var pts = a.map(function (r) { return x(r.year).toFixed(1) + ',' + y(r[key]).toFixed(1); }).join(' ');
      var l = a[a.length - 1], f = a[0];
      return '<polyline points="' + pts + '" fill="none" stroke="' + colour + '" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>' +
        '<circle cx="' + x(f.year) + '" cy="' + y(f[key]) + '" r="4.5" fill="' + colour + '"/><circle cx="' + x(l.year) + '" cy="' + y(l[key]) + '" r="5.5" fill="' + colour + '"/>' +
        '<text x="' + (x(l.year) + 12) + '" y="' + (y(l[key]) + dy) + '" font-size="12.5" font-weight="700" fill="' + colour + '">' + l[key].toFixed(1) + '%</text>' +
        '<text x="' + (x(l.year) + 12) + '" y="' + (y(l[key]) + dy + 14) + '" font-size="10.5" fill="var(--text-soft)">' + label + '</text>' +
        '<text x="' + (x(f.year)) + '" y="' + (y(f[key]) - 11) + '" text-anchor="middle" font-size="11" fill="' + colour + '">' + f[key].toFixed(1) + '%</text>';
    }
    g += series('agri_employment', 'var(--burgundy)', 'of all workers', 4) + series('agri_gdp_share', 'var(--gold)', 'of GDP', 4);
    var l = a[a.length - 1];
    g += '<line x1="' + x(l.year) + '" x2="' + x(l.year) + '" y1="' + y(l.agri_employment) + '" y2="' + y(l.agri_gdp_share) + '" stroke="var(--text-faint)" stroke-dasharray="3 3"/>';
    document.getElementById('shareChart').innerHTML = svg(W, H, g);
  }

  fetch(cfg.data).then(function (r) { return r.json(); }).then(function (d) { food(d); shares(d); })
    .catch(function () {
      ['foodChart', 'shareChart'].forEach(function (id) { var e = document.getElementById(id); if (e) { e.innerHTML = '<p class="muted" style="padding:1.5rem">The chart could not load. The figures above are still correct.</p>'; } });
    });
})();
