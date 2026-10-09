/* Kafka article: interactive duplicate-processing lab. No dependencies. */
(function () {
  var box = document.getElementById('lab-box'); if (!box) return;
  var $ = function (id) { return document.getElementById(id); }, st;
  var anim = typeof gsap !== 'undefined' && !matchMedia('(prefers-reduced-motion: reduce)').matches;
  function reset() { st = { off: 0, next: 1, charged: {}, pending: null, dup: 0 }; $('l-charges').innerHTML = ''; render('Process a few orders, then deploy or crash between the charge and the commit.'); }
  function chip(t, c) { var e = document.createElement('span'); e.className = 'chip' + (c ? ' ' + c : ''); e.textContent = t; $('l-charges').appendChild(e); if (anim) gsap.from(e, { y: -8, opacity: 0, duration: 0.3 }); }
  function render(m) { $('l-off').textContent = st.off; $('l-ord').textContent = st.next - 1; $('l-dup').textContent = st.dup; $('l-dup').style.color = st.dup ? 'var(--warn)' : ''; $('l-msg').textContent = m; }
  function charge(id) {
    var key = $('lab-key').checked;
    if (st.charged[id] && key) { chip('#' + id + ' skipped', 'skip'); return 'skip'; }
    if (st.charged[id]) { st.dup++; chip('#' + id + ' charged again', 'dup'); return 'dup'; }
    st.charged[id] = 1; chip('#' + id + ' charged'); return 'ok';
  }
  function act(a) {
    if (a === 'reset') return reset();
    if (a === 'next') {
      if (st.pending) { var r = charge(st.pending); st.off = st.pending - 7730; st.pending = null;
        return render(r === 'dup' ? 'The replayed order was charged a second time. That is a duplicate.' : r === 'skip' ? 'The key recognised the replay and skipped it. Offset committed.' : 'Charged and committed.'); }
      var id = 7730 + st.next; st.next++; charge(id); st.off = st.next - 1; return render('Order #' + id + ' charged, offset committed.');
    }
    if (st.pending) return render('A replay is waiting. Press "Process next order" to let the next consumer handle it.');
    var id2 = 7730 + st.next; st.next++; charge(id2); st.pending = id2;
    render((a === 'deploy' ? 'Deploy: the partition moved' : 'Crash') + ' after charging #' + id2 + ', before the commit. Press "Process next order" to see what the next consumer does.');
  }
  box.querySelectorAll('[data-act]').forEach(function (b) { b.addEventListener('click', function () { act(b.dataset.act); }); });
  reset();
})();
