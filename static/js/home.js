/* Home page motion: name reveal, counting facts, career line that rises with scroll.
   Content is fully visible without this script; it only adds motion. */
(function () {
  if (typeof gsap === 'undefined' || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  gsap.registerPlugin(ScrollTrigger, MotionPathPlugin, DrawSVGPlugin);

  gsap.timeline({ defaults: { ease: 'power3.out' } })
    .from('.p-hero h1 .ln > span', { yPercent: 105, duration: 0.9, stagger: 0.1 })
    .from('.p-hero .p-status, .p-hero .p-role, .p-hero .lead, .p-hero .btn-row', { y: 14, opacity: 0, duration: 0.6, stagger: 0.08 }, '-=0.5')
    .from('.p-card', { y: 16, opacity: 0, duration: 0.7 }, 0.25)
    .from('.p-net', { drawSVG: '0%', duration: 1.6, ease: 'power2.inOut' }, 0.5);

  document.querySelectorAll('#facts b').forEach(function (b) {
    var o = { v: 0 }, n = +b.dataset.n, s = b.dataset.s || '';
    gsap.to(o, { v: n, duration: 1.2, ease: 'power2.out',
      scrollTrigger: { trigger: '#facts', start: 'top 90%', once: true },
      onUpdate: function () { b.textContent = Math.round(o.v) + s; } });
  });

  gsap.timeline({ scrollTrigger: { trigger: '.p-climb', start: 'top 85%', end: 'bottom 45%', scrub: 0.5 } })
    .fromTo('#climb-path', { drawSVG: '0%' }, { drawSVG: '100%', ease: 'none' })
    .fromTo('#climb-dot', { attr: { cx: 0, cy: 0 } }, { motionPath: { path: '#climb-path', align: '#climb-path', alignOrigin: [0.5, 0.5] }, ease: 'none', immediateRender: false }, 0);
})();
