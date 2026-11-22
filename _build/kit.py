"""Kit dossier MDPH (19 €) : page de vente, conditions de vente, page /merci/ et extrait gratuit.
Appelé par build.py UNIQUEMENT quand PRODUIT est un lien Stripe : sinon rien de ce module n'est produit.
Textes repris de _kit/page-de-vente.md, livraison selon _kit/livraison.md (option A).
Le PDF payant (_kit/kit-dossier-mdph-2026.pdf) n'est JAMAIS copié ici : il est hébergé hors GitHub (KIT_PDF_URL)."""
import os, json, shutil

SLUG = "kit-dossier-mdph"
CGV = "conditions-de-vente"
EXTRAIT = "/telechargements/extrait-kit-dossier-mdph.pdf"
PRIX = "19 €"
CONTACT = "contact@mes-droits-handicap.fr"
EDITEUR = "Louis Lardeux, entrepreneur individuel (micro-entreprise), SIREN 999 443 880, 63 rue Dostoïevski, A 307, 06560 Valbonne Sophia Antipolis"
MEDIATEUR = "désignation en cours ; en attendant, écrivez à contact@mes-droits-handicap.fr, réponse sous 48 h"   # obligatoire avant la mise en vente (art. L612-1 C. conso)
CGV_DATE = "2026-11-16"
APERCU = [(0, "Couverture", "Kit dossier MDPH, édition novembre 2026"), (1, "Mode d'emploi en 1 page", "Les 6 étapes du dépôt et le temps à prévoir"),
          (2, "Les pièces à réunir", "Checklists à cocher selon votre situation")]
MENTION = ("Guide d'information indépendant, ce n'est pas un service public. Le dépôt du dossier est gratuit auprès de votre MDPH et sur "
           '<a href="https://mdphenligne.cnsa.fr/" rel="noopener" target="_blank">mdphenligne.cnsa.fr</a>. '
           "Ce kit ne remplace pas le conseil d'un professionnel (assistante sociale, association, avocat).")
RENONCE = ("Je demande l'accès immédiat au kit et renonce à mon droit de rétractation dès que le téléchargement est disponible "
           "(art. L221-28 13° du code de la consommation). Le remboursement sous 14 jours reste valable.")

BENEF = [
    ("Gagner du temps", "Le mode d'emploi en 6 étapes vous dit quoi faire, dans quel ordre, et combien de temps prévoir."),
    ("Éviter les oublis qui retardent", "Un dossier incomplet décale le départ du délai de 4 mois. Les checklists, par situation, vous évitent les allers et retours."),
    ("Mettre des mots sur votre quotidien", "La méthode en 5 questions et les grilles vous aident à écrire la partie « vie quotidienne », celle que l'équipe d'évaluation lit pour comprendre vos besoins."),
    ("Préparer le rendez-vous médical", "Une fiche à remplir et à donner à votre médecin, pour que le certificat reflète ce que vous vivez."),
    ("Garder la main sur les délais", "Les délais réels de chaque MDPH, la règle des 4 mois, une fiche de suivi des relances et les dates de recours."),
]
SOMMAIRE = [
    ("Le mode d'emploi en 1 page", "Les 6 étapes du dépôt et le temps à prévoir."),
    ("Les checklists des pièces à cocher", "Pour tous, enfant, adulte, renouvellement, aggravation, avec où obtenir chaque document."),
    ("Le formulaire Cerfa 15692*01 section par section, de A à F", "Ce qu'on y met, les erreurs fréquentes, des formulations génériques à adapter."),
    ("Le projet de vie", "La méthode en 5 questions, deux grilles vierges et 4 exemples fictifs (enfant avec un trouble du spectre de l'autisme, salariée avec une maladie chronique, adulte sans emploi, personne de moins de 60 ans avec un handicap moteur)."),
    ("Le certificat médical (Cerfa 15695*01)", "Préparer la consultation et la fiche « ce que je veux que mon médecin sache »."),
    ("Calendrier et délais", "La règle des 4 mois, le tableau des délais moyens de chaque MDPH (CNSA, 2e trimestre 2026) et une fiche de suivi des relances."),
    ("Après la décision", "Lire la notification, les délais de recours (2 mois), le RAPO puis le tribunal, la contribution de 50 €, un modèle vierge de lettre de RAPO à compléter vous-même et une fiche des dates."),
    ("Le renouvellement", "Quand déposer, les droits sans limitation de durée, une fiche rappel."),
    ("Les contacts utiles", "Associations nationales et numéros vérifiés."),
    ("Vos prochaines étapes", "Votre plan d'action et les outils gratuits du site."),
]
POUR = ["Vous faites une première demande pour vous ou pour votre enfant.", "Vous renouvelez vos droits et voulez éviter une coupure.",
        "Votre situation a changé et vous voulez la décrire clairement.", "Vous aidez un proche à monter son dossier."]
FAQ = [
    ("Le dossier MDPH est-il payant ?", "Non. Le formulaire, le dépôt et l'instruction sont gratuits, en ligne comme sur papier. Le kit est un guide pratique facultatif pour vous aider à le préparer."),
    ("Le kit augmente-t-il mes chances d'obtenir une aide ?", "Personne ne peut le promettre : seule la CDAPH décide, au vu de votre situation. Le kit vous aide à déposer un dossier complet et à décrire clairement votre quotidien, ce qui évite des retards."),
    ("Est-ce que vous remplissez le dossier pour moi ?", "Non. Le kit contient des explications et des modèles vierges que vous complétez vous-même. Pour une aide personnalisée, adressez-vous à votre MDPH, à une association ou à un point-justice."),
    ("Comment je reçois le kit ?", "Juste après le paiement, vous arrivez sur une page de téléchargement. Enregistrez le PDF sur votre appareil. Stripe vous envoie aussi un reçu par e-mail."),
    ("Je n'ai pas d'imprimante, ça marche quand même ?", "Oui. Vous pouvez lire le kit sur écran et remplir les grilles sur papier libre, ou faire imprimer seulement les pages utiles."),
    ("Les informations sont-elles à jour ?", "Chaque règle, montant et délai a été vérifié sur les sites officiels (service-public.gouv.fr, monparcourshandicap.gouv.fr, cnsa.fr, legifrance.gouv.fr) le 15 novembre 2026. Les sources et leurs dates sont listées à la fin du kit."),
    ("Et si le kit ne me convient pas ?", f"Écrivez à {CONTACT} dans les 14 jours suivant l'achat : nous vous remboursons, sans justification."),
]


def actif(produit):
    return bool(produit) and str(produit).startswith("https://") and "stripe.com" in str(produit)


def apercus(root, out):
    """Vignettes webp des 3 premières pages de l'EXTRAIT GRATUIT (jamais du kit payant), dans docs/kit-dossier-mdph/."""
    import fitz
    from PIL import Image
    src = os.path.join(root, "_kit", "version-gratuite-extrait.pdf")
    d = os.path.join(out, SLUG)
    os.makedirs(d, exist_ok=True)
    doc = fitz.open(src)
    for i, _, _ in APERCU:
        pix = doc[i].get_pixmap(dpi=110)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        im = im.resize((620, round(620 * pix.height / pix.width)), Image.LANCZOS)
        im.save(os.path.join(d, f"apercu-{i + 1}.webp"), "WEBP", quality=80, method=6)
    return 620, round(620 * pix.height / pix.width)


def extrait(root, out):
    os.makedirs(os.path.join(out, "telechargements"), exist_ok=True)
    shutil.copy(os.path.join(root, "_kit", "version-gratuite-extrait.pdf"), os.path.join(out, EXTRAIT.strip("/")))


def page_vente(B, wh):
    E = B.E
    w, h = wh
    img = lambda i, cls="", prio=False: (f'<img src="/{SLUG}/apercu-{i + 1}.webp" width="{w}" height="{h}" alt="Aperçu de la page : {E(APERCU[i][1])}"'
                                         f'{" class=" + chr(34) + cls + chr(34) if cls else ""}{" fetchpriority=" + chr(34) + "high" + chr(34) if prio else " loading=" + chr(34) + "lazy" + chr(34)}>')
    benef = "".join(f"<li><b>{E(t)}</b><span>{E(d)}</span></li>" for t, d in BENEF)
    som = "".join(f"<li><b>{E(t)}</b><span>{E(d)}</span></li>" for t, d in SOMMAIRE)
    pour = "".join(f"<li>{E(x)}</li>" for x in POUR)
    pages = "".join(f'<li><figure>{img(i)}<figcaption><b>{E(t)}</b><br>{E(d)}</figcaption></figure></li>' for i, t, d in APERCU)
    outils = "".join(f'<li><a href="{B.url(v[0])}">{E(v[2])}</a></li>' for v in B.OUTILS.values())
    outils += '<li><a href="/delais-mdph/">Délais des MDPH par département</a></li><li><a href="/dossier-mdph/">Remplir le dossier MDPH</a></li>'
    form = lambda n: (f'<form class="mdh-kform" action="{E(B.PRODUIT)}" method="get" data-href="{E(B.PRODUIT)}">'
                      f'<label class="mdh-kchk" for="k-renonce{n}"><input type="checkbox" id="k-renonce{n}" required aria-describedby="k-msg{n}"><span>{E(RENONCE)}</span></label>'
                      f'<p class="mdh-kmsg" id="k-msg{n}" role="alert" hidden>Cochez la case ci-dessus pour continuer vers le paiement.</p>'
                      f'<button class="mdh-btn mdh-kpay" type="submit">Payer {PRIX} et télécharger le kit</button></form>')
    body = f"""<div class="mdh-w">
{B.crumbs([("Kit dossier MDPH", None)])}
<div class="mdh-kh">
<div><span class="mdh-badge">Guide pratique · édition novembre 2026</span>
<h1>Kit dossier MDPH 2026 : préparez votre demande pas à pas</h1>
<p class="mdh-chapo">Checklists à cocher, Cerfa expliqué, grilles et modèles vierges : tout pour déposer un dossier complet du premier coup.</p>
<div class="mdh-kbuy"><p class="mdh-kbuy-p">{PRIX}<small>TTC · PDF A4 de 26 pages · paiement unique</small></p>
{form(1)}
<p class="mdh-ksous">Paiement sécurisé par Stripe · téléchargement immédiat · remboursé sous 14 jours sur simple demande · <a href="/{CGV}/">Conditions de vente</a></p></div>
<p class="mdh-kext0">Pas encore sûr ? <a href="{EXTRAIT}">Lire l'extrait gratuit</a> (4 pages).</p>
<p class="mdh-kmen">{MENTION}</p>
</div>
<div class="mdh-kvis"><div class="mdh-kstack">{img(1, "mdh-kback")}{img(0, "mdh-kfront", True)}</div>
<div class="mdh-float mdh-float-a" aria-hidden="true"><p class="mdh-lab">Édition 2026</p><p class="mdh-fl-n"><b>26</b> pages</p><p class="mdh-fl-s">sources vérifiées le 15/11/2026</p></div>
<div class="mdh-float mdh-float-b" aria-hidden="true"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#4f8a7b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/></svg>Rien n'est collecté</div>
</div>
</div>
<section class="mdh-sec" aria-labelledby="k-apport"><h2 id="k-apport">Ce que le kit vous apporte</h2>
<ul class="mdh-kben">{benef}</ul></section>
<section class="mdh-sec" aria-labelledby="k-contenu"><div class="mdh-kcols">
<div><h2 id="k-contenu">Ce qu'il contient</h2>
<ol class="mdh-steps">{som}</ol>
<p class="mdh-kplus">Plus : la liste des sources officielles, chacune avec sa date de vérification.</p></div>
<aside class="mdh-kpour" aria-labelledby="k-pour"><h3 id="k-pour">Pour qui ?</h3><ul>{pour}</ul></aside>
</div></section>
<section class="mdh-sec" aria-labelledby="k-apercu"><h2 id="k-apercu">Aperçu des pages</h2>
<p>Ces pages viennent de l'extrait gratuit : le mode d'emploi et les checklists sont aussi dans le kit complet, à côté du Cerfa expliqué, des grilles du projet de vie, de la fiche pour votre médecin et du modèle vierge de recours.</p>
<ul class="mdh-kpages">{pages}</ul></section>
<section class="mdh-sec" aria-labelledby="k-nest"><h2 id="k-nest">Ce que le kit n'est pas</h2>
<div class="mdh-knot"><p>Le kit est de l'information générale et des modèles vierges que vous complétez vous-même. Il n'étudie pas votre situation personnelle, ne rédige pas de courrier à votre place et ne peut pas prédire la décision : c'est la commission de la MDPH (CDAPH) qui décide.</p>
<p>Pour un accompagnement personnalisé, l'accueil de votre MDPH, une association ou un point-justice peuvent vous aider, souvent gratuitement. Leurs coordonnées sont dans le kit.</p></div>
<h3>Vos données</h3>
<p>Rien n'est collecté. Le kit est un PDF : vous le remplissez à la main ou sur votre ordinateur, et rien ne nous est envoyé. Le paiement est traité par Stripe ; nous ne voyons ni votre numéro de carte ni aucune information de santé.</p></section>
<section class="mdh-sec" aria-labelledby="k-urg"><h2 id="k-urg">Pourquoi le préparer maintenant</h2>
<ul class="mdh-kben"><li><b>Le délai ne commence qu'au dossier complet</b><span>Une pièce manquante et la MDPH vous la réclame : le traitement attend. Les MDPH mettent en moyenne autour de 4 à 5 mois pour une demande d'adulte (baromètre CNSA) : <a href="/delais-mdph/">voir le délai de votre département</a>.</span></li>
<li><b>Sans réponse au bout de 4 mois, c'est un refus</b><span>Le silence de la MDPH pendant 4 mois vaut rejet. Un dossier clair et complet dès le premier dépôt vous évite de repartir de zéro.</span></li>
<li><b>Un certificat médical a une durée de validité</b><span>Il doit dater de moins d'un an au dépôt : préparer le reste du dossier en parallèle évite de devoir le refaire.</span></li></ul></section>
<section class="mdh-sec" aria-labelledby="prix-t"><h2 id="prix-t">Obtenir le kit</h2>
<div class="mdh-kprix" id="prix">
<div class="mdh-kprix-a"><p class="mdh-lab">Kit dossier MDPH 2026</p>
<p class="mdh-kprix-n">{PRIX}<small>TTC</small></p><p class="mdh-kprix-s">Paiement unique, sans abonnement</p>
<ul><li>Téléchargement immédiat après le paiement (PDF A4, 26 pages, imprimable)</li>
<li>Mises à jour de l'édition 2026 offertes : si une règle change, écrivez-nous et nous vous envoyons la version corrigée</li>
<li>Remboursé sous 14 jours sur simple demande, sans justification</li></ul></div>
<div class="mdh-kprix-b">
{form(2)}
<p class="mdh-ksous">Paiement sécurisé par Stripe. TVA non applicable, article 293 B du CGI. <a href="/{CGV}/">Conditions de vente</a></p>
<p class="mdh-kext">Pas encore sûr ? <a href="{EXTRAIT}">Téléchargez l'extrait gratuit</a> (4 pages : mode d'emploi et checklists).</p>
</div></div></section>
{B.faq_html(FAQ)}
<section class="mdh-next" aria-labelledby="suite"><h2 id="suite">Les outils et guides gratuits</h2><ul>{outils}</ul></section>
<p class="mdh-kfoot">Guide d'information indépendant, ce n'est pas un service public ; le dépôt du dossier est gratuit auprès de votre MDPH et sur mdphenligne.cnsa.fr ; ce kit ne remplace pas le conseil d'un professionnel (assistante sociale, association, avocat). Édité par Louis Lardeux, entrepreneur individuel, SIREN 999 443 880.</p>
</div>
<script>
document.querySelectorAll('.mdh-kform').forEach(function (f) {{
  var c = f.querySelector('input[type=checkbox]'), m = f.querySelector('.mdh-kmsg'), l = c.parentNode;
  var maj = function () {{ f.classList.toggle('ok', c.checked); if (c.checked) {{ m.hidden = true; l.classList.remove('mdh-kerr'); }} }};
  c.addEventListener('change', maj);
  c.addEventListener('invalid', function (e) {{ e.preventDefault(); m.hidden = false; l.classList.add('mdh-kerr'); c.focus(); }});
  f.addEventListener('submit', function (e) {{ e.preventDefault(); if (!c.checked) {{ c.dispatchEvent(new Event('invalid')); return; }} location.href = f.getAttribute('data-href'); }});
  maj();
}});
</script>"""
    path = f"/{SLUG}/"
    D = B.DOMAIN
    schema = [{"@context": "https://schema.org", "@type": "Product", "name": "Kit dossier MDPH 2026", "description": "Guide pratique PDF de 26 pages pour préparer une demande à la MDPH : checklists des pièces, Cerfa 15692 expliqué, grilles du projet de vie, fiche pour le médecin, délais et modèle vierge de recours.",
               "image": f"{D}/{SLUG}/apercu-1.webp", "brand": {"@type": "Brand", "name": B.SITE},
               "offers": {"@type": "Offer", "price": "19.00", "priceCurrency": "EUR", "availability": "https://schema.org/InStock", "url": D + path, "seller": {"@type": "Person", "name": B.AUTEUR}}},
              B.bc_schema([("Kit dossier MDPH", path)]), B.faq_schema(FAQ)]
    return path, B.page("Kit dossier MDPH 2026 : checklists, Cerfa et modèles", "Préparez votre dossier MDPH pas à pas : checklists des pièces, Cerfa expliqué, projet de vie, délais et recours. PDF de 26 pages, 19 €, remboursable.",
                        path, body, schema, "demarches", "kit", None, "contenu", None, extra_head=B.KIT_STYLE)


def page_cgv(B):
    E = B.E
    mail = f'<a href="mailto:{CONTACT}">{CONTACT}</a>'
    b = f"""<p>Ces conditions s'appliquent à l'achat du <a href="/{SLUG}/">Kit dossier MDPH</a> sur mes-droits-handicap.fr. Version du {B.date_fr(CGV_DATE)}.</p>
<h2>Le produit</h2><p>Le Kit dossier MDPH est un document numérique (PDF) d'information générale sur la demande à la MDPH, avec des modèles vierges à compléter par l'acheteur. Il ne constitue ni une consultation juridique ni la rédaction d'un acte pour autrui. Les démarches auprès de la MDPH sont gratuites ; seule la CDAPH décide de l'attribution des droits.</p>
<h2>Prix et paiement</h2><p>{PRIX} TTC, paiement unique sans abonnement, par carte via Stripe. TVA non applicable, article 293 B du CGI.</p>
<h2>Accès et droit de rétractation</h2><p>Le kit est téléchargeable immédiatement après le paiement. En cochant la case prévue avant le paiement, vous demandez cet accès immédiat et reconnaissez perdre votre droit de rétractation dès que le téléchargement est disponible (article L221-28 13° du code de la consommation). Une confirmation vous est adressée par e-mail.</p>
<h2>Remboursement</h2><p>Si le kit ne vous convient pas, écrivez à {mail} dans les 14 jours suivant l'achat : nous vous remboursons, sans justification.</p>
<h2>Usage</h2><p>Le kit est réservé à un usage personnel. Merci de ne pas le diffuser.</p>
<h2>Vendeur</h2><p>{EDITEUR}. Contact : {mail}.</p>
<h2>Médiation de la consommation</h2><p>En cas de litige non résolu, vous pouvez recourir gratuitement à un médiateur de la consommation. Médiateur : {E(MEDIATEUR)}.</p>"""
    h1 = "Conditions de vente du Kit dossier MDPH"
    path = f"/{CGV}/"
    body = f'<div class="mdh-w mdh-prose">{B.crumbs([("Conditions de vente", None)])}<h1>{E(h1)}</h1>{b}</div>'
    return path, B.page("Conditions de vente | Mes droits handicap", "Conditions de vente du Kit dossier MDPH : prix, paiement, accès immédiat, remboursement sous 14 jours, vendeur et médiation.",
                        path, body, [B.bc_schema([("Conditions de vente", path)])], "accueil", None, None, "contenu", None, extra_head=B.KIT_STYLE)


def page_merci(B):
    pdf = B.KIT_PDF_URL if B.KIT_PDF_URL and str(B.KIT_PDF_URL).startswith("https://") else None
    if pdf:
        livr = (f'<p class="mdh-btns"><a id="dl" class="mdh-btn" href="#" download>Télécharger le Kit dossier MDPH (PDF, 26 pages)</a>'
                f'<button class="mdh-btn mdh-alt" type="button" onclick="window.print()">Enregistrer cette confirmation</button></p>'
                f'<p>Enregistrez le fichier sur votre appareil. Un reçu vous a été envoyé par e-mail. Un souci de téléchargement ? Écrivez à <a href="mailto:{CONTACT}">{CONTACT}</a> avec l\'adresse e-mail utilisée pour le paiement.</p>')
    else:
        livr = (f'<p class="mdh-kmerci-t">Votre kit vous est envoyé par e-mail sous 24 h</p>'
                f'<p>Il arrive à l\'adresse utilisée pour le paiement, en pièce jointe (PDF, 26 pages). Un reçu vous a déjà été envoyé par Stripe. Rien reçu après 24 h ? Regardez dans les indésirables, puis écrivez à <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>'
                f'<p class="mdh-btns"><button class="mdh-btn mdh-alt" type="button" onclick="window.print()">Enregistrer cette confirmation</button></p>')
    body = f"""<div class="mdh-w mdh-prose">
<div id="ok" class="mdh-kok" hidden>
<span class="mdh-badge mdh-b-ok">Paiement reçu</span>
<h1>{"Merci, votre kit est prêt" if pdf else "Merci pour votre achat"}</h1>
<div class="mdh-kmerci"><div class="mdh-kprix-a">{livr}
<p class="mdh-kconf">Vous avez demandé l'accès immédiat au kit et reconnu perdre votre droit de rétractation (art. L221-28 13° du code de la consommation). Remboursement sous 14 jours sur simple demande à {CONTACT}.</p></div></div>
<p>En attendant, les outils gratuits du site restent à votre disposition : <a href="/outils/delai-reponse-mdph/">date de refus implicite</a>, <a href="/outils/fin-de-droits-mdph/">calendrier de renouvellement</a>, <a href="/delais-mdph/">délai de votre MDPH</a>.</p>
</div>
<div id="ko"><h2>Cette page s'affiche après un achat</h2><p><a href="/{SLUG}/">Voir le Kit dossier MDPH</a>.</p></div>
</div>
<script>
(function () {{
  var K = 'mdh-kit', U = {json.dumps(pdf)};
  var get = function () {{ try {{ return JSON.parse(localStorage.getItem(K) || 'null'); }} catch (e) {{ return null; }} }};
  var set = function (v) {{ try {{ localStorage.setItem(K, JSON.stringify(v)); }} catch (e) {{}} }};
  // Accès vérifié par le serveur (VPS, ~/Documents/paiements-sites/server.py) : session Stripe payée, venue du lien du kit.
  var API = 'https://187-124-173-12.sslip.io/pay/verifier?p=kit';
  var s = new URLSearchParams(location.search).get('s') || '', m = get();
  var neuf = /^cs_(live|test)_/.test(s), sess = neuf ? s : (m && m.s), tok = m && m.s === sess ? m.k : '';
  if (!sess) return;
  fetch(API + '&s=' + encodeURIComponent(sess) + (tok ? '&t=' + tok : ''))
    .then(function (r) {{ return r.json(); }})
    .catch(function () {{ return {{ok: false}}; }})
    .then(function (r) {{
      if (!r.ok) {{ document.getElementById('ko').innerHTML = '<h2>Paiement non retrouvé</h2><p>Si vous venez de payer, rechargez la page dans une minute. Sinon, écrivez à <a href="mailto:{CONTACT}">{CONTACT}</a> avec l’adresse e-mail utilisée pour le paiement.</p>'; return; }}
      set({{s: sess, k: r.t, d: Date.now()}}); if (neuf) history.replaceState(null, '', '/merci/');
      document.getElementById('ko').hidden = true;
      document.getElementById('ok').hidden = false;
      var dl = document.getElementById('dl'); if (dl && U) dl.href = U + '?s=' + encodeURIComponent(sess) + '&t=' + r.t;
      if (neuf && window.goatcounter) {{ try {{ goatcounter.count({{path: 'achat-kit-mdph', event: true}}); }} catch (e) {{}} }}
    }});
}})();
</script>"""
    return "/merci/", B.page("Merci pour votre achat | Mes droits handicap", "Téléchargement du Kit dossier MDPH après le paiement.", "/merci/", body, [], "accueil", None, None, "systeme", "noindex", extra_head=B.KIT_STYLE)
