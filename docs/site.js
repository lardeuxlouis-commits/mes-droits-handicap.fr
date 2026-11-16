/* mes-droits-handicap.fr : menu mobile, apparitions au défilement, graphiques, compteurs, recherche de département.
   Aucune requête réseau, aucun cookie, aucun stockage. Animations : transform et opacity uniquement. */
(function () {
  'use strict';
  var d = document, H = d.documentElement;
  var R = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var IO = 'IntersectionObserver' in window;

  /* ---------------------------------------------------------- recherche tolérante (nom, numéro, sans accents) */
  var norm = function (s) {
    return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[-'’().]/g, ' ').replace(/\bst\b/g, 'saint').replace(/\bste\b/g, 'sainte').replace(/\s+/g, ' ').trim();
  };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); };
  var match = function (items, q) {
    q = norm(q); if (!q) return [];
    var w = q.split(' ');
    var out = items.filter(function (it) { var k = it._k || (it._k = norm(it.n + ' ' + it.c)); return w.every(function (x) { return k.indexOf(x) >= 0; }); });
    out.sort(function (a, b) {
      var sa = (a.c.toLowerCase() === q || norm(a.n).indexOf(q) === 0) ? 0 : 1, sb = (b.c.toLowerCase() === q || norm(b.n).indexOf(q) === 0) ? 0 : 1;
      return sa - sb || a.n.localeCompare(b.n, 'fr');
    });
    return out.slice(0, 6);
  };
  /* root contient un input[type=search] et une liste .mdh-sugg ; onPick(item) */
  window.MDH_find = function (root, items, onPick) {
    var inp = root.querySelector('input[type=search]'), ul = root.querySelector('.mdh-sugg'), cur = -1, list = [];
    if (!inp || !ul) return;
    var id = ul.id || (ul.id = 'sg' + Math.random().toString(36).slice(2, 8));
    inp.setAttribute('role', 'combobox'); inp.setAttribute('aria-autocomplete', 'list'); inp.setAttribute('aria-controls', id); inp.setAttribute('aria-expanded', 'false');
    ul.setAttribute('role', 'listbox');
    var close = function () { ul.innerHTML = ''; ul.hidden = true; inp.setAttribute('aria-expanded', 'false'); cur = -1; };
    var mark = function () { Array.prototype.forEach.call(ul.children, function (li, i) { li.setAttribute('aria-selected', i === cur ? 'true' : 'false'); }); };
    var pick = function (it) { inp.value = it.n; close(); onPick(it); };
    var draw = function () {
      list = match(items, inp.value); cur = list.length ? 0 : -1;
      if (!inp.value.trim()) { close(); return; }
      ul.innerHTML = list.length ? list.map(function (it, i) {
        return '<li role="option" id="' + id + '-' + i + '" aria-selected="' + (i === 0) + '"><span>' + esc(it.n) + '</span>' + (it.g != null ? '<em>' + String(it.g).replace('.', ',') + ' mois</em>' : '') + '</li>';
      }).join('') : '<li class="mdh-sugg-0" aria-disabled="true">Aucun département trouvé. Essayez le numéro, par exemple 93.</li>';
      ul.hidden = false; inp.setAttribute('aria-expanded', 'true');
    };
    inp.addEventListener('input', draw);
    inp.addEventListener('focus', function () { if (inp.value && !ul.children.length) draw(); });
    inp.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' && list.length) { cur = (cur + 1) % list.length; mark(); e.preventDefault(); }
      else if (e.key === 'ArrowUp' && list.length) { cur = (cur - 1 + list.length) % list.length; mark(); e.preventDefault(); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!ul.children.length || ul.hidden) draw(); if (list[cur]) pick(list[cur]); }
      else if (e.key === 'Escape') close();
    });
    ul.addEventListener('mousedown', function (e) { e.preventDefault(); });
    ul.addEventListener('click', function (e) { var li = e.target.closest('li[role=option]'); if (li) pick(list[Array.prototype.indexOf.call(ul.children, li)]); });
    d.addEventListener('click', function (e) { if (!root.contains(e.target)) close(); });
    var go = function (e) { if (e) e.preventDefault(); draw(); if (list[0]) pick(list[0]); else inp.focus(); };
    if (root.tagName === 'FORM') root.addEventListener('submit', go);
    else { var btn = root.querySelector('button.mdh-find-go'); if (btn) btn.addEventListener('click', go); }
    return { reset: function () { inp.value = ''; close(); } };
  };

  /* Recherche de l'accueil : affiche tout de suite le délai, puis les liens utiles */
  var dj = d.getElementById('mdh-deps');
  if (dj) {
    var items = [];
    try { items = JSON.parse(dj.textContent).map(function (r) { return {n: r[0], c: r[1], g: r[2], u: r[3], de: r[4]}; }); } catch (e) {}
    d.querySelectorAll('.mdh-find[data-go]').forEach(function (root) {
      var res = root.parentNode.querySelector('.mdh-find-res');
      MDH_find(root, items, function (it) {
        if (!res) { location.href = it.u || '/delais-mdph/'; return; }
        var g = String(it.g).replace('.', ',');
        res.innerHTML = '<p class="mdh-fr-n"><b>' + g + '</b> mois</p><div><p class="mdh-fr-t">La MDPH ' + esc(it.de) + ' met en moyenne <b>' + g + ' mois</b> à répondre' +
          (it.g > 4 ? ', plus que les 4 mois du refus implicite : déposez dès que votre dossier est complet.' : ', sous la limite de 4 mois pour un dossier complet.') + '</p>' +
          '<p class="mdh-fr-l"><a href="' + esc(it.u || '/delais-mdph/#' + it.c) + '">' + (it.u ? 'Voir la page de ma MDPH' : 'Voir le classement') + ' →</a><a href="/outils/delai-reponse-mdph/">Calculer mes dates →</a></p></div>';
        res.hidden = false;
      });
    });
  }

  /* ---------------------------------------------------------- menu mobile */
  var mb = d.querySelector('.mdh-menu'), nav = d.getElementById('mdh-nav');
  if (mb && nav) mb.addEventListener('click', function () {
    var o = mb.getAttribute('aria-expanded') !== 'true';
    mb.setAttribute('aria-expanded', o ? 'true' : 'false'); nav.classList.toggle('mdh-open', o);
  });

  /* ---------------------------------------------------------- apparitions, graphiques, compteurs */
  if (R || !IO) return;
  var vh = window.innerHeight || 800;
  var below = function (el) { return el.getBoundingClientRect().top > vh * 0.92; };
  var count = function (el) {
    var t = el.textContent, m = /^(\d[\d   ]*)(,(\d+))?/.exec(t);
    if (!m) return;
    var whole = m[1].replace(/\D/g, ''), dec = m[3] || '', v = parseFloat(whole + '.' + (dec || '0')), rest = t.slice(m[0].length), n = dec.length;
    if (!(v > 0)) return;
    var t0 = null, dur = 1100;
    var fmt = function (x) { var s = x.toFixed(n).split('.'); return s[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + (n ? ',' + s[1] : ''); };
    var step = function (ts) { if (!t0) t0 = ts; var p = Math.min(1, (ts - t0) / dur); p = 1 - Math.pow(1 - p, 3); el.textContent = fmt(v * p) + rest; if (p < 1) requestAnimationFrame(step); else el.textContent = t; };
    el.textContent = fmt(0) + rest; requestAnimationFrame(step);
  };
  var SEL = 'main h2, main .mdh-sec > p, .mdh-urg > li, .mdh-tile, .mdh-kpis > li, .mdh-cta, .mdh-offre, main details, .mdh-next li, .mdh-deps li, .mdh-answer, .mdh-steps > li, .mdh-ex, .mdh-warn, .mdh-model, .mdh-contact, .mdh-tw, .mdh-tool-box, .mdh-qui, .mdh-step3 > li';
  var els = [].slice.call(d.querySelectorAll(SEL)).filter(below);
  var charts = [].slice.call(d.querySelectorAll('.mdh-chart'));
  var nums = [].slice.call(d.querySelectorAll('.mdh-kpis b, [data-count]')).filter(below);
  H.classList.add('mdh-anim');
  /* cascade : rang de chaque élément parmi ses frères animés */
  els.forEach(function (el) {
    var i = 0, s = el.previousElementSibling;
    while (s && i < 6) { if (els.indexOf(s) >= 0) i++; s = s.previousElementSibling; }
    el.style.setProperty('--d', (i * 70) + 'ms'); el.classList.add('mdh-rv');
  });
  charts.forEach(function (c) { if (!below(c)) c.classList.add('in'); });
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (x) {
      if (!x.isIntersecting) return;
      var t = x.target; io.unobserve(t);
      t.classList.add('in');
      if (nums.indexOf(t) >= 0) count(t);
    });
  }, {rootMargin: '0px 0px -8% 0px', threshold: 0.08});
  els.concat(charts.filter(function (c) { return !c.classList.contains('in'); })).concat(nums).forEach(function (e) { io.observe(e); });
})();
