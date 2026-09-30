/* Karnataka farming map.
   A real map (Leaflet + OpenStreetMap tiles) with district outlines, four layers,
   and a panel that shows what grows in a district, which model fits, and what is
   open. The diagram below the map (keyboard friendly) drives the same panel.
   If Leaflet or the tiles fail, the outlines still draw and the diagram works. */
(function () {
  'use strict';

  var CFG = window.BHOOMI_MAP || {};
  var KN = (document.documentElement.lang || 'en').slice(0, 2) === 'kn';
  var D = {};                                   // by district name
  (CFG.districts || []).forEach(function (d) { D[d.name] = d; });
  var el = function (id) { return document.getElementById(id); };

  /* ---- palette (read from the page's own tokens so a theme change carries over) */
  var css = getComputedStyle(document.documentElement);
  function tok(n, fb) { return (css.getPropertyValue(n) || '').trim() || fb; }
  var BURG = tok('--burgundy', '#9C1536'), BURG_HI = tok('--burgundy-hi', '#BE1E47');
  var GOLD = tok('--gold-soft', '#E0A92E'), LEAF = tok('--leaf', '#3F7A45');
  var SLATE = '#6B5A5C', ROSE = '#D4708A';

  var TIER_FILL = { 3: BURG, 2: '#C9657D', 1: '#EBD3D8' };
  var FIT_FILL = { 'crop-plans': BURG, 'livestock': GOLD, 'small-spaces': LEAF, 'land-shares': SLATE, 'land-lease': ROSE };
  var FIT_NAME = { 'crop-plans': 'Crop plans', 'livestock': 'Livestock', 'small-spaces': 'Small spaces', 'land-shares': 'Land shares', 'land-lease': 'Leases' };
  var DIV_FILL = { Belagavi: BURG, Bengaluru: GOLD, Kalaburagi: SLATE, Mysuru: LEAF };

  var T = {
    division: KN ? ' ವಿಭಾಗ' : ' division',
    tier: { 3: KN ? 'ಪ್ರಮುಖ ಬೆಳೆ ಪಟ್ಟಿ' : 'Major cropland belt', 2: KN ? 'ಮಿಶ್ರ ಕೃಷಿ ಮತ್ತು ತೋಟ' : 'Mixed farming and plantations', 1: KN ? 'ಕರಾವಳಿ, ಕಾಡು ಅಥವಾ ನಗರ' : 'Coast, forest or city' },
    live0: KN ? 'ಏನೂ ತೆರೆದಿಲ್ಲ' : 'Nothing open yet',
    liveN: KN ? 'ತೆರೆದಿರುವುದು ಇದೆ' : 'Something is open',
    pilot: KN ? 'ನಮ್ಮ ಪೈಲಟ್' : 'Our pilot',
    shared: KN ? 'ಈ ಗಡಿಯಲ್ಲಿ ಇವೆರಡೂ ಇವೆ:' : 'This outline covers both:',
    order: KN ? 'ಮೊದಲ ಆಯ್ಕೆ' : 'first choice'
  };

  var current = null;

  /* ---- the panel ---------------------------------------------------------- */
  function show(name) {
    var d = D[name];
    if (!d) { return; }
    current = name;
    el('dEmpty').hidden = true;
    el('dBody').hidden = false;

    el('dName').textContent = KN ? d.name_kn : d.name;
    el('dDiv').textContent = d.division + T.division;
    el('dTier').textContent = T.tier[d.tier] || d.tier_label;
    el('dPilot').hidden = !d.pilot;
    el('dCrops').textContent = d.crops;
    el('dWhy').textContent = d.why;

    var fit = el('dFit');
    fit.innerHTML = '';
    d.fit.forEach(function (f, i) {
      var a = document.createElement('a');
      a.href = '/models/' + f.slug;
      a.className = 'fitchip' + (i === 0 ? ' fitchip--first' : '');
      a.innerHTML = '<i style="background:' + (FIT_FILL[f.slug] || BURG) + '"></i>' + f.label + (i === 0 ? '<small>' + T.order + '</small>' : '');
      fit.appendChild(a);
    });

    var p = el('dPlans'), l = el('dParcels');
    p.querySelector('b').textContent = d.plans;
    l.querySelector('b').textContent = d.parcels;
    p.href = '/invest?district=' + encodeURIComponent(d.name);
    l.href = '/land?district=' + encodeURIComponent(d.name);
    el('dNone').hidden = !(d.plans === 0 && d.parcels === 0);

    // Ballari and Vijayanagara share one outline
    var share = el('dShare');
    var group = (sharedGroups[name] || null);
    if (group) {
      share.hidden = false;
      share.innerHTML = T.shared + ' ';
      group.forEach(function (n) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'sharechip' + (n === name ? ' is-on' : '');
        b.textContent = KN ? D[n].name_kn : n;
        b.addEventListener('click', function () { show(n); });
        share.appendChild(b);
      });
    } else { share.hidden = true; }

    document.querySelectorAll('.tile').forEach(function (t) { t.classList.toggle('is-on', t.getAttribute('data-name') === name); });
    restyle();
  }

  /* ---- map ---------------------------------------------------------------- */
  var sharedGroups = {};
  var layerName = 'tier';
  var geo = null, map = null, labels = [], pilotMarker = null;

  function fillFor(names) {
    // a shared outline uses its first district for colour
    var d = D[names[0]];
    if (!d) { return '#eee'; }
    if (layerName === 'tier') { return TIER_FILL[d.tier]; }
    if (layerName === 'fit') { return FIT_FILL[d.fit[0].slug] || BURG; }
    if (layerName === 'division') { return DIV_FILL[d.division] || BURG; }
    var n = names.reduce(function (s, x) { return s + D[x].plans + D[x].parcels; }, 0);
    return n ? BURG : '#F3E7E9';
  }
  function opacityFor(names) {
    if (layerName !== 'live') { return layerName === 'tier' ? 0.82 : 0.78; }
    var n = names.reduce(function (s, x) { return s + D[x].plans + D[x].parcels; }, 0);
    return n ? Math.min(0.35 + n * 0.12, 0.92) : 0.55;
  }

  function styleFor(feature) {
    var names = feature.properties.districts;
    var on = current && names.indexOf(current) !== -1;
    return {
      fillColor: fillFor(names),
      fillOpacity: opacityFor(names),
      color: on ? '#2B1619' : '#ffffff',
      weight: on ? 2.6 : 1.1,
      opacity: 1
    };
  }

  function restyle() {
    if (geo) { geo.setStyle(styleFor); geo.eachLayer(function (l) { if (current && l.feature.properties.districts.indexOf(current) !== -1) { l.bringToFront(); } }); }
    legend();
  }

  function legend() {
    var ul = el('legend'); if (!ul) { return; }
    var rows = [];
    if (layerName === 'tier') {
      [3, 2, 1].forEach(function (t) { rows.push([TIER_FILL[t], T.tier[t]]); });
    } else if (layerName === 'fit') {
      Object.keys(FIT_FILL).forEach(function (k) { rows.push([FIT_FILL[k], FIT_NAME[k]]); });
      rows.push([null, KN ? 'ಪ್ರತಿ ಜಿಲ್ಲೆಯ ಮೊದಲ ಆಯ್ಕೆಯ ಬಣ್ಣ' : 'colour shows each district’s first-choice model']);
    } else if (layerName === 'live') {
      rows.push(['#F3E7E9', T.live0]); rows.push([BURG, T.liveN]);
    } else {
      Object.keys(DIV_FILL).forEach(function (k) { rows.push([DIV_FILL[k], k + T.division]); });
    }
    rows.push(['pilot', T.pilot]);
    ul.innerHTML = rows.map(function (r) {
      if (r[0] === 'pilot') { return '<li><i class="sw-pilot"></i>' + r[1] + '</li>'; }
      if (r[0] === null) { return '<li class="legend__note">' + r[1] + '</li>'; }
      return '<li><i style="background:' + r[0] + '"></i>' + r[1] + '</li>';
    }).join('');
  }

  function centroid(feature) {
    // centre of the largest ring's bounding box: good enough for a label
    var best = null, area = -1;
    feature.geometry.coordinates.forEach(function (poly) {
      var ring = poly[0], minx = 1e9, miny = 1e9, maxx = -1e9, maxy = -1e9;
      ring.forEach(function (c) { minx = Math.min(minx, c[0]); maxx = Math.max(maxx, c[0]); miny = Math.min(miny, c[1]); maxy = Math.max(maxy, c[1]); });
      var a = (maxx - minx) * (maxy - miny);
      if (a > area) { area = a; best = [(miny + maxy) / 2, (minx + maxx) / 2]; }
    });
    return best;
  }

  function buildMap(gj) {
    var node = el('kmap');
    if (!node || typeof L === 'undefined') { return; }

    map = L.map(node, {
      zoomSnap: 0.25, minZoom: 6, maxZoom: 11, scrollWheelZoom: false, attributionControl: true
    });
    if (CFG.tileUrl) {
      L.tileLayer(CFG.tileUrl, { attribution: CFG.attribution || '', maxZoom: 11, opacity: 0.55 }).addTo(map);
    }
    map.attributionControl.addAttribution('Boundaries: <a href="https://github.com/datameet/maps">DataMeet</a>, Census 2011');

    geo = L.geoJSON(gj, {
      style: styleFor,
      onEachFeature: function (f, layer) {
        var names = f.properties.districts;
        if (names.length > 1) { names.forEach(function (n) { sharedGroups[n] = names; }); }
        var label = names.map(function (n) { return KN ? D[n].name_kn : n; }).join(' / ');
        layer.on({
          click: function () { map.scrollWheelZoom.enable(); show(names[0]); },
          mouseover: function () { if (!(current && names.indexOf(current) !== -1)) { layer.setStyle({ weight: 2.2, color: '#2B1619' }); layer.bringToFront(); } },
          mouseout: function () { geo.resetStyle(layer); layer.setStyle(styleFor(f)); }
        });
        layer.bindTooltip(label, { sticky: true, direction: 'top', className: 'dtip' });
        var c = centroid(f);
        if (c) {
          var t = L.tooltip({ permanent: true, direction: 'center', className: 'dlabel', interactive: false }).setContent(label).setLatLng(c);
          labels.push(t);
        }
      }
    }).addTo(map);

    map.fitBounds(geo.getBounds(), { padding: [10, 10] });
    map.setMaxBounds(geo.getBounds().pad(0.35));

    // pilot marker on Belagavi
    var pilot = (CFG.districts || []).filter(function (d) { return d.pilot; })[0];
    if (pilot) {
      geo.eachLayer(function (l) {
        if (l.feature.properties.districts.indexOf(pilot.name) !== -1) {
          var c = centroid(l.feature);
          pilotMarker = L.marker(c, {
            interactive: false, keyboard: false,
            icon: L.divIcon({ className: 'pilotpin', html: '<span></span>', iconSize: [18, 18] })
          }).addTo(map);
        }
      });
    }

    function syncLabels() {
      var on = map.getZoom() >= 6.3;
      labels.forEach(function (t) { if (on) { t.addTo(map); } else { map.removeLayer(t); } });
    }
    map.on('zoomend', syncLabels); syncLabels();

    // give the map a nudge once it is laid out (fonts and cards settle late)
    window.setTimeout(function () { map.invalidateSize(); map.fitBounds(geo.getBounds(), { padding: [10, 10] }); }, 250);

    // open the pilot district on wide screens so the panel is never empty
    if (pilot && window.matchMedia('(min-width: 981px)').matches) { show(pilot.name); }
    legend();
  }

  /* ---- layer switch ------------------------------------------------------- */
  document.querySelectorAll('.layer').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.layer').forEach(function (x) { x.classList.remove('is-on'); x.setAttribute('aria-checked', 'false'); });
      b.classList.add('is-on'); b.setAttribute('aria-checked', 'true');
      layerName = b.getAttribute('data-layer');
      restyle();
    });
  });

  /* ---- the keyboard-friendly diagram drives the same panel ---------------- */
  var tiles = Array.prototype.slice.call(document.querySelectorAll('.tile'));
  tiles.forEach(function (t) {
    t.addEventListener('click', function () { show(t.getAttribute('data-name')); var p = el('dpanel'); if (p && window.matchMedia('(max-width: 980px)').matches) { p.scrollIntoView({ behavior: 'smooth', block: 'start' }); } });
    t.addEventListener('keydown', function (e) {
      var dx = { ArrowLeft: -1, ArrowRight: 1 }[e.key] || 0, dy = { ArrowUp: -1, ArrowDown: 1 }[e.key] || 0;
      if (!dx && !dy) { return; }
      e.preventDefault();
      var c = parseInt(t.style.gridColumnStart || t.style.gridColumn, 10), r = parseInt(t.style.gridRowStart || t.style.gridRow, 10);
      var best = null, bestD = 1e9;
      tiles.forEach(function (o) {
        if (o === t) { return; }
        var oc = parseInt(o.style.gridColumnStart || o.style.gridColumn, 10), or_ = parseInt(o.style.gridRowStart || o.style.gridRow, 10);
        var vx = oc - c, vy = or_ - r;
        if ((dx && Math.sign(vx) !== dx) || (dy && Math.sign(vy) !== dy)) { return; }
        var dist = Math.abs(vx) + Math.abs(vy) + (dx ? Math.abs(vy) : Math.abs(vx)) * 2;
        if (dist < bestD) { bestD = dist; best = o; }
      });
      if (best) { best.focus(); }
    });
  });

  /* ---- go ----------------------------------------------------------------- */
  if (typeof L === 'undefined') {
    // no map library: show the diagram instead, and open the pilot
    var alt = el('altview'); if (alt) { alt.open = true; }
    var mapEl = el('kmap'); if (mapEl) { mapEl.innerHTML = '<p class="mapfail">The map could not load. The district diagram below works the same way.</p>'; }
    var pd = (CFG.districts || []).filter(function (d) { return d.pilot; })[0]; if (pd) { show(pd.name); }
    return;
  }
  fetch(CFG.geojson).then(function (r) { return r.json(); }).then(buildMap).catch(function () {
    var mapEl = el('kmap'); if (mapEl) { mapEl.innerHTML = '<p class="mapfail">The map data could not load. Use the district diagram below.</p>'; }
    var alt = el('altview'); if (alt) { alt.open = true; }
  });
})();
