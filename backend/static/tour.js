/* First-run guided tour.

   A dimmed overlay with a cut-out around one thing at a time, and a card
   explaining it. Steps come from the server as JSON, already in the reader's
   language. When a step's target is missing or hidden — the nav links are
   hidden on a phone — the card centres itself and the cut-out is skipped, so
   the words are never lost, only the pointing. */

(function () {
  var data = document.getElementById('tour-data');
  if (!data) { return; }

  var tour;
  try {
    tour = JSON.parse(data.textContent);
  } catch (e) {
    return;
  }
  if (!tour.steps || !tour.steps.length) { return; }

  var index = 0;
  var PAD = 8;

  var root = document.createElement('div');
  root.className = 'tour';
  root.setAttribute('role', 'dialog');
  root.setAttribute('aria-modal', 'true');
  root.setAttribute('aria-label', tour.labels.title);
  root.innerHTML =
    '<div class="tour__hole" hidden></div>' +
    '<div class="tour__veil"></div>' +
    '<div class="tour__card" tabindex="-1">' +
      '<p class="tour__count"></p>' +
      '<h2 class="tour__title"></h2>' +
      '<p class="tour__body"></p>' +
      '<div class="tour__row">' +
        '<button type="button" class="btn btn--ghost btn--small tour__skip"></button>' +
        '<span class="tour__spacer"></span>' +
        '<button type="button" class="btn btn--line btn--small tour__back"></button>' +
        '<button type="button" class="btn btn--solid btn--small tour__next"></button>' +
      '</div>' +
    '</div>';
  document.body.appendChild(root);

  var hole = root.querySelector('.tour__hole');
  var card = root.querySelector('.tour__card');
  var elCount = root.querySelector('.tour__count');
  var elTitle = root.querySelector('.tour__title');
  var elBody = root.querySelector('.tour__body');
  var btnBack = root.querySelector('.tour__back');
  var btnNext = root.querySelector('.tour__next');
  var btnSkip = root.querySelector('.tour__skip');

  btnSkip.textContent = tour.labels.skip;
  btnBack.textContent = tour.labels.back;

  function place(target) {
    if (!target) {
      hole.hidden = true;
      card.classList.add('tour__card--mid');
      card.style.top = '';
      card.style.left = '';
      return;
    }

    var r = target.getBoundingClientRect();
    hole.hidden = false;
    hole.style.top = (r.top - PAD) + 'px';
    hole.style.left = (r.left - PAD) + 'px';
    hole.style.width = (r.width + PAD * 2) + 'px';
    hole.style.height = (r.height + PAD * 2) + 'px';

    card.classList.remove('tour__card--mid');
    card.style.top = '';
    card.style.left = '';

    var cr = card.getBoundingClientRect();
    var gap = 14;
    var below = r.bottom + gap;
    var top = (below + cr.height < window.innerHeight) ? below
            : Math.max(gap, r.top - cr.height - gap);
    var left = Math.min(
      Math.max(gap, r.left),
      Math.max(gap, window.innerWidth - cr.width - gap)
    );
    card.style.top = top + 'px';
    card.style.left = left + 'px';
  }

  function visible(el) {
    if (!el) { return false; }
    var r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && !!el.offsetParent;
  }

  function show() {
    var step = tour.steps[index];
    var target = step.target ? document.querySelector(step.target) : null;
    if (!visible(target)) { target = null; }

    elCount.textContent = (index + 1) + ' ' + tour.labels.of + ' ' + tour.steps.length;
    elTitle.textContent = step.title;
    elBody.textContent = step.body;
    btnNext.textContent = (index === tour.steps.length - 1) ? tour.labels.done : tour.labels.next;
    btnBack.hidden = index === 0;

    if (target) {
      var r = target.getBoundingClientRect();
      if (r.top < 60 || r.bottom > window.innerHeight - 60) {
        target.scrollIntoView({ block: 'center', behavior: 'auto' });
      }
    }
    place(target);
    card.focus();
  }

  function finish() {
    root.remove();
    window.removeEventListener('resize', onMove);
    window.removeEventListener('scroll', onMove, true);
    document.removeEventListener('keydown', onKey);

    fetch('/dashboard/tour/done', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }).catch(function () { /* worst case it shows once more */ });
  }

  function onMove() {
    var step = tour.steps[index];
    var target = step.target ? document.querySelector(step.target) : null;
    place(visible(target) ? target : null);
  }

  function onKey(e) {
    if (e.key === 'Escape') { finish(); }
    else if (e.key === 'ArrowRight') { btnNext.click(); }
    else if (e.key === 'ArrowLeft' && index > 0) { btnBack.click(); }
  }

  btnNext.addEventListener('click', function () {
    if (index === tour.steps.length - 1) { finish(); return; }
    index += 1;
    show();
  });
  btnBack.addEventListener('click', function () {
    if (index > 0) { index -= 1; show(); }
  });
  btnSkip.addEventListener('click', finish);
  root.querySelector('.tour__veil').addEventListener('click', finish);

  window.addEventListener('resize', onMove);
  window.addEventListener('scroll', onMove, true);
  document.addEventListener('keydown', onKey);

  show();
})();
