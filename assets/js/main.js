// Standpoint Seychelles — site behaviours (no dependencies)
(function () {
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── Mobile navigation ──────────────────────────────────────────
  var toggle = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');
  if (toggle && links) {
    function setMenu(open) {
      links.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent = open ? '✕' : '☰';
    }
    toggle.addEventListener('click', function () { setMenu(!links.classList.contains('open')); });
    links.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('open')) { setMenu(false); toggle.focus(); }
    });
    document.addEventListener('click', function (e) {
      if (links.classList.contains('open') && !e.target.closest('.nav')) setMenu(false);
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

  // ── Scroll-driven intro ────────────────────────────────────────
  // 0 → P_VIDEO   : video frames scrub with scroll (captions fade in and out)
  // P_VIDEO → P_SETTLE : camera eases out and the logo artwork crossfades in,
  //                      aligned so the two logos overlap exactly
  // P_UI_START → P_UI_END : buttons and values fade in → the landing screen
  // after that     : the landing screen holds, then the page scrolls on
  var intro = document.getElementById('intro');
  if (intro && document.documentElement.classList.contains('motion')) {
    var P_VIDEO = 0.72, P_SETTLE = 0.86, P_UI_START = 0.80, P_UI_END = 0.93;
    // Where the artwork sits relative to the video's last frame (measured offline).
    var ART_W = 0.5352, ART_CX = 0.4984, ART_CY = 0.4472;
    // Logo cluster inside the artwork (fractions of the artwork).
    var LOGO_W = 0.64, LOGO_H = 0.58 / 0.6667, LOGO_CY = 0.495;

    var canvas = intro.querySelector('.intro-canvas');
    var ctx = canvas.getContext('2d');
    var captions = [].slice.call(intro.querySelectorAll('.intro-caption'));
    var finalEl = intro.querySelector('.intro-final');
    var steps = [finalEl.querySelector('.hero-actions')].concat([].slice.call(finalEl.querySelectorAll('.feature')));
    steps.forEach(function (el) { el.setAttribute('data-step', ''); });
    var HEADER = 76;
    function measureHeader() {
      var h = document.querySelector('.site-header');
      HEADER = h ? h.offsetHeight : 76;
      document.documentElement.style.setProperty('--header-h', HEADER + 'px');
    }
    measureHeader();

    var FRAMES = 181;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var size = (window.innerWidth * dpr > 1000) ? 'lg' : 'sm';
    var frames = new Array(FRAMES);
    var currentP = 0, targetP = 0, ticking = false, lastKey = '';

    function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
    function easeOut(t) { return 1 - Math.pow(1 - t, 3); }
    function easeInOut(t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
    function lerp(a, b, t) { return a + (b - a) * t; }

    // Feathered copy of the logo artwork, built once it loads.
    var art = null;
    var artImg = new Image();
    artImg.decoding = 'async';
    artImg.onload = function () {
      var c = document.createElement('canvas');
      c.width = artImg.naturalWidth; c.height = artImg.naturalHeight;
      var x = c.getContext('2d');
      x.drawImage(artImg, 0, 0);
      x.globalCompositeOperation = 'destination-in';
      x.save();
      x.translate(c.width / 2, c.height * 0.5);
      x.scale(1, (c.height / c.width) * 1.3);
      var g = x.createRadialGradient(0, 0, c.width * 0.32, 0, 0, c.width * 0.55);
      g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
      x.fillStyle = g; x.fillRect(-c.width, -c.width, c.width * 2, c.width * 2);
      x.restore();
      art = c;
      requestDraw(true);
    };

    function src(i) { return 'assets/frames/' + size + '/f' + String(i + 1).padStart(3, '0') + '.webp'; }

    // Load order: first frame, then a coarse pass (every 8th frame) right away.
    // The rest (and the logo artwork) waits until the visitor starts scrolling
    // or the browser is idle, so the first paint stays light on mobile data.
    var order = [0], seen = { 0: true };
    [8, 4, 2, 1].forEach(function (step) {
      for (var i = 0; i < FRAMES; i += step) if (!seen[i]) { seen[i] = true; order.push(i); }
    });
    var limit = Math.ceil(FRAMES / 8), cursor = 0, inflight = 0;
    function idxNow() { return Math.round(clamp(currentP / P_VIDEO) * (FRAMES - 1)); }
    function pump() {
      while (inflight < 6 && cursor < limit) {
        (function (i) {
          var img = new Image();
          img.decoding = 'async';
          inflight++;
          img.onload = function () {
            frames[i] = img; inflight--;
            if (i === 0 || Math.abs(i - idxNow()) < 4) requestDraw(true);
            pump();
          };
          img.onerror = function () { inflight--; pump(); };
          img.src = src(i);
        })(order[cursor++]);
      }
    }
    var fullLoad = false;
    function loadRest() {
      if (fullLoad) return;
      fullLoad = true;
      limit = order.length;
      artImg.src = 'assets/img/hero-wide.webp';
      pump();
    }
    pump();
    window.addEventListener('scroll', loadRest, { passive: true, once: true });
    if ('requestIdleCallback' in window) requestIdleCallback(loadRest, { timeout: 4000 });
    else setTimeout(loadRest, 3000);

    function nearestLoaded(i) {
      for (var d = 0; d < FRAMES; d++) {
        if (frames[i - d]) return frames[i - d];
        if (frames[i + d]) return frames[i + d];
      }
      return null;
    }

    var finalH = 0;
    function resize() {
      measureHeader();
      canvas.width = Math.round(canvas.clientWidth * dpr);
      canvas.height = Math.round(canvas.clientHeight * dpr);
      finalH = finalEl.offsetHeight * dpr;
      lastKey = '';
      requestDraw(true);
    }

    // Rect of a video frame drawn at rest (cover on wide screens; on tall screens keep
    // the centre ~half of the frame visible so the logo is never cropped).
    function videoRect(iw, ih) {
      var cw = canvas.width, ch = canvas.height;
      var scale = Math.min(Math.max(cw / iw, ch / ih), cw / (iw * 0.5));
      var w = iw * scale, h = ih * scale;
      return { x: (cw - w) / 2, y: (ch - h) / 2, w: w, h: h };
    }

    // Where the artwork ends up: its logo fills the space above the landing content.
    function artEnd() {
      var cw = canvas.width, ch = canvas.height;
      var top = 18 * dpr, bottom = ch - finalH - 6 * dpr;
      var availH = Math.max(bottom - top, ch * 0.4);
      var aw = Math.min((availH * 0.98) / (LOGO_H * 0.6667), (cw * 0.94) / LOGO_W);
      var ah = aw * 0.6667;
      var cy = top + availH / 2 - (LOGO_CY - 0.5) * ah;
      return { cx: cw / 2, cy: cy, w: aw };
    }

    function feather(y, h) {
      if (y <= 1) return;
      var cw = canvas.width, f = h * 0.22, g;
      g = ctx.createLinearGradient(0, y, 0, y + f);
      g.addColorStop(0, '#000'); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(0, y - 1, cw, f + 1);
      g = ctx.createLinearGradient(0, y + h - f, 0, y + h);
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, '#000');
      ctx.fillStyle = g; ctx.fillRect(0, y + h - f, cw, f + 1);
    }

    function draw(p, force) {
      var idx = Math.round(clamp(p / P_VIDEO) * (FRAMES - 1));
      var t = easeInOut(clamp((p - P_VIDEO) / (P_SETTLE - P_VIDEO)));
      var key = idx + ':' + t.toFixed(3) + ':' + (art ? 1 : 0);
      if (!force && key === lastKey) return;
      var img = nearestLoaded(idx);
      if (!img) return;
      lastKey = key;

      var cw = canvas.width, ch = canvas.height;
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, cw, ch);

      var r = videoRect(img.naturalWidth, img.naturalHeight);
      if (t <= 0 || !art) {
        ctx.drawImage(img, r.x, r.y, r.w, r.h);
        feather(r.y, r.h);
        return;
      }
      // Artwork aligned to the video at rest, then eased to its end position.
      var a0 = { cx: r.x + ART_CX * r.w, cy: r.y + ART_CY * r.h, w: ART_W * r.w };
      var a1 = artEnd();
      var a = { cx: lerp(a0.cx, a1.cx, t), cy: lerp(a0.cy, a1.cy, t), w: lerp(a0.w, a1.w, t) };
      var k = a.w / a0.w;
      var vw = r.w * k, vh = r.h * k;
      var vx = a.cx - ART_CX * vw, vy = a.cy - ART_CY * vh;

      ctx.globalAlpha = 1 - t;
      ctx.drawImage(img, vx, vy, vw, vh);
      ctx.globalAlpha = 1;
      feather(vy, vh);
      var ah = a.w * (art.height / art.width);
      ctx.globalAlpha = t;
      ctx.drawImage(art, a.cx - a.w / 2, a.cy - ah / 2, a.w, ah);
      ctx.globalAlpha = 1;
    }

    function progress() {
      var r = intro.getBoundingClientRect();
      var total = r.height - (window.innerHeight - HEADER);
      return clamp((HEADER - r.top) / total);
    }

    function updateOverlay(p) {
      captions.forEach(function (c) {
        var from = +c.dataset.from, to = +c.dataset.to, fade = 0.045;
        var o = 0;
        if (p >= from && p <= to) o = Math.min(1, (p - from) / fade, (to - p) / fade);
        c.style.opacity = o.toFixed(3);
        c.style.transform = 'translateY(' + ((1 - o) * 10).toFixed(1) + 'px)';
        c.style.filter = o < 0.98 ? 'blur(' + ((1 - o) * 6).toFixed(1) + 'px)' : 'none';
      });
      var u = clamp((p - P_UI_START) / (P_UI_END - P_UI_START));
      finalEl.style.setProperty('--t', u.toFixed(3));
      steps.forEach(function (el, i) {
        var e = easeOut(clamp((u - i * 0.1) / 0.6));
        el.style.opacity = e.toFixed(3);
        el.style.transform = e < 1 ? 'translateY(' + ((1 - e) * 14).toFixed(1) + 'px)' : 'none';
        el.style.filter = e < 0.98 ? 'blur(' + ((1 - e) * 6).toFixed(1) + 'px)' : 'none';
      });
      var isFinal = u > 0.7;
      if (isFinal !== intro.classList.contains('final')) {
        intro.classList.toggle('final', isFinal);
      }
      intro.classList.toggle('scrolled', p > 0.02);
    }

    function loop() {
      // Light smoothing so fast flicks still read as motion, not jumps.
      currentP += (targetP - currentP) * 0.2;
      if (Math.abs(targetP - currentP) < 0.0004) currentP = targetP;
      draw(currentP, false);
      updateOverlay(currentP);
      if (currentP !== targetP) requestAnimationFrame(loop); else ticking = false;
    }

    function requestDraw(force) {
      if (force) { draw(currentP, true); updateOverlay(currentP); }
      if (!ticking) { ticking = true; requestAnimationFrame(loop); }
    }

    function onScroll() {
      targetP = progress();
      requestDraw(false);
    }

    // Keyboard users: focusing the landing buttons scrolls the landing screen into view.
    finalEl.addEventListener('focusin', function () {
      if (!intro.classList.contains('final')) {
        var total = intro.offsetHeight - (window.innerHeight - HEADER);
        window.scrollTo(0, intro.offsetTop - HEADER + total * 0.95);
      }
    });

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', resize);
    resize();
    targetP = currentP = progress();
    requestDraw(true);
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
