/* FAQ search: hides questions that do not contain every word typed. Native
   <details> does the opening and closing, so the page works without this. */
(function () {
  'use strict';
  var q = document.getElementById('faqQ');
  if (!q) { return; }
  var items = Array.prototype.slice.call(document.querySelectorAll('.faq details'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.faqgroup'));
  var none = document.getElementById('faqNone');

  function run() {
    var words = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    var shown = 0;
    items.forEach(function (d) {
      var text = d.getAttribute('data-text') || '';
      var ok = words.every(function (w) { return text.indexOf(w) !== -1; });
      d.hidden = !ok;
      if (ok) { shown++; }
      if (words.length && ok) { d.open = true; } else if (!words.length) { d.open = false; }
    });
    groups.forEach(function (g) {
      g.hidden = !g.querySelector('details:not([hidden])');
    });
    if (none) { none.hidden = shown !== 0; }
  }
  q.addEventListener('input', run);
})();
