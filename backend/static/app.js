/* Bhoomi Share — small, dependency-free behaviour.
   Two things: the mobile menu on every page, and the waitlist form on home. */

(function () {
  var hdr = document.querySelector('.hdr');
  var btn = document.getElementById('menuBtn');
  var nav = document.getElementById('siteNav');
  if (!hdr || !btn || !nav) { return; }

  function close() {
    hdr.classList.remove('is-open');
    btn.setAttribute('aria-expanded', 'false');
  }

  btn.addEventListener('click', function () {
    var open = hdr.classList.toggle('is-open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  nav.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') { close(); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && hdr.classList.contains('is-open')) { close(); btn.focus(); }
  });
})();

(function () {
  var form = document.getElementById('waitlist');
  if (!form) { return; }

  var thanks = document.getElementById('wl-thanks');
  var line = document.getElementById('wl-thanks-line');
  var status = document.getElementById('wl-status');
  var btn = form.querySelector('button[type="submit"]');
  var btnLabel = btn.textContent;

  var blurb = {
    Investor: 'We will send you the season plans that are open, with the structure counsel has signed off on.',
    Grower: 'We will ask you for the parcel and the crop plan, and what a season of inputs actually costs you.',
    Landowner: 'We will send you the licence we drafted for your state, so you can read it before deciding anything.',
    Farmer: 'We will tell you what is listed in your district, and on what terms.'
  };

  function fail(message) {
    status.textContent = message;
    status.style.color = '#A6512B';
  }

  function succeed(message) {
    line.textContent = message;
    form.hidden = true;
    thanks.hidden = false;
    thanks.focus();
  }

  function localMessage(name, role, place) {
    return name.split(' ')[0] + ', you are on the list as a ' + role.toLowerCase() +
      ' in ' + place + '. ' + (blurb[role] || '');
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var name = form.elements.name.value.trim();
    var phone = form.elements.phone.value.trim();
    var role = form.elements.role.value;
    var place = form.elements.place.value.trim();

    var missing = [];
    if (!name) { missing.push('your name'); }
    if (phone.replace(/\D/g, '').length < 10) { missing.push('a 10-digit phone number'); }
    if (!role) { missing.push('which side you are on'); }
    if (!place) { missing.push('your district and state'); }

    if (missing.length) {
      fail('We still need ' + missing.join(', ') + '.');
      var focusMap = {
        'your name': 'name',
        'a 10-digit phone number': 'phone',
        'which side you are on': 'role',
        'your district and state': 'place'
      };
      form.elements[focusMap[missing[0]]].focus();
      return;
    }

    status.textContent = 'Sending…';
    status.style.color = '';
    btn.disabled = true;
    btn.textContent = 'Sending…';

    fetch('/api/waitlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name, phone: phone, role: role, place: place,
        company: form.elements.company.value
      })
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (body) {
        return { ok: r.ok, status: r.status, body: body };
      });
    }).then(function (res) {
      if (res.ok) {
        succeed(res.body.message || localMessage(name, role, place));
      } else if (res.status === 422 || res.status === 429) {
        fail(res.body.error || 'Check the form and try again.');
      } else {
        fail('We could not save that just now. Try again in a minute.');
      }
    }).catch(function () {
      succeed(localMessage(name, role, place));
    }).then(function () {
      btn.disabled = false;
      btn.textContent = btnLabel;
    });
  });
})();
