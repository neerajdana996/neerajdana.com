/* Shared: copy-email button. Works without animation libraries. */
(function () {
  var b = document.getElementById('copy-email');
  if (!b) return;
  b.addEventListener('click', function () {
    var t = b.getAttribute('data-copy');
    function done(m) { b.textContent = m; setTimeout(function () { b.textContent = 'Copy'; }, 1800); }
    function sel() {
      var o = document.getElementById('email'), r = document.createRange();
      r.selectNodeContents(o); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); done('Selected');
    }
    try { navigator.clipboard.writeText(t).then(function () { done('Copied'); }, sel); } catch (e) { sel(); }
  });
})();
