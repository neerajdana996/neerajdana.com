/* AI evaluation page: illustrative verifier run. Works without GSAP; GSAP only adds the pop. */
(function () {
  var rows = document.getElementById('g-rows'); if (!rows) return;
  var anim = typeof gsap !== 'undefined' && !matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fixes = [
    ['Add a sleep before commit', 'Narrows the window, doesn’t close it', 16],
    ['Raise session timeouts', 'Fewer rebalances, same bug', 14],
    ['Commit before charging', 'No duplicates, but loses orders', 0],
    ['Dedupe in memory', 'Forgets everything on restart', 11],
    ['Idempotency key in the same transaction', 'The real fix', 20]
  ];
  fixes.forEach(function (f, i) {
    var row = document.createElement('div'); row.className = 'g-row';
    row.innerHTML = '<div class="g-name">' + f[0] + '<small>' + f[1] + '</small></div><div class="seeds" aria-hidden="true">' +
      new Array(21).join('<i></i>') + '</div><div class="verdict" aria-live="polite"></div>';
    rows.appendChild(row);
    var s = 31 + i * 7, order = []; for (var k = 0; k < 20; k++) order.push(k);
    order.sort(function () { s = (s * 48271) % 2147483647; return s / 2147483647 - 0.5; });
    row._pass = {}; order.slice(0, f[2]).forEach(function (k) { row._pass[k] = 1; }); row._n = f[2];
  });
  function run() {
    Array.prototype.forEach.call(rows.children, function (row, ri) {
      var dots = row.querySelectorAll('.seeds i'), v = row.querySelector('.verdict');
      Array.prototype.forEach.call(dots, function (d) { d.className = ''; }); v.textContent = '';
      function done() { var ok = row._n === 20; v.className = 'verdict ' + (ok ? 'pass' : 'fail'); v.textContent = (ok ? 'PASS ' : 'FAIL ') + row._n + '/20'; }
      if (!anim) { Array.prototype.forEach.call(dots, function (d, k) { d.className = row._pass[k] ? 'p' : 'f'; }); return done(); }
      Array.prototype.forEach.call(dots, function (d, k) {
        gsap.delayedCall(ri * 0.25 + k * 0.06, function () { d.className = row._pass[k] ? 'p' : 'f'; gsap.fromTo(d, { scale: 0.3 }, { scale: 1, duration: 0.25, ease: 'back.out(3)' }); });
      });
      gsap.delayedCall(ri * 0.25 + 1.3, done);
    });
  }
  document.getElementById('g-run').addEventListener('click', run);
  if (anim && typeof ScrollTrigger !== 'undefined') { gsap.registerPlugin(ScrollTrigger); ScrollTrigger.create({ trigger: '#gauntlet', start: 'top 75%', once: true, onEnter: run }); }
  else run();
})();
