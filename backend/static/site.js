/* Bhoomi Share — shared behaviour for the v2 pages.
   Dependency-free. Every effect is progressive: with JS off, or with
   prefers-reduced-motion, the page is fully visible and fully usable. */

(function () {
  'use strict';

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* header gains a solid background once the page has scrolled */
  var hdr = document.querySelector('.hdr');
  if (hdr) {
    var onScroll = function () { hdr.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* reveal-on-scroll */
  var rv = document.querySelectorAll('.rv');
  if (rv.length) {
    if (reduce || !('IntersectionObserver' in window)) {
      rv.forEach(function (el) { el.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
      rv.forEach(function (el) { io.observe(el); });
      // failsafe: if the observer never fires (throttled tab, script error),
      // nothing stays hidden
      window.setTimeout(function () { rv.forEach(function (el) { el.classList.add('in'); }); }, 4000);
    }
  }

  /* count-up numbers: <span data-count="1240" data-prefix="₹">  */
  function format(n) {
    // Indian digit grouping, matching the server's inr() helper
    var s = String(Math.round(n));
    if (s.length <= 3) { return s; }
    var tail = s.slice(-3), head = s.slice(0, -3), parts = [];
    while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2); }
    if (head) { parts.unshift(head); }
    return parts.join(',') + ',' + tail;
  }
  var counters = document.querySelectorAll('[data-count]');
  counters.forEach(function (el) {
    var target = parseFloat(el.getAttribute('data-count')) || 0;
    var prefix = el.getAttribute('data-prefix') || '';
    var suffix = el.getAttribute('data-suffix') || '';
    var plain = el.hasAttribute('data-plain');
    var show = function (v) { el.textContent = prefix + (plain ? String(Math.round(v)) : format(v)) + suffix; };
    if (reduce || !('IntersectionObserver' in window)) { show(target); return; }
    show(0);
    var obs = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) { return; }
      obs.disconnect();
      var start = null, dur = 1400;
      (function step(ts) {
        if (start === null) { start = ts; }
        var t = Math.min((ts - start) / dur, 1);
        show(target * (1 - Math.pow(1 - t, 3)));
        if (t < 1) { requestAnimationFrame(step); }
      })(performance.now());
    }, { threshold: 0.4 });
    obs.observe(el);
  });

  /* dropdowns: Escape closes, and focus leaving the group closes it */
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') { return; }
    var active = document.activeElement;
    if (active && active.closest && active.closest('.nav__group')) { active.blur(); }
  });
})();

/* sidebar menu: open from the button, close from the X, the veil, Escape, or any link */
(function () {
  var btn = document.getElementById('menuBtn');
  var drawer = document.getElementById('drawer');
  var veil = document.getElementById('drawerVeil');
  var closeBtn = document.getElementById('drawerClose');
  if (!btn || !drawer || !veil) { return; }

  var lastFocus = null;

  function open() {
    lastFocus = document.activeElement;
    veil.hidden = false;
    document.body.classList.add('drawer-open');
    drawer.setAttribute('aria-hidden', 'false');
    btn.setAttribute('aria-expanded', 'true');
    var first = drawer.querySelector('a.dl');
    if (first) { window.setTimeout(function () { first.focus({ preventScroll: true }); }, 60); }
  }
  function close() {
    document.body.classList.remove('drawer-open');
    drawer.setAttribute('aria-hidden', 'true');
    btn.setAttribute('aria-expanded', 'false');
    window.setTimeout(function () { if (!document.body.classList.contains('drawer-open')) { veil.hidden = true; } }, 320);
    if (lastFocus && lastFocus.focus) { lastFocus.focus({ preventScroll: true }); }
  }

  btn.addEventListener('click', function () {
    document.body.classList.contains('drawer-open') ? close() : open();
  });
  if (closeBtn) { closeBtn.addEventListener('click', close); }
  veil.addEventListener('click', close);
  drawer.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a');
    if (a) { document.body.classList.remove('drawer-open'); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && document.body.classList.contains('drawer-open')) { close(); }
    // keep Tab inside the open drawer
    if (e.key === 'Tab' && document.body.classList.contains('drawer-open')) {
      var f = drawer.querySelectorAll('a[href],button:not([disabled])');
      if (!f.length) { return; }
      var firstEl = f[0], lastEl = f[f.length - 1];
      if (e.shiftKey && document.activeElement === firstEl) { e.preventDefault(); lastEl.focus(); }
      else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); firstEl.focus(); }
    }
  });
})();
