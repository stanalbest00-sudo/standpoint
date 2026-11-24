// Standpoint Seychelles — small site behaviours (no dependencies)
(function () {
  // Mobile navigation toggle
  var toggle = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Footer year
  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  // Quiz: each .q has buttons; the correct one carries data-correct
  var quizzes = document.querySelectorAll('.quiz');
  quizzes.forEach(function (quiz) {
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

  // Contact form: opens the visitor's email app with the message pre-filled
  var form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var to = form.getAttribute('data-email');
      var name = form.elements.name.value;
      var topic = form.elements.topic.value;
      var msg = form.elements.message.value;
      var subject = encodeURIComponent('[Standpoint] ' + topic + ' — ' + name);
      var body = encodeURIComponent(msg + '\n\n— ' + name);
      window.location.href = 'mailto:' + to + '?subject=' + subject + '&body=' + body;
    });
  }
})();
