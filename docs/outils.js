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
  /* Département : champ de recherche tolérant (nom, numéro, sans accents), valeur dans un champ caché */
  var depSelect = function () {
    return '<div class="mdh-full mdh-q"><label class="mdh-ql" for="dep-q">Votre département <small>(facultatif, pour la date de décision attendue)</small></label>' +
      '<div class="mdh-find mdh-find-f"><div class="mdh-sfield"><svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 20 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>' +
      '<input id="dep-q" type="search" autocomplete="off" placeholder="Nom ou numéro, par exemple 93"></div><ul class="mdh-sugg" hidden></ul></div><input type="hidden" name="dep" value=""></div>';
  };
  /* Choix en cartes cliquables (boutons radio) : f.nom.value fonctionne comme avec un menu déroulant */
  var uid = 0;
  var choice = function (name, legend, opts, def, attrs) {
    return '<fieldset class="mdh-ch mdh-full"' + (attrs || '') + '><legend>' + legend + '</legend><div>' + opts.map(function (o) {
      var id = 'c' + (++uid);
      return '<input type="radio" id="' + id + '" name="' + name + '" value="' + o[0] + '"' + (String(o[0]) === String(def) ? ' checked' : '') + '><label for="' + id + '">' + o[1] + '</label>';
    }).join('') + '</div></fieldset>';
  };
  /* Mise en forme commune des résultats : chiffre en grand, phrase claire, détail repliable, suite */
  var result = function (big, small, phrase, corps, how, links) {
    return '<div class="mdh-rhead"><p class="mdh-rk">Résultat</p><p class="mdh-big">' + String(big).replace(/\u202f/g, '\u00a0') + (small ? ' <small>' + small + '</small>' : '') + '</p><p class="mdh-rs">' + phrase + '</p></div>' +
      (corps || '') + (how ? '<details class="mdh-how"><summary>Comment c’est calculé</summary>' + how + '</details>' : '') +
      '<div class="mdh-rnext">' + (links || '') + '<button type="button" class="mdh-restart">Recommencer</button></div>';
  };
  var wait = function (t) { return '<p class="mdh-rwait">' + t + '</p>'; };

  var W = {
    /* ---------------------------------------------------------- 4 mois sans réponse */
    delai: {
      html: function () {
        return '<label class="mdh-full">Date de dépôt du dossier complet<small>celle de l’accusé de réception ou du dépôt en ligne</small><input type="date" name="d" required></label>' +
          depSelect() +
          '<label class="mdh-full">Date de la notification de décision <small>(facultatif, si vous l’avez déjà reçue)</small><input type="date" name="n"></label>';
      },
      calc: function (f) {
        var d = parseD(f.d.value); if (!d) return wait('Indiquez la date de dépôt : vos dates s’affichent ici aussitôt.');
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
        return result(t >= imp && !n ? 'Refus implicite atteint' : fdate(imp), t >= imp && !n ? 'depuis le ' + fdate(imp) : 'date du refus implicite', msg, out,
          '<p class="mdh-note">Calcul indicatif à partir des règles générales (silence de 4 mois, recours dans les 2 mois). La notification de la MDPH indique toujours les voies et délais de recours qui s’appliquent à votre décision.</p>',
          '<a class="mdh-btn mdh-alt" href="/dossier-mdph-trop-long/">Relancer la MDPH</a><a class="mdh-btn mdh-alt" href="/recours-mdph/">Contester une décision</a>');
      }
    },
    /* ---------------------------------------------------------- fin de droits */
    fin: {
      html: function () {
        return '<label class="mdh-full">Date de fin de vos droits<small>elle figure sur la notification de la MDPH</small><input type="date" name="f" required></label>' +
          choice('t', 'Droit concerné', [['AAH', 'AAH'], ['PCH', 'PCH'], ['AEEH', 'AEEH'], ['RQTH', 'RQTH'], ['CMI', 'Carte mobilité inclusion'], ['orientation', 'Orientation (ESAT, établissement, scolarisation)']], 'AAH') +
          depSelect();
      },
      calc: function (f) {
        var fin = parseD(f.f.value); if (!fin) return wait('Indiquez la date de fin de vos droits : votre calendrier s’affiche ici aussitôt.');
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
        return result(fdate(dep), 'date limite conseillée pour redéposer', msg, out,
          '<p class="mdh-note">Dépôt 6 mois avant la fin des droits, certificat médical à prévoir 3 mois plus tôt. Le fichier de rappel est créé dans votre navigateur et enregistré seulement sur votre appareil. Certains droits peuvent être accordés à vie : voyez <a href="/renouvellement-mdph/">le guide du renouvellement</a>.</p>',
          '<a class="mdh-btn" download="rappel-renouvellement-mdph.ics" href="' + href + '">Ajouter le rappel à mon agenda</a><a class="mdh-btn mdh-alt" href="/dossier-mdph/">Préparer mon dossier pas à pas</a>');
      }
    },
    /* ---------------------------------------------------------- AEEH */
    aeeh: {
      html: function () {
        return '<label class="mdh-full mdh-eur">Dépenses mensuelles liées au handicap<small>non remboursées : matériel, soins, transport, séances…</small><input name="dep" inputmode="decimal" placeholder="ex. 300"></label>' +
          choice('act', 'Votre activité professionnelle', [['0', 'Pas de réduction'], ['20', 'Réduite d’au moins 20 %'], ['50', 'Réduite d’au moins 50 %'], ['100', 'Arrêtée pour s’occuper de l’enfant']], '0') +
          choice('tp', 'Tierce personne rémunérée', [['0', 'Aucune'], ['8', 'Au moins 8 h par semaine'], ['20', 'Au moins 20 h par semaine'], ['35', 'Temps plein']], '0') +
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
        return result(eur(tot), 'par mois (estimation)', 'Vous pourriez recevoir environ ' + eur(tot) + ' par mois pour votre enfant, d’après vos réponses.', '', '<ul>' +
          '<li>AEEH de base : ' + eur(A.base) + '</li>' +
          (cat ? '<li>Complément de ' + cat + '<sup>e</sup> catégorie : ' + eur(comp) + '</li>' : '<li>Pas de complément : ' + why + '</li>') +
          (maj ? '<li>Majoration pour parent isolé : ' + eur(maj) + '</li>' : (pi && cat >= 2 ? '<li>La majoration parent isolé suppose une réduction d’activité ou l’embauche d’une tierce personne.</li>' : '')) +
          '</ul><p class="mdh-note">Montants en vigueur depuis le ' + esc(A.date) + '. C’est la CDAPH, à la MDPH, qui fixe la catégorie après évaluation : gardez les justificatifs de vos dépenses et de votre réduction d’activité. Base de calcul : service-public.gouv.fr et monparcourshandicap.gouv.fr.</p>',
          '<a class="mdh-btn mdh-alt" href="/aeeh/">Comprendre les 6 catégories</a><a class="mdh-btn mdh-alt" href="/delais-mdph/">Délai de ma MDPH</a>');
      }
    },
    /* ---------------------------------------------------------- AAH */
    aah: {
      html: function () {
        return choice('sit', 'Votre situation', [['sans', 'Je ne travaille pas'], ['mo', 'Je travaille (entreprise, fonction publique)'], ['esat', 'Je travaille en ESAT']], 'sans') +
          choice('tx', 'Taux d’incapacité reconnu ou attendu', [['80', '80 % ou plus'], ['50', 'De 50 à 79 %'], ['0', 'Moins de 50 % ou inconnu']], '80') +
          '<label class="mdh-eur" data-s="sans">Votre revenu net catégoriel de ' + esc(P.aah.anneeRef) + '<small>ligne « revenu net catégoriel » de l’avis d’impôt sur les revenus de ' + esc(P.aah.anneeRef) + ' (pensions, rentes, hors AAH), montant annuel, déjà net de la déduction de 10 %</small><input name="ran" inputmode="decimal" placeholder="ex. 8 400"></label>' +
          '<label class="mdh-eur" data-s="esat">Rémunération garantie mensuelle moyenne du dernier trimestre<small>montant net imposable de vos bulletins de l’Ésat</small><input name="rg" inputmode="decimal" placeholder="ex. 750"></label>' +
          choice('esp', 'Part de la rémunération payée par l’Ésat <small>(elle figure sur le bulletin, à côté de l’aide au poste)</small>', [['0', 'Moins de 10 % du Smic'], ['1', 'De 10 à 15 %'], ['2', 'De 15 à 20 %'], ['3', '20 % ou plus'], ['x', 'Je ne sais pas']], 'x', ' data-s="esat"') +
          '<label class="mdh-eur" data-s="mo">Salaire net imposable mensuel moyen du dernier trimestre<input name="sal" inputmode="decimal" placeholder="ex. 900"></label>' +
          '<label class="mdh-chk mdh-full" data-s="mo"><input type="checkbox" name="rep"> J\u2019ai commencé ou repris ce travail il y a moins de 6 mois, alors que je touchais déjà l\u2019AAH</label>' +
          '<label class="mdh-eur" data-s="mo esat">Autres revenus mensuels <small>(pension d’invalidité, rente…)</small><input name="aut" inputmode="decimal" placeholder="ex. 0"></label>' +
          choice('enf', 'Enfants à votre charge', [['0', 'Aucun'], ['1', '1'], ['2', '2'], ['3', '3'], ['4', '4 ou plus']], '0');
      },
      init: function (f) {
        var maj = function () { var s = f.sit.value; f.querySelectorAll('[data-s]').forEach(function (l) { l.hidden = l.getAttribute('data-s').split(' ').indexOf(s) < 0; }); };
        f.addEventListener('change', maj); maj();
      },
      calc: function (f) {
        var A = P.aah, tx = +f.tx.value, enf = Math.min(4, +f.enf.value), sit = f.sit.value;
        if (tx === 0) return result('Pas d’AAH', '', 'L’AAH demande un taux d’incapacité d’au moins 80 %, ou de 50 à 79 % avec une restriction substantielle et durable d’accès à l’emploi. C’est la MDPH qui fixe ce taux.', '', '', '<a class="mdh-btn mdh-alt" href="/aah/">Les conditions de l’AAH</a>');
        var plaf = A.max * 12 * (1 + A.majEnfant * enf), res, det = [], cumul = null, rg = 0;
        if (sit === 'mo') {
          var sal = num(f.sal.value), aut = num(f.aut.value), seuil = Math.round(A.smicBrut * A.seuilPart * 100) / 100;
          var ab = Math.min(sal, seuil) * (1 - A.ab1) + Math.max(0, sal - seuil) * (1 - A.ab2);
          if (f.rep.checked) { ab = 0; det.push('Reprise d\u2019activité depuis moins de 6 mois : le salaire n\u2019est pas pris en compte pendant cette période (6 mois au plus sur 12 mois glissants)'); }
          res = ab + aut;
          if (!f.rep.checked) det.push('Salaire retenu après abattement : ' + eur(ab) + ' par mois (' + Math.round(A.ab1 * 100) + ' % d’abattement jusqu’à ' + eur(seuil) + ', ' + Math.round(A.ab2 * 100) + ' % au-delà)');
          if (aut) det.push('Autres revenus retenus : ' + eur(aut) + ' par mois');
        } else if (sit === 'esat') {
          /* Depuis le 1er octobre 2026 : revenus du dernier trimestre, abattement de 3,5 à 5 % (D821-10), cumul plafonné (D821-5) */
          rg = num(f.rg.value); var au2 = num(f.aut.value), k = f.esp.value, tab = k === 'x' ? A.esatAb[0] : A.esatAb[+k];
          res = rg * (1 - tab) + au2;
          det.push('Rémunération garantie retenue après l’abattement de ' + String(Math.round(tab * 1000) / 10).replace('.', ',') + ' % : ' + eur(rg * (1 - tab)) + ' par mois' + (k === 'x' ? ' (taux le plus bas, faute de connaître la part payée par l’Ésat : estimation prudente)' : ''));
          if (au2) det.push('Autres revenus retenus : ' + eur(au2) + ' par mois');
          cumul = A.smicBrut * A.esatCumul * (enf ? 1 + A.esatCumulMaj : 1);
        } else {
          /* Revenu net catégoriel : déjà net de la déduction fiscale de 10 %, aucun abattement supplémentaire */
          var ran = num(f.ran.value);
          res = Math.max(0, ran) / 12;
          det.push('Revenu net catégoriel de ' + esc(A.anneeRef) + ' retenu tel quel : ' + eur(res * 12) + ' par an, soit ' + eur(res) + ' par mois');
        }
        var plafM = plaf / 12, aah = Math.max(0, Math.min(A.max, plafM - res));
        if (cumul !== null) {
          var lim = Math.max(0, cumul - rg);
          if (lim < aah) { aah = lim; }
          det.push('Plafond de cumul en Ésat : rémunération garantie et AAH ensemble au plus ' + eur(cumul) + ' par mois' + (enf ? ' (majoré de ' + Math.round(A.esatCumulMaj * 100) + ' % avec un enfant à charge)' : '') + ', Smic au ' + esc(A.smicDate));
        }
        if (aah < 0.01) aah = 0;
        det.push('Plafond de ressources : ' + eur(plaf) + ' par an' + (enf ? ' (majoré de ' + Math.round(A.majEnfant * 100) + ' % par enfant)' : ''));
        if (tx === 50) det.push('Entre 50 et 79 %, l’AAH suppose aussi une restriction substantielle et durable d’accès à l’emploi, reconnue par la MDPH.');
        return result(aah ? eur(aah) : 'Pas d’AAH à verser', aah ? 'par mois (estimation)' : '',
          aah ? 'Vous pourriez toucher jusqu’à ' + eur(aah) + ' par mois, d’après vos réponses.' : 'D’après vos réponses, vos ressources dépassent le plafond : l’AAH ne serait pas versée.', '',
          '<ul><li>' + det.join('</li><li>') + '</li></ul>' +
          '<p class="mdh-note">Estimation simplifiée sur le barème officiel (AAH à taux plein : ' + eur(A.max) + ' par mois depuis le ' + esc(A.date) + '). Seuils calculés avec le Smic en vigueur au ' + esc(A.smicDate) + '. Le calcul de la CAF tient compte d’autres éléments (abattements particuliers, hospitalisation, déductions propres aux Ésat). Pour un chiffre plus précis, utilisez le <a href="https://www.mesdroitssociaux.gouv.fr/" rel="noopener" target="_blank">simulateur officiel mesdroitssociaux.gouv.fr</a>.</p>',
          '<a class="mdh-btn mdh-alt" href="/aah/">Comprendre le calcul</a><a class="mdh-btn mdh-alt" href="/dossier-mdph/">Préparer mon dossier pas à pas</a><a class="mdh-btn mdh-alt" href="/delais-mdph/">Délai de ma MDPH</a>');
      }
    }
  };

  document.querySelectorAll('[data-outil]').forEach(function (box) {
    var w = W[box.getAttribute('data-outil')]; if (!w) return;
    box.innerHTML = '<p class="mdh-lab mdh-priv"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/></svg>Calcul dans votre navigateur, rien n’est envoyé</p>' +
      '<div class="mdh-tgrid"><form class="mdh-f" novalidate>' + w.html() + '<button class="mdh-btn mdh-go" type="submit">Voir le résultat</button></form><div class="mdh-res" aria-live="polite"></div></div>';
    var f = box.querySelector('form'), out = box.querySelector('.mdh-res'), dep = f.querySelector('input[name=dep][type=hidden]'), finder = null;
    if (w.init) w.init(f);
    var run = function () { out.innerHTML = w.calc(f); };
    var tm; var later = function () { clearTimeout(tm); tm = setTimeout(run, 180); };
    f.addEventListener('submit', function (e) {
      e.preventDefault(); run();
      var r = out.getBoundingClientRect();
      if (r.top > window.innerHeight * 0.6 || r.top < 0) out.scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'});
    });
    f.addEventListener('change', run);
    f.addEventListener('input', later);
    if (dep && window.MDH_find) {
      var items = Object.keys(D).map(function (c) { return {n: D[c].n, c: c, g: D[c].g}; });
      var q = f.querySelector('#dep-q');
      finder = MDH_find(f.querySelector('.mdh-find-f'), items, function (it) { dep.value = it.c; run(); });
      q.addEventListener('input', function () { if (!q.value.trim() && dep.value) { dep.value = ''; run(); } });
    }
    out.addEventListener('click', function (e) {
      if (!e.target.closest('.mdh-restart')) return;
      f.reset(); if (dep) dep.value = ''; if (finder) finder.reset(); if (w.init) w.init(f); run();
      var first = f.querySelector('input:not([type=hidden])'); if (first) first.focus({preventScroll: true});
      box.scrollIntoView({block: 'start'});
    });
    run();
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
    var sb = document.querySelector('.mdh-sortbar');
    if (sb) sb.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var k = +b.getAttribute('data-k'), asc = b.getAttribute('data-dir') === 'asc', th = ths[k];
      th.setAttribute('aria-sort', asc ? 'descending' : 'ascending'); th.querySelector('button').click();
      sb.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    });
    var q2 = document.getElementById('q2'), res = document.getElementById('q-res');
    var norm = function (s) { return String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[-'\u2019().]/g, ' ').replace(/\bst\b/g, 'saint').replace(/\bste\b/g, 'sainte').replace(/\s+/g, ' ').trim(); };
    var filt = function (v) {
      v = norm(v); var n = 0, last = null, w = v.split(' ');
      Array.prototype.forEach.call(body.rows, function (r) {
        var k = r._k || (r._k = norm(r.getAttribute('data-nom')));
        var ok = !v || w.every(function (x) { return k.indexOf(x) >= 0; }) || k.split(' ').pop() === v;
        r.hidden = !ok; r.classList.toggle('mdh-hl', !!v && ok); if (ok) { n++; last = r; }
      });
      if (v && n === 1 && res) {
        var c = last.cells, a = c[1].querySelector('a'), g = parseFloat(c[2].getAttribute('data-v'));
        res.innerHTML = '<p class="mdh-fr-n"><b>' + esc(c[2].textContent) + '</b> mois</p><div><p class="mdh-fr-t"><strong>' + esc(c[1].textContent) + '</strong> : la MDPH met en moyenne <b>' + esc(c[2].textContent) + ' mois</b> à répondre (rang ' + esc(c[0].textContent) + '). ' +
          (g > 4 ? 'C’est plus que les 4 mois du refus implicite : déposez dès que votre dossier est complet.' : 'C’est sous la limite de 4 mois pour un dossier complet.') + '</p><p class="mdh-fr-l">' +
          (a ? '<a href="' + a.getAttribute('href') + '">Voir la page détaillée →</a>' : '') + '<a href="/outils/delai-reponse-mdph/">Calculer mes dates →</a></p></div>';
        res.hidden = false;
      } else if (res) {
        res.innerHTML = v && !n ? '<p class="mdh-fr-t">Aucun département trouvé. Essayez le numéro, par exemple 33.</p>' : '';
        res.hidden = !(v && !n);
      }
    };
    if (q2) q2.addEventListener('input', function () { filt(q2.value); });
    if (location.hash && q2) { var h = decodeURIComponent(location.hash.slice(1)); if (/^[0-9a-z]{2,3}$/i.test(h)) { q2.value = h; filt(h); } }
  }
})();
