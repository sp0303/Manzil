// Design gallery: room filters + lightbox (projects.html)
(function () {
  var grid = document.querySelector('.gallery-grid');
  if (!grid) return;
  var items = Array.prototype.slice.call(grid.querySelectorAll('.gallery-item'));
  var buttons = document.querySelectorAll('.gallery-filter');

  buttons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var f = btn.getAttribute('data-filter');
      buttons.forEach(function (b) {
        b.classList.toggle('active', b === btn);
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
      items.forEach(function (it) {
        it.classList.toggle('is-hidden', f !== 'all' && it.getAttribute('data-category') !== f);
      });
    });
  });

  var lb = document.getElementById('galleryLightbox');
  var lbImg = lb.querySelector('img');
  var lbCap = lb.querySelector('.lb-caption');
  var current = [], index = 0, lastFocus = null;

  function show(i) {
    index = (i + current.length) % current.length;
    var a = current[index], img = a.querySelector('img');
    lbImg.src = a.getAttribute('href');
    lbImg.alt = img.alt;
    lbCap.textContent = img.alt + ' (' + (index + 1) + ' / ' + current.length + ')';
  }
  function open(a) {
    current = items.filter(function (it) { return !it.classList.contains('is-hidden'); });
    lastFocus = a;
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    show(current.indexOf(a));
    lb.querySelector('.lb-close').focus();
  }
  function close() {
    lb.hidden = true;
    lbImg.src = '';
    document.body.style.overflow = '';
    if (lastFocus) lastFocus.focus();
  }

  items.forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); open(a); });
  });
  lb.querySelector('.lb-close').addEventListener('click', close);
  lb.querySelector('.lb-prev').addEventListener('click', function () { show(index - 1); });
  lb.querySelector('.lb-next').addEventListener('click', function () { show(index + 1); });
  lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
  document.addEventListener('keydown', function (e) {
    if (lb.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(index - 1);
    else if (e.key === 'ArrowRight') show(index + 1);
  });

  // Swipe on touch devices
  var x0 = null;
  lb.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
    x0 = null;
  });
})();
