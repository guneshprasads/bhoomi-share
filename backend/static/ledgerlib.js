/* Shared by the Farm ledger and Money-at-risk pages: the ledger held in the
   browser (so an imported file carries from one page to the other), rupee
   formatting, and small SVG chart helpers. No dependencies. */
(function () {
  'use strict';
  var KEY = 'bhoomi.ledger.v1';
  var L = window.BhoomiLedger = {};

  L.inr = function (n) {
    n = Math.round(n || 0);
    var neg = n < 0; n = Math.abs(n);
    var s = String(n);
    if (s.length > 3) {
      var tail = s.slice(-3), head = s.slice(0, -3), parts = [];
      while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2); }
      if (head) { parts.unshift(head); }
      s = parts.join(',') + ',' + tail;
    }
    return (neg ? '−' : '') + '₹' + s;
  };
  L.short = function (n) {               // 1,42,000 -> ₹1.4L ; 12,50,000 -> ₹12.5L ; 2.5 crore -> ₹2.5Cr
    var a = Math.abs(n), sign = n < 0 ? '−' : '';
    if (a >= 1e7) { return sign + '₹' + (a / 1e7).toFixed(a >= 1e8 ? 0 : 1) + 'Cr'; }
    if (a >= 1e5) { return sign + '₹' + (a / 1e5).toFixed(a >= 1e6 ? 1 : 2).replace(/\.?0+$/, '') + 'L'; }
    if (a >= 1e3) { return sign + '₹' + (a / 1e3).toFixed(a >= 1e4 ? 0 : 1).replace(/\.0$/, '') + 'k'; }
    return sign + '₹' + Math.round(a);
  };
  L.pct = function (x, d) { return (x * 100).toFixed(d == null ? 0 : d) + '%'; };
  L.esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };

  /* ---- the ledger in this browser ---------------------------------------- */
  L.save = function (payload) { try { sessionStorage.setItem(KEY, JSON.stringify(payload)); } catch (e) { /* private mode: fine */ } };
  L.load = function () { try { return JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch (e) { return null; } };
  L.clear = function () { try { sessionStorage.removeItem(KEY); } catch (e) { /* ignore */ } };

  L.example = function () {
    return fetch('/api/ledger/example').then(function (r) { return r.json(); });
  };
  L.current = function () {
    var saved = L.load();
    return saved ? Promise.resolve(saved) : L.example().then(function (p) { p.source = 'example'; L.save(p); return p; });
  };
  L.post = function (url, body) {
    return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (j) { if (!r.ok) { throw new Error(j.error || 'Something went wrong.'); } return j; }); });
  };

  /* ---- svg helpers -------------------------------------------------------- */
  var NS = 'http://www.w3.org/2000/svg';
  L.svg = function (w, h, inner, cls) {
    return '<svg xmlns="' + NS + '" viewBox="0 0 ' + w + ' ' + h + '" class="' + (cls || '') + '" role="img" preserveAspectRatio="xMidYMid meet">' + inner + '</svg>';
  };
  L.scale = function (d0, d1, r0, r1) { return function (v) { return r0 + (v - d0) / ((d1 - d0) || 1) * (r1 - r0); }; };

  L.ring = function (score, size) {      // trust score ring
    var r = 26, c = 2 * Math.PI * r, off = c * (1 - Math.max(0, Math.min(100, score)) / 100);
    var col = score >= 80 ? 'var(--leaf)' : (score >= 55 ? 'var(--gold-soft)' : 'var(--rose)');
    return '<svg viewBox="0 0 64 64" width="' + (size || 64) + '" height="' + (size || 64) + '" class="ring" role="img" aria-label="Trust score ' + score + ' of 100">' +
      '<circle cx="32" cy="32" r="' + r + '" fill="none" stroke="var(--surface-3)" stroke-width="7"/>' +
      '<circle cx="32" cy="32" r="' + r + '" fill="none" stroke="' + col + '" stroke-width="7" stroke-linecap="round" stroke-dasharray="' + c.toFixed(1) + '" stroke-dashoffset="' + off.toFixed(1) + '" transform="rotate(-90 32 32)"/>' +
      '<text x="32" y="37" text-anchor="middle" font-family="var(--display)" font-weight="700" font-size="17" fill="var(--text)">' + score + '</text></svg>';
  };

  L.costTotal = function (p) {
    var lines = (p.costs || []).reduce(function (s, c) { return s + c[2]; }, 0);
    return lines || p.stated_budget || 0;
  };
  L.KIND = { crop: 'Crop plan', livestock: 'Livestock unit', space: 'Small space', shares: 'Land shares' };
})();
