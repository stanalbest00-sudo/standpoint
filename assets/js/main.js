// Standpoint Seychelles — site behaviours (no dependencies)
(function () {
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── Mobile navigation ──────────────────────────────────────────
  var toggle = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  // ── Reveal on scroll (staggered within each group) ─────────────
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      var batch = entries.filter(function (e) { return e.isIntersecting; });
      batch.forEach(function (e, i) {
        e.target.style.setProperty('--d', Math.min(i * 70, 280) + 'ms');
        e.target.classList.add('is-in');
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  }

  // ── Scroll-driven intro: draws video frames to a canvas ────────
  var intro = document.getElementById('intro');
  if (intro && document.documentElement.classList.contains('motion')) {
    var canvas = intro.querySelector('.intro-canvas');
    var ctx = canvas.getContext('2d');
    var captions = [].slice.call(intro.querySelectorAll('.intro-caption'));
    var FRAMES = 181;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var size = (window.innerWidth * dpr > 1000) ? 'lg' : 'sm';
    var frames = new Array(FRAMES);
    var current = 0, target = 0, lastDrawn = -1, ticking = false;

    function src(i) { return 'assets/frames/' + size + '/f' + String(i + 1).padStart(3, '0') + '.webp'; }

    // Load order: first frame, then a coarse pass (every 8th), then fill in the rest.
    var order = [0], seen = { 0: true };
    [8, 4, 2, 1].forEach(function (step) {
      for (var i = 0; i < FRAMES; i += step) if (!seen[i]) { seen[i] = true; order.push(i); }
    });
    var cursor = 0, inflight = 0;
    function pump() {
      while (inflight < 6 && cursor < order.length) {
        (function (i) {
          var img = new Image();
          img.decoding = 'async';
          inflight++;
          img.onload = function () { frames[i] = img; inflight--; if (i === 0 || Math.abs(i - Math.round(current)) < 8) requestDraw(true); pump(); };
          img.onerror = function () { inflight--; pump(); };
          img.src = src(i);
        })(order[cursor++]);
      }
    }
    pump();

    function nearestLoaded(i) {
      for (var d = 0; d < FRAMES; d++) {
        if (frames[i - d]) return frames[i - d];
        if (frames[i + d]) return frames[i + d];
      }
      return null;
    }

    function resize() {
      canvas.width = Math.round(canvas.clientWidth * dpr);
      canvas.height = Math.round(canvas.clientHeight * dpr);
      lastDrawn = -1;
      requestDraw(true);
    }

    function draw(force) {
      var idx = Math.round(current);
      if (!force && idx === lastDrawn) return;
      var img = nearestLoaded(idx);
      if (!img) return;
      lastDrawn = idx;
      var cw = canvas.width, ch = canvas.height, iw = img.naturalWidth, ih = img.naturalHeight;
      // Cover on wide screens; on tall screens keep the centre ~55% of the frame visible
      // so the logo and its tagline never get cropped.
      var cover = Math.max(cw / iw, ch / ih);
      var scale = Math.min(cover, cw / (iw * 0.5));
      var w = iw * scale, h = ih * scale;
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, cw, ch);
      var x = (cw - w) / 2, y = (ch - h) / 2;
      ctx.drawImage(img, x, y, w, h);
      // When the frame is letterboxed (tall screens), feather its top and bottom into black.
      if (y > 1) {
        var f = h * 0.22, g;
        g = ctx.createLinearGradient(0, y, 0, y + f);
        g.addColorStop(0, '#000'); g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g; ctx.fillRect(0, y - 1, cw, f + 1);
        g = ctx.createLinearGradient(0, y + h - f, 0, y + h);
        g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, '#000');
        ctx.fillStyle = g; ctx.fillRect(0, y + h - f, cw, f + 1);
      }
    }

    function progress() {
      var r = intro.getBoundingClientRect();
      var total = r.height - window.innerHeight;
      return Math.max(0, Math.min(1, -r.top / total));
    }

    function updateCaptions(p) {
      captions.forEach(function (c) {
        var from = +c.dataset.from, to = +c.dataset.to, fade = 0.05;
        var o = 0;
        if (p >= from && p <= to) o = Math.min(1, (p - from) / fade, (to - p) / fade);
        var y = (1 - o) * 10, b = (1 - o) * 6;
        c.style.opacity = o.toFixed(3);
        c.style.transform = 'translateY(' + y.toFixed(1) + 'px)';
        c.style.filter = b > 0.1 ? 'blur(' + b.toFixed(1) + 'px)' : 'none';
      });
      intro.classList.toggle('scrolled', p > 0.02);
    }

    function loop() {
      // Light smoothing so fast flicks still read as motion, not jumps.
      current += (target - current) * 0.22;
      if (Math.abs(target - current) < 0.05) current = target;
      draw(false);
      if (current !== target) requestAnimationFrame(loop); else ticking = false;
    }

    function requestDraw(force) {
      if (force) draw(true);
      if (!ticking) { ticking = true; requestAnimationFrame(loop); }
    }

    function onScroll() {
      var p = progress();
      target = p * (FRAMES - 1);
      updateCaptions(p);
      requestDraw(false);
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', resize);
    resize();
    onScroll();
  }

  // ── Video modal ────────────────────────────────────────────────
  var modal = document.getElementById('video-modal');
  if (modal) {
    var video = modal.querySelector('video');
    var openBtns = document.querySelectorAll('[data-video-open]');
    function close() {
      if (!modal.open) return;
      video.pause();
      if (reduceMotion) { modal.close(); return; }
      modal.classList.add('closing');
      setTimeout(function () { modal.classList.remove('closing'); modal.close(); }, 160);
    }
    openBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        if (typeof modal.showModal !== 'function') { window.location.href = video.querySelector('source').src; return; }
        modal.showModal();
        video.currentTime = 0;
        var p = video.play(); if (p && p.catch) p.catch(function () {});
      });
    });
    modal.querySelector('[data-video-close]').addEventListener('click', close);
    modal.addEventListener('cancel', function (e) { e.preventDefault(); close(); });
    modal.addEventListener('click', function (e) { if (e.target === modal) close(); });
    video.addEventListener('ended', close);
  }

  // ── Quiz ───────────────────────────────────────────────────────
  document.querySelectorAll('.quiz').forEach(function (quiz) {
    var total = quiz.querySelectorAll('.q').length;
    var score = 0, answered = 0;
    var out = quiz.parentElement.querySelector('.score');
    quiz.querySelectorAll('.q').forEach(function (q) {
      var buttons = q.querySelectorAll('button');
      buttons.forEach(function (b) {
        b.addEventListener('click', function () {
          if (q.classList.contains('answered')) return;
          q.classList.add('answered');
          answered++;
          buttons.forEach(function (x) {
            x.disabled = true;
            if (x.hasAttribute('data-correct')) x.classList.add('correct');
          });
          if (b.hasAttribute('data-correct')) score++; else b.classList.add('wrong');
          if (out) out.textContent = 'Score: ' + score + ' / ' + total + (answered === total ? ' — well done for taking part!' : '');
        });
      });
    });
  });

  // ── Contact form: opens the visitor's email app ────────────────
  var form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var to = form.getAttribute('data-email');
      var subject = encodeURIComponent('[Standpoint] ' + form.elements.topic.value + ' — ' + form.elements.name.value);
      var body = encodeURIComponent(form.elements.message.value + '\n\n— ' + form.elements.name.value);
      window.location.href = 'mailto:' + to + '?subject=' + subject + '&body=' + body;
    });
  }
})();
