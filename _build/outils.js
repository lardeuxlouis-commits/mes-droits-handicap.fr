/* Outils de mes-droits-handicap.fr. Tout est calculé dans le navigateur : aucune requête réseau,
   aucun cookie, aucun stockage, aucune mesure d'audience sur les réponses. */
(function () {
  'use strict';
  var P = window.MDH_PARAMS || {};
  var eur = function (x) { return x.toLocaleString('fr-FR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' €'; };
  var num = function (v) { v = parseFloat(String(v || '').replace(/\s| /g, '').replace(',', '.')); return isNaN(v) ? 0 : v; };
  var M = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
  var fdate = function (d) { return (d.getDate() === 1 ? '1er' : d.getDate()) + ' ' + M[d.getMonth()] + ' ' + d.getFullYear(); };
  var parseD = function (s) { var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || ''); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; };
  /* Ajout de mois « de date à date » : le 31 janvier + 1 mois donne le dernier jour de février. */
  var addM = function (d, n) { var r = new Date(d.getFullYear(), d.getMonth() + n, 1); var last = new Date(r.getFullYear(), r.getMonth() + 1, 0).getDate(); r.setDate(Math.min(d.getDate(), last)); return r; };
  var addD = function (d, n) { var r = new Date(d); r.setDate(r.getDate() + n); return r; };
  var today = function () { var t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate()); };
  var days = function (a, b) { return Math.round((b - a) / 864e5); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); };
  var D = {};
  try { var el = document.getElementById('mdh-delais'); if (el) D = JSON.parse(el.textContent); } catch (e) {}
  var depSelect = function () {
    var k = Object.keys(D).sort(function (a, b) { return D[a].n.localeCompare(D[b].n, 'fr'); });
    return '<label>Votre département <small>(facultatif)</small><select name="dep"><option value="">Je ne sais pas</option>' +
      k.map(function (c) { return '<option value="' + c + '">' + esc(D[c].n) + '</option>'; }).join('') + '</select></label>';
  };

  var W = {
    /* ---------------------------------------------------------- 4 mois sans réponse */
    delai: {
      html: function () {
        return '<label>Date de dépôt du dossier complet<small>celle de l’accusé de réception ou du dépôt en ligne</small><input type="date" name="d" required></label>' +
          depSelect() +
          '<label class="mdh-full">Date de la notification de décision <small>(si vous l’avez déjà reçue)</small><input type="date" name="n"></label>';
      },
      calc: function (f) {
        var d = parseD(f.d.value); if (!d) return '<p class="mdh-note">Indiquez la date de dépôt.</p>';
        var t = today(), imp = addM(d, 4), rec = addM(imp, 2), out = '<ol class="mdh-tl">';
        out += '<li><b>' + fdate(d) + '</b>Dépôt du dossier complet.</li>';
        var c = f.dep.value, est = null;
        if (c && D[c]) { est = addD(d, Math.round(D[c].g * 30.44)); out += '<li><b>vers le ' + fdate(est) + '</b>Décision attendue si votre dossier suit le délai moyen ' + esc(D[c].de) + ' (' + String(D[c].g).replace('.', ',') + ' mois au ' + esc(P.trimestre || '') + ').</li>'; }
        out += '<li class="mdh-tl-alert"><b>' + fdate(imp) + '</b>Sans décision à cette date, la demande est considérée comme <strong>refusée</strong> (refus implicite, 4 mois après le dépôt). La MDPH peut encore décider ensuite.</li>';
        out += '<li class="mdh-tl-alert"><b>jusqu’au ' + fdate(rec) + '</b>Délai pour contester ce refus implicite par un recours amiable (RAPO), 2 mois après la date du refus implicite.</li>';
        var n = parseD(f.n.value);
        if (n) out += '<li class="mdh-tl-alert"><b>jusqu’au ' + fdate(addM(n, 2)) + '</b>Délai pour contester la décision notifiée le ' + fdate(n) + ' (2 mois après la notification).</li>';
        out += '</ol>';
        var msg;
        if (n && t > addM(n, 2)) msg = 'Le délai de 2 mois après la notification est dépassé : renseignez-vous auprès de la MDPH, une nouvelle demande reste possible.';
        else if (t >= imp) msg = 'Les 4 mois sont passés (' + days(imp, t) + ' jours de plus). Vous pouvez relancer la MDPH ou contester le refus implicite d’ici le ' + fdate(rec) + '.';
        else msg = 'Il reste ' + days(t, imp) + ' jours avant la date du refus implicite.';
        if (est && est > imp && t < imp) msg += ' Dans votre département, la décision moyenne arrive après cette limite : notez la date.';
        return '<p class="mdh-big">' + (t >= imp && !n ? 'Refus implicite atteint' : fdate(imp)) + ' <small>' + (t >= imp && !n ? 'depuis le ' + fdate(imp) : 'date du refus implicite') + '</small></p><p>' + msg + '</p>' + out +
          '<p class="mdh-note">Calcul indicatif à partir des règles générales (silence de 4 mois, recours dans les 2 mois). La notification de la MDPH indique toujours les voies et délais de recours qui s’appliquent à votre décision.</p>' +
          '<p class="mdh-btns"><a class="mdh-btn mdh-alt" href="/dossier-mdph-trop-long/">Relancer la MDPH</a><a class="mdh-btn mdh-alt" href="/recours-mdph/">Contester une décision</a></p>';
      }
    },
    /* ---------------------------------------------------------- fin de droits */
    fin: {
      html: function () {
        return '<label>Date de fin de vos droits<small>elle figure sur la notification de la MDPH</small><input type="date" name="f" required></label>' +
          '<label>Droit concerné<select name="t"><option value="AAH">AAH</option><option value="PCH">PCH</option><option value="AEEH">AEEH</option><option value="RQTH">RQTH</option><option value="CMI">Carte mobilité inclusion</option><option value="orientation">Orientation (ESAT, établissement, scolarisation)</option></select></label>' +
          depSelect();
      },
      calc: function (f) {
        var fin = parseD(f.f.value); if (!fin) return '<p class="mdh-note">Indiquez la date de fin de vos droits.</p>';
        var t = today(), dep = addM(fin, -6), cert = addM(dep, -3), nom = f.t.value;
        var c = f.dep.value, g = c && D[c] ? D[c].g : null;
        var out = '<ol class="mdh-tl">';
        out += '<li><b>à partir du ' + fdate(cert) + '</b>Prenez rendez-vous avec votre médecin pour un certificat médical récent (il doit dater de moins d’un an au dépôt).</li>';
        out += '<li class="mdh-tl-alert"><b>le ' + fdate(dep) + ' au plus tard</b>Déposez la demande de renouvellement (' + esc(nom) + '), 6 mois avant la fin des droits.</li>';
        if (g) out += '<li><b>vers le ' + fdate(addD(dep, Math.round(g * 30.44))) + '</b>Décision attendue si le dossier suit le délai moyen ' + esc(D[c].de) + ' (' + String(g).replace('.', ',') + ' mois).</li>';
        out += '<li><b>' + fdate(fin) + '</b>Fin des droits actuels.</li></ol>';
        var msg = t > fin ? 'Vos droits sont arrivés à échéance : déposez une demande sans attendre et signalez-le à la MDPH.' : t >= dep ? 'Vous êtes à moins de 6 mois de la fin de vos droits : déposez votre renouvellement maintenant.' : 'Il vous reste ' + days(t, dep) + ' jours avant la date conseillée de dépôt.';
        if (g && g > 6 && t < fin) msg += ' Attention : le délai moyen de votre MDPH dépasse 6 mois, déposez dès que possible.';
        var ics = 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//mes-droits-handicap.fr//rappel//FR\r\nBEGIN:VEVENT\r\nUID:' + Date.now() + '@mes-droits-handicap.fr\r\nDTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z\r\nDTSTART;VALUE=DATE:' +
          dep.getFullYear() + ('0' + (dep.getMonth() + 1)).slice(-2) + ('0' + dep.getDate()).slice(-2) + '\r\nSUMMARY:Renouvellement MDPH (' + nom + ') : déposer le dossier\r\nDESCRIPTION:Droits jusqu\'au ' + fdate(fin) + '. Prévoir un certificat médical de moins d\'un an.\r\nBEGIN:VALARM\r\nTRIGGER:-P30D\r\nACTION:DISPLAY\r\nDESCRIPTION:Renouvellement MDPH dans 30 jours\r\nEND:VALARM\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n';
        var href = 'data:text/calendar;charset=utf-8,' + encodeURIComponent(ics);
        return '<p class="mdh-big">' + fdate(dep) + ' <small>date limite conseillée pour redéposer</small></p><p>' + msg + '</p>' + out +
          '<p class="mdh-btns"><a class="mdh-btn" download="rappel-renouvellement-mdph.ics" href="' + href + '">Ajouter le rappel à mon agenda</a></p>' +
          '<p class="mdh-note">Le fichier de rappel est créé dans votre navigateur et enregistré seulement sur votre appareil. Certains droits peuvent être accordés à vie : voyez <a href="/renouvellement-mdph/">le guide du renouvellement</a>.</p>';
      }
    },
    /* ---------------------------------------------------------- AEEH */
    aeeh: {
      html: function () {
        return '<label>Dépenses mensuelles liées au handicap<small>non remboursées : matériel, soins, transport, séances…</small><input name="dep" inputmode="decimal" placeholder="ex. 300"></label>' +
          '<label>Votre activité professionnelle<select name="act"><option value="0">Pas de réduction</option><option value="20">Réduite d’au moins 20 %</option><option value="50">Réduite d’au moins 50 %</option><option value="100">Arrêtée pour s’occuper de l’enfant</option></select></label>' +
          '<label>Tierce personne rémunérée<select name="tp"><option value="0">Aucune</option><option value="8">Au moins 8 h par semaine</option><option value="20">Au moins 20 h par semaine</option><option value="35">Temps plein</option></select></label>' +
          '<label class="mdh-chk mdh-full"><input type="checkbox" name="cs"> L’état de l’enfant impose des contraintes permanentes de surveillance et de soins à la charge de la famille</label>' +
          '<label class="mdh-chk mdh-full"><input type="checkbox" name="pi"> Vous élevez seul(e) l’enfant</label>';
      },
      calc: function (f) {
        var A = P.aeeh, dep = num(f.dep.value), act = +f.act.value, tp = +f.tp.value, cs = f.cs.checked, pi = f.pi.checked;
        var r20 = act >= 20 || tp >= 8, r50 = act >= 50 || tp >= 20, r100 = act >= 100 || tp >= 35, cat = 0;
        if (r100 && cs) cat = 6;
        else if (r100 && dep >= A.s5) cat = 5;
        else if (r100 || (r50 && dep >= A.s4b) || (r20 && dep >= A.s4c) || dep >= A.s4) cat = 4;
        else if (r50 || (r20 && dep >= A.s3b) || dep >= A.s3) cat = 3;
        else if (r20 || dep >= A.s2) cat = 2;
        else if (dep >= A.s1) cat = 1;
        var comp = cat ? A.comp[cat - 1] : 0, maj = (pi && cat >= 2 && (act > 0 || tp > 0)) ? A.maj[cat - 1] : 0, tot = A.base + comp + maj;
        var why = cat === 0 ? 'vos dépenses et votre organisation, telles que saisies, ne correspondent à aucune catégorie de complément' : 'catégorie ' + cat + ' estimée selon les critères réglementaires';
        return '<p class="mdh-big">' + eur(tot) + ' <small>par mois (estimation)</small></p><ul>' +
          '<li>AEEH de base : ' + eur(A.base) + '</li>' +
          (cat ? '<li>Complément de ' + cat + '<sup>e</sup> catégorie : ' + eur(comp) + '</li>' : '<li>Pas de complément : ' + why + '</li>') +
          (maj ? '<li>Majoration pour parent isolé : ' + eur(maj) + '</li>' : (pi && cat >= 2 ? '<li>La majoration parent isolé suppose une réduction d’activité ou l’embauche d’une tierce personne.</li>' : '')) +
          '</ul><p class="mdh-note">Montants en vigueur depuis le ' + esc(A.date) + '. C’est la CDAPH, à la MDPH, qui fixe la catégorie après évaluation : gardez les justificatifs de vos dépenses et de votre réduction d’activité. Base de calcul : service-public.gouv.fr et monparcourshandicap.gouv.fr.</p>' +
          '<p class="mdh-btns"><a class="mdh-btn mdh-alt" href="/aeeh/">Comprendre les 6 catégories</a></p>';
      }
    },
    /* ---------------------------------------------------------- AAH */
    aah: {
      html: function () {
        return '<label>Votre situation<select name="sit"><option value="sans">Je ne travaille pas</option><option value="mo">Je travaille (entreprise, fonction publique)</option><option value="esat">Je travaille en ESAT</option></select></label>' +
          '<label>Taux d’incapacité reconnu ou attendu<select name="tx"><option value="80">80 % ou plus</option><option value="50">De 50 à 79 %</option><option value="0">Moins de 50 % ou inconnu</option></select></label>' +
          '<label data-s="sans esat">Vos revenus imposables de ' + esc(P.aah.anneeRef) + '<small>salaires, pensions, rentes (hors AAH), montant annuel</small><input name="ran" inputmode="decimal" placeholder="ex. 3 000"></label>' +
          '<label data-s="mo">Salaire net imposable mensuel moyen du dernier trimestre<input name="sal" inputmode="decimal" placeholder="ex. 900"></label>' +
          '<label class="mdh-chk mdh-full" data-s="mo"><input type="checkbox" name="rep"> J\u2019ai commencé ou repris ce travail il y a moins de 6 mois, alors que je touchais déjà l\u2019AAH</label>' +
          '<label data-s="mo">Autres revenus mensuels <small>(pension d’invalidité, rente…)</small><input name="aut" inputmode="decimal" placeholder="ex. 0"></label>' +
          '<label>Enfants à votre charge<select name="enf"><option value="0">Aucun</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4 ou plus</option></select></label>';
      },
      init: function (f) {
        var maj = function () { var s = f.sit.value; f.querySelectorAll('[data-s]').forEach(function (l) { l.hidden = l.getAttribute('data-s').split(' ').indexOf(s) < 0; }); };
        f.sit.addEventListener('change', maj); maj();
      },
      calc: function (f) {
        var A = P.aah, tx = +f.tx.value, enf = Math.min(4, +f.enf.value), sit = f.sit.value;
        if (tx === 0) return '<p class="mdh-big">Pas d’AAH</p><p>L’AAH demande un taux d’incapacité d’au moins 80 %, ou de 50 à 79 % avec une restriction substantielle et durable d’accès à l’emploi. C’est la MDPH qui fixe ce taux.</p><p class="mdh-btns"><a class="mdh-btn mdh-alt" href="/aah/">Les conditions de l’AAH</a></p>';
        var plaf = A.max * 12 * (1 + A.majEnfant * enf), res, det = [];
        if (sit === 'mo') {
          var sal = num(f.sal.value), aut = num(f.aut.value), seuil = A.smicBrut * A.seuilPart;
          var ab = Math.min(sal, seuil) * (1 - A.ab1) + Math.max(0, sal - seuil) * (1 - A.ab2);
          if (f.rep.checked) { ab = 0; det.push('Reprise d\u2019activité depuis moins de 6 mois : le salaire n\u2019est pas pris en compte pendant cette période (6 mois au plus sur 12 mois glissants)'); }
          res = ab + aut;
          if (!f.rep.checked) det.push('Salaire retenu après abattement : ' + eur(ab) + ' par mois (' + Math.round(A.ab1 * 100) + ' % d’abattement jusqu’à ' + eur(seuil) + ', ' + Math.round(A.ab2 * 100) + ' % au-delà)');
          if (aut) det.push('Autres revenus retenus : ' + eur(aut) + ' par mois');
        } else {
          var ran = num(f.ran.value);
          res = Math.max(0, ran * (1 - A.abNet)) / 12;
          det.push('Revenus de ' + esc(A.anneeRef) + ' retenus après l’abattement de ' + Math.round(A.abNet * 100) + ' % : ' + eur(res * 12) + ' par an, soit ' + eur(res) + ' par mois');
        }
        var plafM = plaf / 12, aah = Math.max(0, Math.min(A.max, plafM - res));
        if (aah < 0.01) aah = 0;
        det.push('Plafond de ressources : ' + eur(plaf) + ' par an' + (enf ? ' (majoré de ' + Math.round(A.majEnfant * 100) + ' % par enfant)' : ''));
        if (tx === 50) det.push('Entre 50 et 79 %, l’AAH suppose aussi une restriction substantielle et durable d’accès à l’emploi, reconnue par la MDPH.');
        return '<p class="mdh-big">' + (aah ? eur(aah) + ' <small>par mois (estimation)</small>' : 'Pas d’AAH à verser') + '</p><ul><li>' + det.join('</li><li>') + '</li></ul>' +
          '<p class="mdh-note">Estimation simplifiée sur le barème officiel (AAH à taux plein : ' + eur(A.max) + ' par mois depuis le ' + esc(A.date) + '). Le calcul de la CAF tient compte d’autres éléments (abattements particuliers, pension d’invalidité, hospitalisation, ESAT). Pour un chiffre plus précis, utilisez le <a href="https://www.mesdroitssociaux.gouv.fr/" rel="noopener" target="_blank">simulateur officiel mesdroitssociaux.gouv.fr</a>.</p>' +
          '<p class="mdh-btns"><a class="mdh-btn mdh-alt" href="/aah/">Comprendre le calcul</a><a class="mdh-btn mdh-alt" href="/delais-mdph/">Délai de ma MDPH</a></p>';
      }
    }
  };

  document.querySelectorAll('[data-outil]').forEach(function (box) {
    var w = W[box.getAttribute('data-outil')]; if (!w) return;
    box.innerHTML = '<p class="mdh-lab">Calcul dans votre navigateur, rien n’est envoyé</p><form class="mdh-f" novalidate>' + w.html() + '<button class="mdh-btn" type="submit">Calculer</button></form><div class="mdh-res" aria-live="polite"></div>';
    var f = box.querySelector('form'), out = box.querySelector('.mdh-res');
    if (w.init) w.init(f);
    var run = function (e) { if (e) e.preventDefault(); out.innerHTML = w.calc(f); };
    f.addEventListener('submit', run);
    f.addEventListener('change', function () { if (out.innerHTML) run(); });
  });

  /* ---------------------------------------------------------- classement : tri et recherche */
  var tb = document.getElementById('classement');
  if (tb) {
    var body = tb.tBodies[0], ths = tb.tHead.rows[0].cells;
    Array.prototype.forEach.call(ths, function (th, k) {
      var b = th.querySelector('button'); if (!b) return;
      b.addEventListener('click', function () {
        var asc = th.getAttribute('aria-sort') !== 'ascending';
        Array.prototype.forEach.call(ths, function (x) { x.removeAttribute('aria-sort'); });
        th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
        var rows = Array.prototype.slice.call(body.rows);
        rows.sort(function (a, b) {
          var x = a.cells[k].getAttribute('data-v'), y = b.cells[k].getAttribute('data-v');
          if (x === '' && y === '') return 0; if (x === '') return 1; if (y === '') return -1;
          var nx = parseFloat(x), ny = parseFloat(y);
          var r = (isNaN(nx) || isNaN(ny)) ? x.localeCompare(y, 'fr') : nx - ny;
          return asc ? r : -r;
        });
        rows.forEach(function (r) { body.appendChild(r); });
      });
    });
    var q = document.getElementById('q'), q2 = document.getElementById('q2'), res = document.getElementById('q-res');
    var norm = function (s) { return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
    var filt = function (v) {
      v = norm(v.trim()); var n = 0, last = null;
      Array.prototype.forEach.call(body.rows, function (r) { var ok = !v || norm(r.getAttribute('data-nom')).indexOf(v) >= 0; r.hidden = !ok; r.classList.toggle('mdh-hl', !!v && ok); if (ok) { n++; last = r; } });
      if (v && n === 1 && res) {
        var c = last.cells, a = c[1].querySelector('a');
        res.innerHTML = '<span><strong>' + esc(c[1].textContent) + '</strong> : ' + esc(c[2].textContent) + ' mois en moyenne (rang ' + esc(c[0].textContent) + '). ' + (parseFloat(c[2].getAttribute('data-v')) > 4 ? 'C’est plus que les 4 mois du refus implicite : déposez dès que votre dossier est complet. ' : '') + (a ? '<a href="' + a.getAttribute('href') + '">Voir la page détaillée</a>' : '<a href="/outils/delai-reponse-mdph/">Calculer mes dates</a>') + '</span>';
        res.hidden = false;
      } else if (res) res.hidden = true;
    };
    if (q) q.addEventListener('change', function () { q2.value = ''; filt(q.value); });
    if (q2) q2.addEventListener('input', function () { q.value = ''; filt(q2.value); });
    if (location.hash && q2) { var h = decodeURIComponent(location.hash.slice(1)); if (/^[0-9a-z]{2,3}$/i.test(h)) { q2.value = h; filt(h); } }
  }
})();
