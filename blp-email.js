/* BetLegend email signup (Oct 1 2026). Posts to the TrustMyRecord Brevo
   double opt in endpoint; the confirmation email completes the signup.
   Markup comes from scripts/email_signup.py. GA4 events via window.blpTrack
   (blp-events.js): email_signup_view, email_signup_submit, email_signup_pending,
   email_signup_error. */
(function () {
  var API = 'https://trustmyrecord-api.onrender.com/api/email/subscribe';
  function track(name, params) {
    try { if (typeof window.blpTrack === 'function') window.blpTrack(name, params); } catch (e) {}
  }
  function utm() {
    var out = {};
    try {
      var q = new URLSearchParams(window.location.search);
      ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function (k) {
        if (q.get(k)) out[k] = q.get(k).slice(0, 100);
      });
    } catch (e) {}
    return out;
  }
  function init(box) {
    if (box.getAttribute('data-ready')) return;
    box.setAttribute('data-ready', '1');
    var form = box.querySelector('form');
    var msg = box.querySelector('.blp-email-msg');
    var btn = form.querySelector('button[type="submit"]');
    var base = { source: box.getAttribute('data-source') || 'betlegendpicks',
      page_type: box.getAttribute('data-page-type') || '', sport: box.getAttribute('data-sport') || '' };
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (en) {
        if (en[0].isIntersecting) { track('email_signup_view', base); io.disconnect(); }
      }, { threshold: 0.5 });
      io.observe(box);
    }
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var email = (form.email.value || '').trim();
      var lists = [].slice.call(form.querySelectorAll('input[name="list"]:checked')).map(function (i) { return i.value; });
      msg.className = 'blp-email-msg';
      if (!lists.length) { msg.textContent = 'Pick at least one email to receive.'; msg.className += ' err'; return; }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { msg.textContent = 'Enter a valid email address.'; msg.className += ' err'; return; }
      var body = Object.assign({ email: email, lists: lists, source: base.source, page: window.location.pathname,
        sport: base.sport, website: form.website ? form.website.value : '' }, utm());
      track('email_signup_submit', Object.assign({ lists: lists.join(',') }, base));
      btn.disabled = true; btn.textContent = 'Sending...';
      fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok, status: r.status, d: d }; }); })
        .then(function (res) {
          if (res.ok && res.d && res.d.ok) {
            form.style.display = 'none';
            msg.textContent = res.d.message || 'Check your inbox and click the confirmation link to finish signing up.';
            msg.className += ' ok';
            track('email_signup_pending', Object.assign({ lists: lists.join(',') }, base));
          } else {
            msg.textContent = (res.d && res.d.message) || (res.status === 429 ? 'Too many attempts. Try again in a few minutes.' : 'Something went wrong. Please try again.');
            msg.className += ' err';
            track('email_signup_error', Object.assign({ error: (res.d && res.d.error) || String(res.status) }, base));
          }
        })
        .catch(function () {
          msg.textContent = 'Could not reach the server. Please try again.';
          msg.className += ' err';
          track('email_signup_error', Object.assign({ error: 'network' }, base));
        })
        .then(function () { btn.disabled = false; btn.textContent = 'Sign me up'; });
    });
  }
  function run() { [].forEach.call(document.querySelectorAll('.blp-email'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
