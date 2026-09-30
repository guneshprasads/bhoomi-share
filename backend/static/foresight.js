/* Foresight canvas: drag the year along an illustrative S-curve and read the milestone. */
(function () {
  'use strict';
  var M = (window.BHOOMI_MILES || []).map(function (m) { return { y: m[0], title: m[1], body: m[2] }; });
  var slider = document.getElementById('year'), out = document.getElementById('yearOut'), now = document.getElementById('now'), trend = document.getElementById('trend');
  if (!slider || !M.length) { return; }

  // an S-curve from 6 to 92, steepest around 2030-31: a direction, not data
  function idx(y) { return 6 + 86 / (1 + Math.exp(-(y - 2030.6) * 0.62)); }
  var W = 900, H = 240, pl = 40, pr = 20, pt = 18, pb = 34;
  var x = function (y) { return pl + (y - 2026) / 10 * (W - pl - pr); };
  var yy = function (v) { return H - pb - v / 100 * (H - pb - pt); };

  function draw(year) {
    var pts = [], area = [];
    for (var t = 2026; t <= 2036.001; t += 0.1) { pts.push(x(t).toFixed(1) + ',' + yy(idx(t)).toFixed(1)); }
    var g = '<defs><linearGradient id="fsg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--burgundy)" stop-opacity=".28"/><stop offset="1" stop-color="var(--burgundy)" stop-opacity="0"/></linearGradient></defs>';
    [0, 25, 50, 75, 100].forEach(function (v) { g += '<line x1="' + pl + '" x2="' + (W - pr) + '" y1="' + yy(v) + '" y2="' + yy(v) + '" stroke="var(--line)" stroke-dasharray="3 5"/><text x="' + (pl - 8) + '" y="' + (yy(v) + 3) + '" text-anchor="end" font-size="10" fill="var(--text-faint)">' + v + '</text>'; });
    g += '<polygon points="' + x(2026) + ',' + yy(0) + ' ' + pts.join(' ') + ' ' + x(2036) + ',' + yy(0) + '" fill="url(#fsg)"/>';
    g += '<polyline points="' + pts.join(' ') + '" fill="none" stroke="var(--burgundy)" stroke-width="3" stroke-linecap="round"/>';
    for (var y = 2026; y <= 2036; y++) { g += '<text x="' + x(y) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="10.5" fill="' + (y === year ? 'var(--burgundy)' : 'var(--text-faint)') + '" font-weight="' + (y === year ? 700 : 400) + '">' + y + '</text>'; }
    M.forEach(function (m) {
      var on = m.y === year;
      g += '<circle cx="' + x(m.y) + '" cy="' + yy(idx(m.y)) + '" r="' + (on ? 8 : 5.5) + '" fill="' + (on ? 'var(--burgundy)' : '#fff') + '" stroke="var(--burgundy)" stroke-width="2.5" style="cursor:pointer" data-y="' + m.y + '"><title>' + m.y + ': ' + m.title + '</title></circle>';
    });
    g += '<line x1="' + x(year) + '" x2="' + x(year) + '" y1="' + pt + '" y2="' + (H - pb) + '" stroke="var(--text)" stroke-width="1.4" stroke-dasharray="4 4"/>' +
      '<circle cx="' + x(year) + '" cy="' + yy(idx(year)) + '" r="6" fill="var(--text)"/>' +
      '<text x="' + Math.min(Math.max(x(year), 60), W - 60) + '" y="' + (yy(idx(year)) - 14) + '" text-anchor="middle" font-size="12" font-weight="700" fill="var(--text)">index ' + Math.round(idx(year)) + '</text>';
    trend.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" class="fsvg" role="img" aria-label="Illustrative index of farm-level money risk becoming visible, 2026 to 2036">' + g + '</svg>';
  }

  function update() {
    var year = parseInt(slider.value, 10);
    out.textContent = year;
    slider.style.setProperty('--p', ((year - 2026) / 10 * 100) + '%');
    var m = M.filter(function (z) { return z.y <= year; }).pop() || M[0];
    now.innerHTML = '<span class="pill pill--rose">' + m.y + (m.y === year ? '' : ' (latest milestone)') + '</span><h3>' + m.title + '</h3><p>' + m.body + '</p>';
    document.querySelectorAll('.fsmiles li').forEach(function (li) { li.classList.toggle('is-on', parseInt(li.getAttribute('data-year'), 10) === m.y); });
    draw(year);
  }
  slider.addEventListener('input', update);
  trend.addEventListener('click', function (e) { var c = e.target.closest('[data-y]'); if (c) { slider.value = c.getAttribute('data-y'); update(); } });
  update();
})();
