/* BetLegendPicks conversion events (Oct 1 2026).
   Sends GA4 events through the page's existing gtag (G-QS8L5TDNLY). Safe when gtag
   is missing or blocked: events are pushed to dataLayer and nothing else happens.

   pro_cta_click      any element with data-pro-cta (the contextual Pro module)
                      params: page_type, sport, source_url, cta_variant, destination
   email_signup_view  an email form scrolled into view      (form[data-email-form])
   email_signup_submit / email_signup_success / email_signup_error
                      params: signup_source, list, page_type, sport, source_url
   Links to the Pro checkout also carry utm_source=betlegendpicks so TrustMyRecord's
   GA4 sees the arrival, checkout starts and purchases with the same campaign tags. */
(function () {
  'use strict';
  if (window.blpTrack) return; // the Pro and email modules both include this file
  window.dataLayer = window.dataLayer || [];
  function send(name, params) {
    params = params || {};
    params.source_url = params.source_url || location.pathname;
    try {
      if (typeof window.gtag === 'function') {
        window.gtag('event', name, Object.assign({ transport_type: 'beacon' }, params));
      } else {
        window.dataLayer.push(Object.assign({ event: name }, params));
      }
    } catch (e) { /* analytics must never break the page */ }
  }
  window.blpTrack = send;

  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('[data-pro-cta]') : null;
    if (!a) return;
    send('pro_cta_click', {
      page_type: a.getAttribute('data-page-type') || '',
      sport: a.getAttribute('data-sport') || '',
      cta_variant: a.getAttribute('data-pro-cta') || '',
      destination: (a.href || '').split('?')[0]
    });
  }, true);

  if ('IntersectionObserver' in window) {
    var seen = false;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting || seen) return;
        seen = true;
        var f = en.target;
        send('email_signup_view', {
          signup_source: f.getAttribute('data-source') || '',
          list: f.getAttribute('data-list') || '',
          page_type: f.getAttribute('data-page-type') || '',
          sport: f.getAttribute('data-sport') || ''
        });
        io.disconnect();
      });
    }, { threshold: 0.5 });
    document.addEventListener('DOMContentLoaded', function () {
      var f = document.querySelector('form[data-email-form]');
      if (f) io.observe(f);
    });
  }
})();
