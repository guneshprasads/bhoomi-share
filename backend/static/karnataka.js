/* Karnataka tile map: choose a district, see what is open, jump to the filtered lists. */
(function () {
  'use strict';
  var KN = (document.documentElement.lang || 'en').slice(0, 2) === 'kn';
  var notes = window.BHOOMI_DIV_NOTES || {};
  var tiles = Array.prototype.slice.call(document.querySelectorAll('.tile'));
  var empty = document.getElementById('dEmpty');
  var body = document.getElementById('dBody');
  if (!tiles.length || !body) { return; }

  var el = function (id) { return document.getElementById(id); };

  function show(tile) {
    tiles.forEach(function (t) { t.classList.toggle('is-on', t === tile); });
    var name = tile.getAttribute('data-name');
    var plans = parseInt(tile.getAttribute('data-plans'), 10) || 0;
    var parcels = parseInt(tile.getAttribute('data-parcels'), 10) || 0;
    var division = tile.getAttribute('data-division');
    var n = notes[division] || { note: '', crops: '' };

    el('dName').textContent = KN ? tile.getAttribute('data-name-kn') : name;
    el('dDiv').textContent = division + (KN ? ' ವಿಭಾಗ' : ' division');
    el('dPilot').hidden = tile.getAttribute('data-pilot') !== '1';

    var p = el('dPlans'), l = el('dParcels');
    p.querySelector('b').textContent = plans;
    l.querySelector('b').textContent = parcels;
    p.href = '/invest?district=' + encodeURIComponent(name);
    l.href = '/land?district=' + encodeURIComponent(name);

    el('dNote').textContent = n.note;
    el('dCrops').textContent = n.crops;
    el('dNone').hidden = !(plans === 0 && parcels === 0);

    empty.hidden = true;
    body.hidden = false;
  }

  tiles.forEach(function (t, i) {
    t.addEventListener('click', function () { show(t); });
    t.addEventListener('keydown', function (e) {
      // arrow keys move to the nearest tile in that direction
      var dx = { ArrowLeft: -1, ArrowRight: 1 }[e.key] || 0;
      var dy = { ArrowUp: -1, ArrowDown: 1 }[e.key] || 0;
      if (!dx && !dy) { return; }
      e.preventDefault();
      var c = parseInt(t.style.gridColumnStart || t.style.gridColumn, 10);
      var r = parseInt(t.style.gridRowStart || t.style.gridRow, 10);
      var best = null, bestD = 1e9;
      tiles.forEach(function (o) {
        if (o === t) { return; }
        var oc = parseInt(o.style.gridColumnStart || o.style.gridColumn, 10);
        var or_ = parseInt(o.style.gridRowStart || o.style.gridRow, 10);
        var vx = oc - c, vy = or_ - r;
        if ((dx && Math.sign(vx) !== dx) || (dy && Math.sign(vy) !== dy)) { return; }
        var d = Math.abs(vx) + Math.abs(vy) + (dx ? Math.abs(vy) : Math.abs(vx)) * 2;
        if (d < bestD) { bestD = d; best = o; }
      });
      if (best) { best.focus(); }
    });
  });

  // open the pilot district by default so the panel is never empty on wide screens
  var pilot = tiles.filter(function (t) { return t.getAttribute('data-pilot') === '1'; })[0];
  if (pilot && window.matchMedia('(min-width: 981px)').matches) { show(pilot); }
})();
