#!/usr/bin/env python3
"""Générateur statique de mes-droits-handicap.fr : contenu/*.json + _data/*.json -> docs/ (GitHub Pages)."""
import json, glob, os, re, html, shutil, sys, hashlib, csv, io, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import departements as DP
import graph as G
import kit as KIT
import smic as SM   # Smic et seuils dépendants : un seul endroit (_build/smic.py), à mettre à jour au 01/12/2026 dès parution du décret

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("MDH_OUT") or os.path.join(ROOT, "docs")   # MDH_OUT : dossier de sortie temporaire pour les tests
DOMAIN = "https://mes-droits-handicap.fr"
SITE = "Mes droits handicap"
LANCEMENT = "2026-11-15"
MAJ_DONNEES = "2026-11-15"          # date du dernier relevé des sources (donnees.py)
GOATCOUNTER = "https://mesdroitshandicap.goatcounter.com/count"                    # ex. "https://mesdroitshandicap.goatcounter.com/count" ; vide = aucun compteur
PRODUIT = "https://buy.stripe.com/7sY7sMgiC9mlbV95q4ebu00"                      # lien Stripe du « Kit dossier MDPH, 19 € » (https://buy.stripe.com/...) ; None = rien n'est affiché (relecture avocat)
KIT_PDF_URL = "https://187-124-173-12.sslip.io/pay/kit"                  # lien du PDF payant hébergé HORS GitHub (Drive, R2) ; None = /merci/ annonce un envoi par e-mail sous 24 h
AUTEUR = "Louis Lardeux"
INDEXNOW = "50f1cb133c1a8499537462019c5a94c2"             # clé IndexNow, servie à la racine dans <clé>.txt
# Microsoft Clarity, PRÉPARÉ MAIS INACTIF. None = rien n'est chargé et la confidentialité dit qu'il n'y a aucune mesure d'audience.
# Pour l'activer : mettre l'ID du projet (chaîne), régler le masquage sur « Strict » dans le tableau de bord Clarity,
# vérifier la doc de l'API de consentement (consentv2), puis rebuild. Chargé seulement sur les pages de contenu,
# jamais sur les outils, et seulement après un clic sur « Accepter » dans le bandeau.
CLARITY_ID = None
# Pages réellement modifiées (date de dernière modification du sitemap et du JSON-LD). Ne mettre une date que si la page a changé.
MODIFS = {"/": "2026-11-22", "/delais-mdph/": "2026-11-19", "/outils/": "2026-11-19", "/dossier-mdph-trop-long/": "2026-11-19", "/recours-mdph/": "2026-11-19",
          "/mentions-legales/": "2026-11-19", "/confidentialite/": "2026-11-19", "/projet-de-vie-mdph/": "2026-11-22"}
MODIF_DEPS = "2026-11-19"           # les 20 pages départements (accord « de l'Hérault », intertitres, doublon supprimé)

E = lambda s: html.escape(str(s if s is not None else ""), quote=True)
date_fr = lambda iso: dt.date.fromisoformat(iso).strftime("%d/%m/%Y")

# --------------------------------------------------------------------------- registre des pages
GUIDES = {  # slug -> (libellé court, image, outil associé)
    "dossier-mdph": ("Remplir le dossier MDPH (Cerfa 15692)", "demarches", "delai"),
    "projet-de-vie-mdph": ("Le projet de vie, avec exemples", "accueil", "delai"),
    "certificat-medical-mdph": ("Le certificat médical (Cerfa 15695)", "demarches", "delai"),
    "dossier-mdph-trop-long": ("Dossier sans réponse : que faire", "accueil", "delai"),
    "recours-mdph": ("Contester une décision", "demarches", "delai"),
    "renouvellement-mdph": ("Renouveler ses droits", "accueil", "fin"),
    "aah": ("AAH : montant et cumul avec un salaire", "travail", "aah"),
    "rqth": ("RQTH : les avantages", "travail", "aah"),
    "rqth-delai-obtention": ("RQTH : délai pour l'obtenir", "demarches", "delai"),
    "rqth-aides-financieres": ("RQTH : aides financières et CPF", "travail", "aah"),
    "aeeh": ("AEEH et compléments", "enfant", "aeeh"),
    "pch": ("PCH : ce qu'elle finance", "domicile", "aah"),
    "carte-mobilite-inclusion": ("Carte mobilité inclusion", "mobilite", "delai"),
}
OUTILS = {  # clé -> (slug, libellé du bouton, titre court, description courte)
    "aah": ("outils/simulateur-aah", "Estimer mon AAH en 1 minute", "Simulateur AAH", "Votre AAH estimée selon vos ressources ou votre salaire."),
    "aeeh": ("outils/calcul-aeeh", "Calculer l'AEEH de mon enfant", "Calcul de l'AEEH", "Montant de base et complément selon vos frais et votre temps de travail."),
    "delai": ("outils/delai-reponse-mdph", "Calculer mes dates (4 mois, recours)", "Date de refus implicite", "4 mois sans réponse : la date exacte et vos délais de recours."),
    "fin": ("outils/fin-de-droits-mdph", "Calculer ma date de renouvellement", "Calendrier de renouvellement", "Quand redéposer pour éviter une coupure de vos droits."),
}
ALT = {
    "accueil": "Une mère et son fils en fauteuil roulant trient des papiers à la table de la cuisine, un ordinateur ouvert entre eux",
    "enfant": "Un père aide sa fille, qui porte des appareils auditifs, à faire ses devoirs",
    "travail": "Un homme avec une prothèse de jambe travaille à un bureau debout dans un open space",
    "domicile": "Une aide à domicile prépare des légumes avec une femme qui se déplace avec un déambulateur",
    "demarches": "Une main remplit un formulaire papier à côté d'un ordinateur, une canne blanche posée contre la table",
    "mobilite": "Une jeune femme en fauteuil roulant monte dans un tramway par une rampe d'accès",
}
CSS = open(os.path.join(ROOT, "_build", "style.css"), encoding="utf-8").read()
SITE_JS = open(os.path.join(ROOT, "_build", "site.js"), encoding="utf-8").read()
ASSET_V = hashlib.md5((CSS + SITE_JS + open(os.path.join(ROOT, "_build", "outils.js"), encoding="utf-8").read()).encode()).hexdigest()[:8]
KIT_STYLE = "<style>" + open(os.path.join(ROOT, "_build", "kit.css"), encoding="utf-8").read() + "</style>"   # pages du kit seulement
SLUGS = set(GUIDES) | {v[0] for v in OUTILS.values()} | {"outils", "delais-mdph", "a-propos", "methode-et-sources", "mentions-legales", "confidentialite"}


def inline(s):
    s = E(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

    def lien(m):
        t, cible = m.group(1), m.group(2).strip("/")
        if cible in SLUGS or cible.startswith("delais-mdph/"): return f'<a href="/{cible}/">{t}</a>'
        if cible.startswith("https://"): return f'<a href="{cible}" rel="noopener" target="_blank">{t}</a>'
        return t
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lien, s)


def strip(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", str(s or ""))
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)


def url(slug):
    return "/" if not slug else f"/{slug}/"


LOGO = ('<svg width="40" height="40" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="24" fill="#1f3b63"/>'
        '<path d="M13.5 31.5c4-9 8-13 10.5-13s6.5 4 10.5 13" fill="none" stroke="#e8b06a" stroke-width="4.2" stroke-linecap="round"/>'
        '<circle cx="24" cy="12.8" r="3.5" fill="#fbf7f0"/><path d="M13 36.5h22" stroke="#fbf7f0" stroke-width="2.8" stroke-linecap="round" opacity=".8"/></svg>')


def header(actif=None):
    items = [("delais-mdph", "Délais des MDPH"), ("outils", "Outils"), ("#guides", "Guides"), ("a-propos", "À propos")]
    lis = ""
    for s, t in items:
        href = "/" + s if s.startswith("#") else url(s)
        cur = ' aria-current="page"' if actif == s else ""
        lis += f'<li><a href="{href}"{cur}>{E(t)}</a></li>'
    lis += f'<li><a class="mdh-nav-cta" href="/outils/simulateur-aah/">Estimer mon AAH</a></li>'
    if KIT.actif(PRODUIT):  # 22/11 : l'offre payante doit se voir partout (retour de Louis : « je n'ai même pas trouvé comment payer »)
        lis += f'<li class="mdh-nav-kitli"><a class="mdh-nav-cta mdh-nav-kit" href="/{KIT.SLUG}/"{" aria-current=" + chr(34) + "page" + chr(34) if actif == "kit" else ""}>Le kit, 19 €</a></li>'
    return (f'<header class="mdh-top"><div class="mdh-w mdh-bar"><a class="mdh-logo" href="/">{LOGO}'
            f'<span><b>mes droits <i>handicap</i></b><small>Site d\'information indépendant</small></span></a>'
            f'<button class="mdh-menu" type="button" aria-expanded="false" aria-controls="mdh-nav"><span aria-hidden="true"></span>Menu</button>'
            f'<nav class="mdh-nav" id="mdh-nav" aria-label="Menu principal"><ul>{lis}</ul></nav></div></header>')


def footer():
    g = "".join(f'<li><a href="{url(s)}">{E(v[0])}</a></li>' for s, v in GUIDES.items() if s in CONTENUS)
    o = "".join(f'<li><a href="{url(v[0])}">{E(v[2])}</a></li>' for v in OUTILS.values())
    return (f'<footer class="mdh-foot"><div class="mdh-w"><div class="mdh-fcols">'
            f'<div><h2>mes-droits-handicap.fr</h2><p>Des explications claires sur l\'AAH, la PCH, l\'AEEH, la RQTH et les délais des MDPH, avec les chiffres officiels et leurs sources.</p>'
            f'<p>Rédigé et vérifié par {AUTEUR}. Ce site n\'est rattaché à aucune MDPH ni à aucune administration : votre dossier se dépose auprès de votre MDPH ou sur <a href="https://mdphenligne.cnsa.fr/" rel="noopener" target="_blank">mdphenligne.cnsa.fr</a>.</p></div>'
            f'<div><h2>Les délais</h2><ul><li><a href="/delais-mdph/">Classement des MDPH en 2026</a></li><li><a href="/methode-et-sources/">D\'où viennent les chiffres</a></li></ul><h2 style="margin-top:18px"><a href="/outils/">Outils</a></h2><ul>{o}</ul></div>'
            f'<div><h2>Guides</h2><ul>{g}</ul></div>'
            f'<div><h2>Le site</h2><ul><li><a href="/a-propos/">À propos et financement</a></li><li><a href="/methode-et-sources/">Méthode et sources</a></li>'
            f'<li><a href="/mentions-legales/">Mentions légales</a></li><li><a href="/confidentialite/">Confidentialité</a></li>'
            + (f'<li><a href="/{KIT.SLUG}/">Kit dossier MDPH</a></li><li><a href="/{KIT.CGV}/">Conditions de vente</a></li>' if KIT.actif(PRODUIT) else "") + '</ul></div>'
            f'</div>{aide_urgente(pied=True)}</div></footer>')


URGENCES = [  # intitulés vérifiés le 19/11/2026 (service-public F33954 vérifiée le 25/08/2026, solidarites.gouv.fr, 3114.fr, allo119.gouv.fr)
    ("15", "Samu, urgence médicale", "gratuit, 24 h/24"),
    ("114", "urgence par SMS, application ou internet pour les personnes sourdes, malentendantes ou aphasiques", "gratuit, 24 h/24"),
    ("3114", "numéro national de prévention du suicide", "gratuit, 24 h/24 et 7 j/7"),
    ("3133", "maltraitances envers les personnes âgées et les adultes en situation de handicap (il remplace le 3977 depuis le 1er mars 2026)", "gratuit, tous les jours de 9 h à 20 h"),
    ("119", "Allô enfance en danger", "gratuit et confidentiel, 24 h/24"),
]


def aide_urgente(pied=False):
    """Encart sobre « urgence ou détresse » : dans le pied de page de tout le site, et plus visible sur les guides concernés."""
    lis = "".join(f'<li><a href="tel:{n}"><b>{n}</b></a> {E(t)} <span>({E(h)})</span></li>' for n, t, h in URGENCES)
    src = ('<p class="mdh-src">Sources : <a href="https://www.service-public.gouv.fr/particuliers/vosdroits/F33954" rel="noopener" target="_blank">service-public.gouv.fr, numéros d\'urgence et d\'écoute</a> (vérifié le 25/08/2026) ; '
           '<a href="https://solidarites.gouv.fr/3133-maltraitances" rel="noopener" target="_blank">solidarites.gouv.fr, le 3133</a> (mis à jour le 01/06/2026), consultés le 19/11/2026.</p>')
    if pied:
        return f'<aside class="mdh-sos mdh-sos-pied" aria-label="Urgence ou détresse"><p><b>Urgence ou détresse ?</b> Ces numéros sont gratuits :</p><ul>{lis}</ul></aside>'
    return (f'<aside class="mdh-sos" aria-labelledby="sos-t"><p class="mdh-lab" id="sos-t">Urgence ou détresse</p><p>L\'attente d\'une décision ou un refus peuvent peser très lourd. Si vous ou un proche êtes en danger, ou si vous n\'en pouvez plus, appelez :</p>'
            f'<ul>{lis}</ul>{src}</aside>')


def trust(nb_src=None, maj=MAJ_DONNEES, outil=False, lieu=None):
    li = [f"<li>Données officielles {'CNSA, CAF et Insee ' + lieu if lieu else 'CNSA, CAF et service-public'}, vérifiées le {date_fr(maj)}</li>"]
    if nb_src: li.append(f"<li>{nb_src} sources officielles citées</li>")
    li.append('<li>Gratuit, sans inscription, <a href="/methode-et-sources/">méthode et sources publiées</a></li>')
    if outil: li.append("<li>Vos réponses restent sur votre appareil, rien n'est enregistré</li>")
    return '<ul class="mdh-trust">' + "".join(li) + "</ul>"


def urgences(keys):
    """Repères de délais réels (règles officielles), affichés en badges."""
    U = {
        "delai": ("Comptez " + DP.fr(DP.nat("global")) + " mois", f"Délai moyen national des MDPH au {DP.tlab(DP.DERNIER)}. Déposez dès que votre dossier est complet.", "/delais-mdph/", "Voir le délai de ma MDPH"),
        "4mois": ("4 mois", "Sans réponse au bout de 4 mois, la demande est considérée comme refusée (refus implicite).", "/outils/delai-reponse-mdph/", "Calculer ma date"),
        "2mois": ("2 mois", "Pour contester une décision : recours amiable dans les 2 mois qui suivent la notification.", "/recours-mdph/", "Contester une décision"),
        "6mois": ("6 mois avant", "Renouvellement : déposez 6 mois avant la fin de vos droits, comme le recommandent les sites officiels, pour éviter une coupure.", "/outils/fin-de-droits-mdph/", "Calculer ma date de renouvellement"),
    }
    return '<ul class="mdh-urg">' + "".join(f'<li><b>{E(U[k][0])}</b><span>{E(U[k][1])}</span><a href="{U[k][2]}">{E(U[k][3])} →</a></li>' for k in keys) + "</ul>"


def insecables(h):
    """Espace insécable avant : ; ? ! dans le texte visible (hors balises et scripts) : la ponctuation ne tombe plus en début de ligne."""
    parts = re.split(r"(<script.*?</script>|<[^>]+>)", h, flags=re.S)
    return "".join(x if x.startswith("<") else re.sub(r" ([:;?!])(?=\s|$|<|\u00a0)", "\u00a0\\1", x) for x in parts)


def page(title, desc, path, body, schema, image="accueil", actif=None, sticky=None, kind="contenu", robots=None, extra_head=""):
    canon = DOMAIN + path
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schema)
    st = ""
    if KIT.actif(PRODUIT) and kind in ("contenu", "classement", "outil") and path not in (f"/{KIT.SLUG}/", f"/{KIT.CGV}/", "/merci/", "/mentions-legales/", "/confidentialite/"):
        st = STICKY_KIT
    elif sticky:
        s_slug, s_txt = sticky
        st = f'<div class="mdh-sticky"><a href="{url(s_slug)}">{E(s_txt)}</a></div>'
    gc = f'<script data-goatcounter="{GOATCOUNTER}" async src="//gc.zgo.at/count.js"></script>' if GOATCOUNTER and kind == "contenu" else ""
    cl = clarity_html() if CLARITY_ID and kind == "contenu" else ""
    js = f'<script src="/outils.js?v={ASSET_V}" defer></script>' if kind in ("outil", "classement") else ""
    rob = f'<meta name="robots" content="{robots}">' if robots else ""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{rob}<link rel="canonical" href="{canon}">
<meta property="og:type" content="{'website' if path == '/' else 'article'}">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{DOMAIN}/img/{image}.jpg">
<meta property="og:image:width" content="1600"><meta property="og:image:height" content="1067">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f8f5ef">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/lexend-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
<script>document.documentElement.classList.add("js")</script>
<link rel="stylesheet" href="/style.css?v={ASSET_V}">
<script src="/site.js?v={ASSET_V}" defer></script>
{ld}{js}{gc}{extra_head}
</head>
<body{' data-clarity-mask="true"' if cl else ''}>
<a class="mdh-skip" href="#contenu">Aller au contenu</a>
{header(actif)}
<main id="contenu">
{insecables(body)}
</main>
{FOOTER}
{st}{cl}
</body>
</html>"""


STICKY_KIT = ('<div class="mdh-stk" id="mdh-stk" hidden><p><b>Kit dossier MDPH</b>, 19 €</p><a class="mdh-btn mdh-sun" href="/kit-dossier-mdph/">Voir le kit</a>'
              '<button type="button" aria-label="Fermer ce bandeau">×</button></div>'
              "<script>(function(){var b=document.getElementById('mdh-stk'),K='mdh-stk',f=0;if(!b)return;try{f=+localStorage.getItem(K)||0}catch(e){}if(Date.now()-f<6048e5)return;"
              "function v(){if(scrollY>500&&innerWidth<=760){b.hidden=false;document.body.classList.add('mdh-stk-on');removeEventListener('scroll',v)}}addEventListener('scroll',v,{passive:true});"
              "b.querySelector('button').addEventListener('click',function(){b.hidden=true;document.body.classList.remove('mdh-stk-on');try{localStorage.setItem(K,Date.now())}catch(e){}})})();</script>")


def offre_ctx(titre, texte):
    """Encart court après l'introduction (classe mdh-offre exacte : exclue de la mesure anti-gabarit de verif.py)."""
    if not KIT.actif(PRODUIT): return ""
    return (f'<aside class="mdh-offre" aria-label="Offre optionnelle"><div class="mdh-offre-t"><p class="mdh-lab">Kit dossier MDPH, 19 €</p><p class="mdh-ctat">{E(titre)}</p>'
            f'<p>{E(texte)}</p></div><a class="mdh-btn mdh-sun" href="/{KIT.SLUG}/">Voir le kit</a></aside>')


OFFRE_GUIDE = {
    "dossier-mdph": ("Gagnez du temps sur votre dossier", "Checklists des pièces à cocher et Cerfa 15692 expliqué section par section, pour un dossier complet dès le dépôt."),
    "projet-de-vie-mdph": ("Besoin d'aide pour écrire votre projet de vie ?", "Le kit donne une méthode en 5 questions, deux grilles vierges et 4 exemples fictifs."),
    "certificat-medical-mdph": ("Préparez la consultation avec votre médecin", "Le kit contient une fiche à lui donner, pour que le certificat reflète votre quotidien."),
    "dossier-mdph-trop-long": ("Pour le prochain dépôt, un dossier complet", "Checklists, fiche de suivi des relances et délais de chaque MDPH, dans un PDF de 26 pages."),
    "recours-mdph": ("Préparez votre recours sans rien oublier", "Le kit explique les délais, le RAPO puis le tribunal, avec un modèle vierge de lettre à compléter."),
    "renouvellement-mdph": ("Renouvelez sans coupure de droits", "Checklists des pièces, fiche rappel et Cerfa expliqué : tout pour redéposer à temps."),
}


def clarity_html():
    """Bandeau de consentement + chargement différé de Clarity. Rien n'est chargé avant « Accepter ». « Refuser » est aussi visible.
    Le choix est gardé dans le navigateur (localStorage, 6 mois). Masquage strict : data-clarity-mask sur <body> et réglage « Strict »."""
    cid = json.dumps(str(CLARITY_ID))
    return ('<div class="mdh-consent" id="mdh-consent" role="region" aria-label="Mesure d\'audience" hidden style="position:fixed;left:12px;right:12px;bottom:12px;z-index:30;max-width:640px;margin:0 auto;background:var(--papier);border:1px solid var(--filet2);border-radius:16px;padding:16px 18px;box-shadow:0 10px 30px rgba(29,39,53,.15)">'
            '<p style="margin:0 0 10px">Acceptez-vous une mesure d\'audience anonyme (Microsoft Clarity) pour améliorer les guides ? Tout le texte est masqué, les outils ne sont jamais mesurés. <a href="/confidentialite/">En savoir plus</a></p>'
            '<p class="mdh-btns" style="margin:0"><button type="button" class="mdh-btn" data-c="1">Accepter</button><button type="button" class="mdh-btn" data-c="0">Refuser</button></p></div>'
            '<script>(function(){var K="mdh-consent",b=document.getElementById(K),v=null;try{v=JSON.parse(localStorage.getItem(K)||"null")}catch(e){}'
            'function go(){(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y)})(window,document,"clarity","script",' + cid + ');'
            'window.clarity("consentv2",{ad_Storage:"denied",analytics_Storage:"granted"})}'
            'if(v&&v.t>Date.now()-15552e6){if(v.ok)go();return}b.hidden=false;b.addEventListener("click",function(e){var x=e.target.getAttribute("data-c");if(x===null)return;'
            'try{localStorage.setItem(K,JSON.stringify({ok:x==="1",t:Date.now()}))}catch(e){}b.hidden=true;if(x==="1")go()})})();</script>')


def img_html(nom, sizes="(max-width: 860px) 100vw, 780px", prio=False):
    return (f'<picture><source type="image/webp" srcset="/img/{nom}-800.webp 800w, /img/{nom}.webp 1600w" sizes="{sizes}">'
            f'<img src="/img/{nom}-800.jpg" srcset="/img/{nom}-800.jpg 800w, /img/{nom}.jpg 1600w" sizes="{sizes}" width="1600" height="1067" alt="{E(ALT[nom])}"'
            f'{" fetchpriority=" + chr(34) + "high" + chr(34) if prio else " loading=" + chr(34) + "lazy" + chr(34)}></picture>')


def person():
    return {"@type": "Person", "name": AUTEUR, "url": DOMAIN + "/a-propos/"}


def org():
    return {"@context": "https://schema.org", "@type": "Organization", "name": SITE, "url": DOMAIN + "/", "logo": DOMAIN + "/favicon.svg", "founder": person()}


def crumbs(items):
    h = '<nav class="mdh-crumbs" aria-label="Fil d\'Ariane"><a href="/">Accueil</a>'
    for t, u in items:
        h += f' › <a href="{u}">{E(t)}</a>' if u else f" › <span>{E(t)}</span>"
    return h + "</nav>"


def bc_schema(items):
    el = [{"@type": "ListItem", "position": 1, "name": "Accueil", "item": DOMAIN + "/"}]
    for i, (t, u) in enumerate(items):
        el.append({"@type": "ListItem", "position": i + 2, "name": t, "item": DOMAIN + u})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": el}


def faq_html(faq, fid="faq"):
    if not faq: return ""
    return (f'<section aria-labelledby="{fid}"><h2 id="{fid}">Questions fréquentes</h2>' +
            "".join(f"<details><summary>{E(strip(q))}</summary><p>{inline(r)}</p></details>" for q, r in faq) + "</section>")


def faq_schema(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(r)}} for q, r in faq]}


def cta(outil, titre=None, texte=None):
    s, btn, t, d = OUTILS[outil]
    return (f'<aside class="mdh-cta"><div><p class="mdh-ctat">{E(titre or t)}</p><p>{E(texte or d)} Gratuit, rien n\'est enregistré.</p></div>'
            f'<a class="mdh-btn" href="{url(s)}">{E(btn)}</a></aside>')


def produit_slot(court=False):
    """Emplacement réservé au futur produit payant : vide tant que PRODUIT vaut None. court=True : version brève (pages départements, anti-gabarit)."""
    if not KIT.actif(PRODUIT): return ""
    if court:
        return (f'<aside class="mdh-offre" aria-label="Offre optionnelle"><div class="mdh-offre-t"><p class="mdh-lab">Optionnel</p><p class="mdh-ctat">Kit dossier MDPH, 19 €</p>'
                f'<p>Checklists, Cerfa expliqué et modèles vierges. Le dépôt reste gratuit.</p></div><a class="mdh-btn" href="/{KIT.SLUG}/">Voir le kit</a></aside>')
    return (f'<aside class="mdh-offre" aria-label="Offre optionnelle"><div class="mdh-offre-t"><p class="mdh-lab">Optionnel, pour aller plus vite</p>'
            f'<p class="mdh-ctat">Préparez votre dossier MDPH sans rien oublier</p><p>Le Kit dossier MDPH réunit en 26 pages tout ce qu\'il faut pour préparer votre dossier : '
            f'checklists des pièces, Cerfa expliqué de A à F, grilles pour le projet de vie, fiche pour votre médecin, délais de votre MDPH et modèle vierge de recours.</p>'
            f'<p><b>19 €</b> · téléchargement immédiat · remboursé sous 14 jours sur simple demande · <a href="{KIT.EXTRAIT}">Lire l\'extrait gratuit</a></p>'
            f'<p class="mdh-note">Guide indépendant. Le dépôt du dossier est gratuit auprès de votre MDPH.</p></div>'
            f'<a class="mdh-btn" href="/{KIT.SLUG}/">Voir le kit</a></aside>')


# --------------------------------------------------------------------------- guides
def bloc(b):
    t = b.get("type")
    if t == "p": return f"<p>{inline(b.get('texte'))}</p>"
    if t == "liste": return "<ul>" + "".join(f"<li>{inline(i)}</li>" for i in b.get("items", [])) + "</ul>"
    if t == "etapes": return '<ol class="mdh-steps">' + "".join(f"<li>{inline(i)}</li>" for i in b.get("items", [])) + "</ol>"
    if t == "tableau":
        th = "".join(f'<th scope="col">{inline(h)}</th>' for h in b.get("entetes", []))
        rows = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in b.get("lignes", []))
        return f'<div class="mdh-tw"><table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div>'
    if t == "exemple": return f'<aside class="mdh-ex"><p class="mdh-lab">{E(b.get("titre") or "Exemple")}</p><p>{inline(b.get("texte"))}</p></aside>'
    if t == "attention": return f'<aside class="mdh-warn"><p class="mdh-lab">Attention</p><p>{inline(b.get("texte"))}</p></aside>'
    if t == "modele": return f'<aside class="mdh-model"><p class="mdh-lab">{E(b.get("titre") or "Modèle vierge")}</p><pre>{E(b.get("texte"))}</pre><p class="mdh-note">Modèle d\'information générale, à adapter vous-même. Pour une situation précise, une association, un point-justice ou un avocat peut vous aider.</p></aside>'
    return ""


def ancre(h2):
    s = re.sub(r"[^a-z0-9]+", "-", strip(h2).lower().translate(str.maketrans("àâäéèêëîïôöùûüç’'", "aaaeeeeiioouuuc  "))).strip("-")
    return s[:60] or "section"


def guide(d):
    slug = d["slug"]
    court, img, outil = GUIDES[slug]
    path = url(slug)
    verif = d.get("date_verification") or LANCEMENT
    srcs = [x for x in d.get("sources", []) if str(x.get("url", "")).startswith("https://")]
    secs = d.get("sections", [])
    ids = []
    for s in secs:
        a = ancre(s["h2"]); n = 2
        while a in ids: a = f"{ancre(s['h2'])}-{n}"; n += 1
        ids.append(a)
    corps = []
    for i, (s, a) in enumerate(zip(secs, ids)):
        sh = "".join(bloc(b) for b in s.get("blocs", []))
        idx = [k for k in s.get("sources", []) if isinstance(k, int) and 0 <= k < len(d.get("sources", []))]
        ss = [d["sources"][k] for k in idx if str(d["sources"][k].get("url", "")).startswith("https://")]
        if ss:
            sh += '<p class="mdh-src">Source : ' + " ; ".join(f'<a href="{E(x["url"])}" rel="noopener" target="_blank">{E(x.get("titre") or x["url"])}</a>' + (f" ({E(x['date'])})" if x.get("date") else "") for x in ss) + ".</p>"
        corps.append(f'<section aria-labelledby="{a}"><h2 id="{a}">{E(strip(s["h2"]))}</h2>{sh}</section>')
        if i == 0 and len(secs) >= 3:
            corps.append(offre_ctx(*OFFRE_GUIDE.get(slug, ("Gagnez du temps sur votre dossier MDPH", "Checklists des pièces, Cerfa expliqué, grilles pour le projet de vie et modèles vierges, dans un PDF de 26 pages."))))
        if i == 1: corps.append(cta(outil))
    toc = "".join(f'<li><a href="#{a}">{E(strip(s["h2"]))}</a></li>' for s, a in zip(secs, ids))
    faq = [(f["q"], f["r"]) for f in d.get("faq", [])]
    bref = "".join(f"<li>{inline(x)}</li>" for x in d.get("en_bref", []))
    urg = d.get("urgence")
    urg_html = f'<aside class="mdh-warn"><p class="mdh-lab">À ne pas laisser passer</p><p>{inline(urg)}</p></aside>' if urg else ""
    liens = []
    for l in d.get("liens_internes", []):
        s2 = l.get("slug") if isinstance(l, dict) else l
        s2 = (s2 or "").strip("/")
        if s2 in SLUGS and s2 != slug and s2 not in [x[0] for x in liens] and (s2 not in GUIDES or s2 in CONTENUS):
            lab = GUIDES[s2][0] if s2 in GUIDES else next((v[2] for v in OUTILS.values() if v[0] == s2), None) or (l.get("ancre") if isinstance(l, dict) else s2)
            liens.append((s2, lab))
    if "delais-mdph" not in [x[0] for x in liens]: liens.append(("delais-mdph", "Délais des MDPH par département"))
    nxt = "".join(f'<li><a href="{url(s2)}">{E(strip(a)[:1].upper() + strip(a)[1:])}</a></li>' for s2, a in liens[:6])
    sources = "".join(f'<li><a href="{E(x["url"])}" rel="noopener" target="_blank">{E(x.get("titre") or x["url"])}</a>' + (f" ({E(x['date'])})" if x.get("date") else "") + "</li>" for x in srcs)
    keys = {"delai": ["delai", "4mois", "2mois"], "fin": ["6mois", "delai", "2mois"], "aah": ["delai", "4mois", "6mois"], "aeeh": ["delai", "4mois", "6mois"]}[outil]
    if slug == "recours-mdph": keys = ["2mois", "4mois", "delai"]
    deps_html = ""
    if slug == "dossier-mdph-trop-long":
        lis = "".join(f'<li><a href="/delais-mdph/{DP.DEPS[c]["slug"]}/">{E(DP.DEPS[c]["nom"])} ({c})</a></li>' for c in sorted(DP.PAGES_DEP, key=lambda c: DP.DEPS[c]["nom"]))
        deps_html = f'<section class="mdh-next" aria-labelledby="delais-dep"><h2 id="delais-dep">Délais par département</h2><p>Le délai de traitement varie d\'une MDPH à l\'autre. Voici les pages qui détaillent le délai moyen de chaque département suivi :</p><ul>{lis}</ul></section>\n'
    body = f"""<div class="mdh-w"><div class="mdh-art">
{crumbs([("Guides", "/#guides"), (court, None)])}
<header class="mdh-head"><span class="mdh-badge">Guide pratique</span>
<h1>{E(strip(d['h1']))}</h1>
<p class="mdh-chapo">{inline(d.get('chapo'))}</p>
<div class="mdh-author"><span class="mdh-ini" aria-hidden="true">LL</span><span>Par <b>{AUTEUR}</b>, <a href="/a-propos/">auteur du site</a> · vérifié le {date_fr(verif)} · {len(srcs)} sources officielles</span></div>
</header>
{urg_html}
<div class="mdh-answer"><p class="mdh-lab">La réponse courte</p><ul>{bref}</ul></div>
<p class="mdh-btns"><a class="mdh-btn" href="{url(OUTILS[outil][0])}">{E(OUTILS[outil][1])}</a><a class="mdh-btn mdh-alt" href="/delais-mdph/">Voir le délai de ma MDPH</a></p>
<figure class="mdh-fig">{img_html(img, prio=True)}</figure>
<nav aria-label="Sommaire"><p class="mdh-lab">Dans ce guide</p><ul class="mdh-toc">{toc}{'<li><a href="#faq">Questions fréquentes</a></li>' if faq else ''}</ul></nav>
{''.join(corps)}
{urgences(keys)}
{aide_urgente() if slug in ("dossier-mdph-trop-long", "recours-mdph") else ""}
{faq_html(faq)}
{produit_slot()}
{deps_html}<section class="mdh-next" aria-labelledby="suite"><h2 id="suite">Pour aller plus loin</h2><ul>{nxt}</ul></section>
<section class="mdh-sources" aria-labelledby="sources"><h2 id="sources">Sources</h2><p>Informations vérifiées le {date_fr(verif)} sur les sites officiels. Les montants changent en général au 1er janvier ou au 1er avril : en cas de doute, l'organisme qui verse l'aide fait foi.</p><ul>{sources}</ul></section>
</div></div>"""
    schema = [{"@context": "https://schema.org", "@type": "Article", "headline": strip(d["h1"])[:110], "description": d.get("description", ""),
               "image": f"{DOMAIN}/img/{img}.jpg", "datePublished": LANCEMENT, "dateModified": max(verif, MODIFS.get(path, verif)), "inLanguage": "fr-FR",
               "author": person(), "publisher": {"@type": "Organization", "name": SITE, "url": DOMAIN + "/", "logo": {"@type": "ImageObject", "url": DOMAIN + "/favicon.svg"}},
               "mainEntityOfPage": DOMAIN + path, "citation": [x["url"] for x in srcs]},
              bc_schema([("Guides", "/"), (court, path)])]
    if faq: schema.append(faq_schema(faq))
    return path, page(d["title"], d["description"], path, body, schema, img, None, (OUTILS[outil][0], OUTILS[outil][1]))


# --------------------------------------------------------------------------- classement
def classement():
    rows = DP.classement_rows()
    n = len(rows)
    gn = DP.nat("global")
    tr = []
    for i, r in enumerate(rows):
        nom = E(r["nom"]) + (f' <span class="mdh-note">({r["code"]})</span>' if r["code"].isdigit() else "")
        if r["lien"]: nom = f'<a href="{r["lien"]}">{nom}</a>'
        ev = r["global"] - r["an"] if r["an"] is not None else None
        evh = "" if ev is None else ('<span style="color:#575267">stable</span>' if abs(ev) < 0.05 else f'<span style="color:{"#a8401b" if ev > 0 else "#1d6e4f"}">{"+" if ev > 0 else ""}{DP.fr(ev)}</span>')
        cells = "".join(f'<td class="mdh-n" data-v="{"" if r[k] is None else round(r[k], 2)}">{"n.c." if r[k] is None else DP.fr(r[k])}</td>' for k, _ in DP.TYPES)
        tr.append(f'<tr data-nom="{E(r["nom"].lower())} {r["code"].lower()}"><td class="mdh-n" data-v="{i + 1}">{i + 1}</td><td data-v="{E(r["nom"])}">{nom}</td>{cells}<td class="mdh-n" data-v="{"" if ev is None else round(ev, 2)}">{evh}</td></tr>')
    heads = '<th class="mdh-n"><button type="button" data-k="0">Rang</button></th><th><button type="button" data-k="1">Département</button></th>' + "".join(
        f'<th class="mdh-n"><button type="button" data-k="{j + 2}">{E(lab.capitalize() if lab[0].islower() else lab)}</button></th>' for j, (_, lab) in enumerate(DP.TYPES)) + '<th class="mdh-n"><button type="button" data-k="7">Sur 1 an</button></th>'
    table = f'<div class="mdh-tw"><table id="classement"><caption class="mdh-note" style="text-align:left;padding:8px 12px">Délai moyen de traitement en mois au {DP.tlab(DP.DERNIER)}, du plus long au plus court. « Sur 1 an » : écart avec le {DP.tlab("2025T2")}. n.c. : non communiqué.</caption><thead><tr>{heads}</tr></thead><tbody>{"".join(tr)}</tbody></table></div>'
    lents = [(r["nom"], r["global"], r["lien"]) for r in rows[:12]]
    rapides = [(r["nom"], r["global"], r["lien"]) for r in rows[-12:]][::-1]
    T = ["2021T2", "2021T3", "2021T4", "2022T1", "2022T2", "2022T3", "2022T4", "2023T1", "2023T2", "2023T3", "2023T4", "2024T1", "2024T2", "2024T3", "2024T4", "2025T1", "2025T2", "2025T3", "2025T4", "2026T1", "2026T2"]
    courbe = G.lignes([("Toutes demandes", G.C["brand"], [DP.nat("global", t) for t in T], False), ("AAH", G.C["alert"], [DP.nat("aah", t) for t in T], False),
                       ("PCH", G.C["ok"], [DP.nat("pch", t) for t in T], False), ("Enfants", G.C["sun"], [DP.nat("enfants", t) for t in T], True)],
                      [DP.tlab(t, True) for t in T], "Délai moyen national de traitement des MDPH, 2021 à 2026")
    hi = max(T, key=lambda t: DP.nat("global", t) or 0)
    plus4 = sum(1 for r in rows if r["global"] > 4)
    med = sorted(r["global"] for r in rows)[n // 2]
    top = rows[0]; bas = rows[-1]
    pages20 = "".join(f'<li><a href="/delais-mdph/{DP.DEPS[c]["slug"]}/">MDPH {E(DP.de(DP.DEPS[c]["nom"]))} ({c})</a></li>' for c in DP.PAGES_DEP)
    faq = [
        ("Quelle est la MDPH la plus lente en 2026 ?", f"Au {DP.tlab(DP.DERNIER)}, le délai moyen le plus long est celui {DP.de(top['nom'])} ({DP.mois_txt(top['global'])}), d'après le baromètre de la CNSA. C'est une moyenne sur tous les dossiers du trimestre."),
        ("Quelle est la MDPH la plus rapide ?", f"Au {DP.tlab(DP.DERNIER)}, c'est {DP.dans(bas['nom'])} que le délai moyen est le plus court ({DP.mois_txt(bas['global'])}). On ne peut toutefois pas choisir sa MDPH : c'est celle de votre lieu de résidence qui est compétente."),
        ("Quel est le délai moyen d'une MDPH en 2026 ?", f"{DP.cap(DP.mois_txt(gn))} en moyenne nationale au {DP.tlab(DP.DERNIER)}, toutes demandes confondues. Il était de {DP.mois_txt(DP.nat('global', '2025T2'))} un an plus tôt. Pour l'AAH, la moyenne est de {DP.mois_txt(DP.nat('aah'))}, pour la PCH de {DP.mois_txt(DP.nat('pch'))}."),
        ("Que faire si la MDPH dépasse 4 mois ?", "Au bout de 4 mois sans réponse, la demande est considérée comme refusée : c'est un refus implicite, qui permet de contester. La MDPH peut toutefois encore rendre sa décision. Le guide [dossier sans réponse](dossier-mdph-trop-long) explique comment relancer et l'outil [date de refus implicite](outils/delai-reponse-mdph) calcule vos dates."),
        ("Ces délais sont-ils mis à jour ?", "Oui. La CNSA publie le baromètre chaque trimestre ; ce classement est mis à jour à chaque nouvelle publication, avec la date indiquée en haut de page."),
    ]
    body = f"""<div class="mdh-w">
{crumbs([("Délais des MDPH en 2026", None)])}
<header class="mdh-head"><span class="mdh-badge">Données officielles · {DP.tlab(DP.DERNIER)}</span>
<h1>Délais des MDPH en 2026 : le classement des {n} territoires</h1>
<p class="mdh-chapo">Au {DP.tlab(DP.DERNIER)}, une MDPH met en moyenne <b>{DP.mois_txt(gn)}</b> à traiter une demande. Mais l'écart va de {DP.mois_txt(bas['global'])} {DP.dans(bas['nom'])} à {DP.mois_txt(top['global'])} {DP.dans(top['nom'])}. Retrouvez le délai de votre MDPH pour l'AAH, la PCH, les enfants et les adultes.</p>
{trust(4)}
</header>
<div class="mdh-filter mdh-search" role="search"><label for="q2" class="mdh-lab">Trouver ma MDPH</label><div class="mdh-sfield"><svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 20 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input id="q2" type="search" autocomplete="off" placeholder="Nom ou numéro, par exemple Gironde ou 33"></div></div>
<div id="q-res" class="mdh-qres" aria-live="polite" hidden></div>
<ul class="mdh-kpis">
<li><b>{DP.fr(gn)} mois</b><span>délai moyen national au {DP.tlab(DP.DERNIER)}</span></li>
<li><b>{plus4} sur {n}</b><span>territoires au-delà de 4 mois, seuil du refus implicite</span></li>
<li><b>{DP.fr(med)} mois</b><span>délai médian : la moitié des MDPH font mieux</span></li>
<li><b>{DP.fr(DP.nat('global', hi))} mois</b><span>pic national, au {DP.tlab(hi)}</span></li>
</ul>
{DP.repartition()}
<section aria-labelledby="tableau"><h2 id="tableau">Le classement complet</h2>
<p>Cliquez sur un intitulé de colonne pour trier. Les départements en lien ont une page détaillée (évolution sur 6 trimestres, droits à vie, allocataires, contacts).</p>
<div class="mdh-sortbar" role="group" aria-label="Trier le classement"><button type="button" data-k="2" data-dir="desc" aria-pressed="true">Plus long d'abord</button><button type="button" data-k="2" data-dir="asc" aria-pressed="false">Plus court d'abord</button><button type="button" data-k="1" data-dir="asc" aria-pressed="false">De A à Z</button></div>
{table}
{DP.src_line("delais")}
</section>
{cta("delai", "Votre dossier dépasse 4 mois ?", "Calculez la date du refus implicite et vos délais de recours.")}
<section aria-labelledby="extremes"><h2 id="extremes">Les MDPH les plus lentes et les plus rapides</h2>
<p>Au {DP.tlab(DP.DERNIER)}, {plus4} territoires sur {n} dépassent 4 mois de délai moyen. Les écarts tiennent à plusieurs facteurs que le baromètre ne détaille pas : nombre de demandes reçues, effectifs, part de dossiers incomplets, organisation de l'évaluation.</p>
{G.barres(lents, "Les 12 délais moyens les plus longs au " + DP.tlab(DP.DERNIER), gn)}
{G.barres(rapides, "Les 12 délais moyens les plus courts au " + DP.tlab(DP.DERNIER), gn)}
{DP.src_line("delais")}
</section>
<section aria-labelledby="evolution"><h2 id="evolution">L'évolution depuis 2021</h2>
<p>Le délai moyen national a atteint {DP.mois_txt(DP.nat('global', hi))} au {DP.tlab(hi)}, puis il recule : {DP.mois_txt(DP.nat('global', '2025T2'))} au {DP.tlab('2025T2')}, {DP.mois_txt(gn)} au {DP.tlab(DP.DERNIER)}. Les demandes d'AAH restent un peu plus longues que la moyenne ({DP.mois_txt(DP.nat('aah'))}), celles de PCH aussi ({DP.mois_txt(DP.nat('pch'))}), car elles demandent souvent une évaluation plus poussée.</p>
{courbe}
{DP.src_line("delais")}
</section>
<section aria-labelledby="pages-dep"><h2 id="pages-dep">Les pages détaillées par département</h2>
<p>Vingt départements ont une page complète, choisis parmi les plus peuplés et ceux où l'attente est la plus longue. Pour les autres, la ligne du tableau donne les mêmes délais.</p>
<ul class="mdh-deps">{pages20}</ul></section>
<section aria-labelledby="lire"><h2 id="lire">Comment lire ces chiffres</h2>
<ul><li><b>Ce qui est mesuré</b> : le délai moyen entre le dépôt d'un dossier complet et la décision, pour les décisions rendues pendant le trimestre. C'est une moyenne : votre dossier peut être plus rapide ou plus long.</li>
<li><b>Le Rhône</b> apparaît deux fois (Métropole de Lyon et Rhône hors Métropole), la <b>Corse</b> et l'<b>Alsace</b> une seule, comme dans le baromètre de la CNSA.</li>
<li><b>Mise à jour</b> : chaque trimestre, à la publication du baromètre. Dernier relevé le {date_fr(MAJ_DONNEES)}. Le fichier est <a href="/donnees/delais-mdph-{DP.DERNIER.lower()}.csv">téléchargeable en CSV</a>.</li>
<li>Détail de la méthode : <a href="/methode-et-sources/">méthode et sources</a>.</li></ul></section>
{urgences(["4mois", "2mois", "6mois"])}
{produit_slot(True)}
{faq_html([(q, r) for q, r in faq])}
</div>"""
    path = "/delais-mdph/"
    schema = [
        {"@context": "https://schema.org", "@type": "Dataset", "name": f"Délais moyens de traitement des MDPH par département, {DP.tlab(DP.DERNIER)}",
         "description": "Délai moyen de traitement des demandes par les maisons départementales des personnes handicapées, toutes demandes, AAH, PCH, enfants et adultes, d'après le baromètre des MDPH de la CNSA.",
         "url": DOMAIN + path, "creator": {"@type": "Organization", "name": "CNSA (Caisse nationale de solidarité pour l'autonomie)", "url": "https://www.cnsa.fr/"},
         "isBasedOn": "https://www.cnsa.fr/donnees/barometre-des-mdph", "temporalCoverage": "2021-04/2026-06", "spatialCoverage": "France",
         "dateModified": MAJ_DONNEES, "inLanguage": "fr-FR", "license": "https://www.etalab.gouv.fr/licence-ouverte-open-licence/",
         "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": f"{DOMAIN}/donnees/delais-mdph-{DP.DERNIER.lower()}.csv"}]},
        {"@context": "https://schema.org", "@type": "Article", "headline": f"Délais des MDPH en 2026 : le classement des {n} territoires", "datePublished": LANCEMENT, "dateModified": MODIFS.get("/delais-mdph/", MAJ_DONNEES),
         "author": person(), "publisher": {"@type": "Organization", "name": SITE, "url": DOMAIN + "/"}, "image": f"{DOMAIN}/img/demarches.jpg", "mainEntityOfPage": DOMAIN + path, "inLanguage": "fr-FR"},
        bc_schema([("Délais des MDPH en 2026", path)]), faq_schema(faq)]
    return path, page(f"Délais MDPH 2026 : le classement des {n} territoires", f"Délai moyen de chaque MDPH au {DP.tlab(DP.DERNIER)} (CNSA) : de {DP.mois_txt(bas['global'])} à {DP.mois_txt(top['global'])}. AAH, PCH, enfants, adultes, évolution sur un an.",
                      path, body, schema, "demarches", "delais-mdph", ("outils/delai-reponse-mdph", "Calculer mes dates (4 mois)"), "classement")


def csv_delais():
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["code", "territoire"] + [f"delai_{k}_{DP.DERNIER}" for k, _ in DP.TYPES] + ["delai_global_2025T2", "source"])
    for r in DP.classement_rows():
        w.writerow([r["code"], r["nom"]] + ["" if r[k] is None else str(round(r[k], 2)).replace(".", ",") for k, _ in DP.TYPES] + ["" if r["an"] is None else str(round(r["an"], 2)).replace(".", ","), "CNSA, barometre des MDPH"])
    return buf.getvalue()


# --------------------------------------------------------------------------- pages départements
def urg_dep(code, nom, g):
    """Repères d'urgence calculés pour le département (règles officielles + délai moyen local)."""
    if g is None: return urgences(["4mois", "2mois", "6mois"])
    li = [(f"{DP.fr(g)} mois", (f"Le délai moyen {DP.de(nom)} dépasse les 4 mois du refus implicite, d'où l'intérêt d'un dossier complet dès le dépôt." if g > 4 else f"Le délai moyen {DP.de(nom)} reste sous les 4 mois légaux pour un dossier complet."), "/dossier-mdph/", "Préparer mon dossier pas à pas"),
          ("2 mois", f"Après une décision de la MDPH {DP.de(nom)}, vous avez 2 mois à compter de la notification pour un recours amiable.", "/recours-mdph/", "Contester une décision"),
          ("6 mois avant", f"Avec {DP.mois_txt(g)} d'attente {DP.dans(nom)}, redéposez 6 mois avant la fin de vos droits, comme le recommandent les sites officiels.", "/outils/fin-de-droits-mdph/", "Calculer ma date de renouvellement")]
    return '<ul class="mdh-urg">' + "".join(f'<li><b>{E(a)}</b><span>{E(b)}</span><a href="{c}">{E(d)} →</a></li>' for a, b, c, d in li) + "</ul>"


def page_dep(code):
    p = DP.page_dep(code)
    nom = p["nom"]
    d = DP.DEPS[code]
    path = f"/delais-mdph/{d['slug']}/"
    g = p["g"]
    nomc = "Rhône" if code == "69" else nom
    an = (d.get("annuaire") or [{}])[0] if d.get("annuaire") else {}
    an = {k: (v.replace(" – ", "-").replace("–", "-").replace("—", ",") if isinstance(v, str) else v) for k, v in an.items()}
    # 23/11/2026 : la Search Console montre « mdph 91 », « mdph 93 », « horaires mdph evry » : l'intention est le contact, pas le délai.
    for t in (f"MDPH {DP.de(nomc)} ({code}) : adresse, téléphone et délais 2026",
              f"MDPH {nomc} ({code}) : adresse, téléphone et délais 2026",
              f"MDPH {nomc} ({code}) : téléphone, adresse, délais",
              f"MDPH {nomc} ({code}) : contact et délais 2026"):
        titre = t
        if len(titre) <= 60: break
    h1 = f"MDPH {DP.de(nom)} ({code}) : délais 2026, contacts et chiffres clés"
    if g is not None:
        r = DP.rang("69M" if code == "69" else code)
        chapo = (f"{DP.cap(DP.dans(nom))}, la MDPH a mis en moyenne <b>{DP.mois_txt(g)}</b> à traiter une demande au {DP.tlab(DP.DERNIER)}" + (" (territoire le plus lent des deux)" if code == "69" else "") +
                 f", contre {DP.mois_txt(DP.nat('global'))} en France. " + DP.V(code, "ch", [f"Détail pour l'AAH et la PCH, droits à vie, allocataires et coordonnées de la MDPH {DP.de(nom)}.", f"Vous trouverez ici l'évolution sur six trimestres, les droits à vie, les allocataires {DP.de(nom)} et les contacts officiels.", f"La page reprend aussi les droits à vie, le nombre d'allocataires de l'AAH et de l'AEEH {DP.dans(nom)} et les coordonnées utiles."]))
        lieu = f" à {an['commune'].replace(' Cedex', '')}" if an.get("commune") else ""
        tel = f" : {an['tel']}" if an.get("tel") else ""
        desc = f"MDPH {DP.de(nomc)}{lieu}{tel}, adresse et horaires (annuaire officiel). Délai moyen {DP.mois_txt(g)} au {DP.tlab(DP.DERNIER)}, France {DP.mois_txt(DP.nat('global'))}."
        if len(desc) > 158: desc = f"MDPH {DP.de(nomc)}{tel}, adresse et horaires. Délai moyen {DP.mois_txt(g)} au {DP.tlab(DP.DERNIER)} (France {DP.mois_txt(DP.nat('global'))})."
    else:
        chapo = desc = f"Délais, allocataires et contacts de la MDPH {DP.de(nom)}."
    if len(desc) > 155: desc = desc[:152].rsplit(" ", 1)[0] + "…"
    contact_top = ""
    if an.get("adresse") or an.get("tel"):
        li = []
        if an.get("tel"): li.append(f'<li><b>Téléphone</b> <a href="tel:{E(an["tel"].replace(" ", ""))}">{E(an["tel"])}</a></li>')
        if an.get("adresse"): li.append(f'<li><b>Adresse</b> {E(an["adresse"])}</li>')
        if not an.get("tel") and an.get("courriel"): li.append(f'<li><b>Courriel</b> <a href="mailto:{E(an["courriel"])}">{E(an["courriel"])}</a></li>')
        contact_top = (f'<div class="mdh-contact mdh-contact-top"><b>Contacter la MDPH {E(DP.de(nom))}</b><ul>{"".join(li)}</ul>'
                       f'<p class="mdh-note">D\u2019après la fiche {E((an.get("commune") or "").replace(" Cedex", ""))} de l\u2019annuaire officiel de l\u2019administration (lannuaire.service-public.gouv.fr){", mise à jour le " + E(an["maj"]) if an.get("maj") else ""}. '
                       f'<a href="#contact">Horaires d\u2019accueil de la MDPH {E(DP.de(nom))}, courriel et site</a></p></div>')
    urg = ""
    if g is not None:
        kp = [f'<li><b>{DP.fr(g)} mois</b><span>délai moyen, toutes demandes</span></li>']
        cc = "69M" if code == "69" else code
        for k, lab in (("aah", "pour une demande d'AAH"), ("pch", "pour une demande de PCH")):
            v = DP.DEPS[cc]["delais"][k].get(DP.DERNIER)
            if v is not None: kp.append(f'<li><b>{DP.fr(v)} mois</b><span>{lab}</span></li>')
        r = DP.rang(cc)
        kp.append(f'<li><b>{r[0]}e sur {r[1]}</b><span>rang national, du plus long au plus court</span></li>')
        badge = '<span class="mdh-badge mdh-b-alert">Au-delà de 4 mois</span>' if g > 4 else '<span class="mdh-badge mdh-b-ok">Sous les 4 mois</span>'
        urg = (f'<p class="mdh-local"><span>{badge}</span><span>{"Comptez " + DP.mois_txt(g) + " en moyenne " + DP.dans(nom) + ", plus que les 4 mois du refus implicite, donc déposez votre dossier dès qu" + chr(39) + "il est complet." if g > 4 else "Comptez " + DP.mois_txt(g) + " en moyenne " + DP.dans(nom) + ", sous la limite légale de 4 mois, si le dossier est complet dès le dépôt."}</span></p>'
               f'<ul class="mdh-kpis">{"".join(kp)}</ul>')
    corps = []
    toc = []
    for i, (sid, h2, blocs) in enumerate(p["sections"]):
        corps.append(f'<section aria-labelledby="{sid}"><h2 id="{sid}">{E(h2)}</h2>{"".join(blocs)}</section>')
        toc.append(f'<li><a href="#{sid}">{E(h2)}</a></li>')
        if i == 0:
            corps.append(offre_ctx(f"Dossier pour la MDPH {DP.de(nom)} ?",
                                   (f"Avec {DP.mois_txt(g)} d'attente en moyenne, une pièce oubliée coûte cher. " if g is not None else "") + "Le kit vous aide à déposer un dossier complet dès le premier envoi."))
        if i == 1: corps.append(cta("delai", DP.V(code, "cta", ["Calculez vos dates à partir de votre dépôt", f"Dossier déposé {DP.dans(nom)} ? Vos dates exactes", "Où en est votre dossier ?"]), f"Refus implicite à 4 mois, délais de recours et décision attendue selon le délai moyen {DP.de(nom)}."))
    autres = [c for c in DP.PAGES_DEP if c != code]
    proches = [c for c in DP.VOISINS.get(code, []) if c in DP.PAGES_DEP][:3]
    reste = proches + [c for c in autres if c not in proches][: 5 - len(proches)]
    nxt = "".join(f'<li><a href="/delais-mdph/{DP.DEPS[c]["slug"]}/">MDPH {E(DP.de(DP.DEPS[c]["nom"]))}</a></li>' for c in reste)
    nxt += '<li><a href="/delais-mdph/">Le classement complet</a></li><li><a href="/dossier-mdph/">Remplir le dossier MDPH</a></li><li><a href="/dossier-mdph-trop-long/">Dossier sans réponse : que faire</a></li>'
    body = f"""<div class="mdh-w"><div class="mdh-art">
{crumbs([("Délais des MDPH", "/delais-mdph/"), (nom, None)])}
<header class="mdh-head"><span class="mdh-badge">Données officielles · {DP.tlab(DP.DERNIER)}</span>
<h1>{E(h1)}</h1>
<p class="mdh-chapo">{chapo}</p>
{trust(5, lieu=DP.de(nom))}
</header>
{contact_top}
{urg}
{DP.repartition(("69M", "69D") if code == "69" else (code,), nomc) if g is not None else ""}
<nav aria-label="Sommaire"><p class="mdh-lab">Sur cette page</p><ul class="mdh-toc">{"".join(toc)}<li><a href="#faq">Questions fréquentes</a></li></ul></nav>
{"".join(corps)}
{urg_dep(code, nom, g)}
{produit_slot(True)}
{faq_html(p["faq"])}
<p class="mdh-src">Dates, définitions et limites de chaque chiffre {E(DP.de(nom))} sur la page <a href="/methode-et-sources/">méthode et sources</a>.</p>
<section class="mdh-next" aria-labelledby="suite"><h2 id="suite">Pour aller plus loin</h2><ul>{nxt}</ul></section>
</div></div>"""
    schema = [{"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": desc, "datePublished": LANCEMENT, "dateModified": MODIF_DEPS, "inLanguage": "fr-FR",
               "author": person(), "publisher": {"@type": "Organization", "name": SITE, "url": DOMAIN + "/"}, "image": f"{DOMAIN}/img/demarches.jpg", "mainEntityOfPage": DOMAIN + path,
               "about": {"@type": "AdministrativeArea", "name": nom}},
              bc_schema([("Délais des MDPH", "/delais-mdph/"), (nom, path)]), faq_schema(p["faq"])]
    return path, page(titre, desc, path, body, schema, "demarches", "delais-mdph", ("outils/delai-reponse-mdph", "Calculer mes dates (4 mois)"))


# --------------------------------------------------------------------------- outils
import outils_pages as OP


def page_outil(cle):
    o = OP.PAGES[cle]
    slug = OUTILS[cle][0]
    path = url(slug)
    body = f"""<div class="mdh-w"><div class="mdh-art">
{crumbs([("Outils", "/outils/"), (OUTILS[cle][2], None)])}
<header class="mdh-head"><span class="mdh-badge">Outil gratuit</span>
<h1>{E(o['h1'])}</h1>
<p class="mdh-chapo">{o['chapo']}</p>
{trust(len(o['sources']), outil=True)}
</header>
<div class="mdh-tool-box" data-outil="{cle}"><noscript>Cet outil a besoin de JavaScript. Il calcule tout dans votre navigateur, sans rien envoyer.</noscript></div>
{o['avant']}
{urgences(o['urg'])}
{o['corps']}
{produit_slot(True)}
{faq_html(o['faq'])}
<section class="mdh-next" aria-labelledby="suite"><h2 id="suite">Pour aller plus loin</h2><ul>{o['suite']}</ul></section>
<section class="mdh-sources" aria-labelledby="sources"><h2 id="sources">Sources</h2><p>Paramètres vérifiés le {date_fr(o['verif'])}.</p><ul>{"".join(f'<li><a href="{E(u)}" rel="noopener" target="_blank">{E(t)}</a></li>' for t, u in o['sources'])}</ul></section>
</div></div>"""
    schema = [{"@context": "https://schema.org", "@type": "WebApplication", "name": o["h1"], "url": DOMAIN + path, "applicationCategory": "UtilityApplication", "operatingSystem": "Tous navigateurs",
               "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "inLanguage": "fr-FR", "author": person(), "dateModified": o["verif"]},
              bc_schema([("Outils", "/outils/"), (OUTILS[cle][2], path)]), faq_schema(o["faq"])]
    return path, page(o["title"], o["desc"], path, body, schema, o["img"], None, None, "outil")


# --------------------------------------------------------------------------- index des outils
ICO = {"aah": '<path d="M15.5 8.5A5 5 0 1 0 15.5 15.5M7 10.5h6M7 13.5h6"/>', "aeeh": '<circle cx="12" cy="7" r="2.6"/><path d="M7 20c0-4 2.2-7 5-7s5 3 5 7"/>',
       "delai": '<path d="M7 4h10M7 20h10M8 4c0 5 8 6 8 8s-8 3-8 8M16 4c0 5-8 6-8 8"/>', "fin": '<rect x="4" y="6" width="16" height="14" rx="3"/><path d="M8 3.5v4M16 3.5v4M4 10.5h16M10 15l2 2 3.5-3.5"/>'}


def tuiles_outils():
    return "".join(f'<li><a class="mdh-tile mdh-tool" href="{url(v[0])}"><i aria-hidden="true"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICO[k]}</svg></i><b>{E(v[2])}</b><span>{E(v[3])}</span><em>{E(v[1])} →</em></a></li>' for k, v in OUTILS.items())


def index_outils():
    """Page /outils/ : index des 4 outils (maillage), sans script d'outil ni mesure d'audience."""
    path = "/outils/"
    A = OP.PARAMS["aah"]; AE = OP.PARAMS["aeeh"]
    quand = [
        ("delai", "Vous avez déposé un dossier et la MDPH ne répond pas", f"Sans décision 4 mois après le dépôt d'un dossier complet, la demande vaut refus implicite. L'outil donne cette date, la fin du délai de recours de 2 mois et la décision attendue selon le délai moyen de votre MDPH ({DP.fr(DP.nat('global'))} mois en France au {DP.tlab(DP.DERNIER)})."),
        ("fin", "Vos droits arrivent à échéance", "La demande de renouvellement se dépose 6 mois avant la fin des droits, comme le recommandent les sites officiels. L'outil calcule cette date et crée un rappel pour votre agenda, enregistré seulement sur votre appareil."),
        ("aah", "Vous voulez savoir combien d'AAH toucher", f"L'AAH est de {OP.eur(A['max'])} par mois au plus depuis le {A['date']}. L'outil tient compte d'un salaire, d'un travail en Ésat (règle trimestrielle depuis le 1er octobre 2026) ou de votre revenu net catégoriel."),
        ("aeeh", "Vous élevez un enfant handicapé", f"L'AEEH de base est de {OP.eur(AE['base'])} par mois depuis le {AE['date']}. L'outil estime la catégorie de complément selon vos dépenses, votre temps de travail et l'aide d'une tierce personne."),
    ]
    blocs = "".join(f'<section aria-labelledby="o-{k}"><h2 id="o-{k}">{E(t)}</h2><p>{E(x)}</p><p><a class="mdh-btn mdh-alt" href="{url(OUTILS[k][0])}">{E(OUTILS[k][1])}</a></p></section>' for k, t, x in quand)
    body = f"""<div class="mdh-w"><div class="mdh-art">
{crumbs([("Outils", None)])}
<header class="mdh-head"><span class="mdh-badge">Outils gratuits</span>
<h1>Outils gratuits : délais MDPH, AAH, AEEH et renouvellement</h1>
<p class="mdh-chapo">Quatre calculs simples, faits à partir des règles officielles. Tout se calcule dans votre navigateur : vos réponses ne sont ni envoyées ni enregistrées.</p>
{trust(None, outil=True)}
</header>
<ul class="mdh-grid2">{tuiles_outils()}</ul>
{blocs}
<section aria-labelledby="limites"><h2 id="limites">Ce que ces outils ne font pas</h2>
<p>Ils donnent une estimation ou des dates indicatives. La décision revient à la MDPH, et le montant à la CAF ou à la MSA. Pour un calcul complet de vos droits, le <a href="https://www.mesdroitssociaux.gouv.fr/" rel="noopener" target="_blank">simulateur officiel mesdroitssociaux.gouv.fr</a> reste la référence. Les règles sont expliquées dans <a href="/#guides">les guides pas à pas</a>.</p></section>
</div></div>"""
    schema = [{"@context": "https://schema.org", "@type": "ItemList", "name": "Outils gratuits de mes-droits-handicap.fr", "url": DOMAIN + path,
               "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": v[2], "url": DOMAIN + url(v[0])} for i, v in enumerate(OUTILS.values())]},
              bc_schema([("Outils", path)])]
    return path, page("Outils gratuits : délais MDPH, AAH, AEEH, renouvellement", "Quatre outils gratuits : date de refus implicite de la MDPH, renouvellement, simulateur AAH et calcul de l'AEEH. Calcul dans votre navigateur.",
                      path, body, schema, "accueil", "outils", None, "index-outils")


# --------------------------------------------------------------------------- accueil
def hero_kit():
    """Bloc offre en haut de l'accueil, au-dessus de la ligne de flottaison (22/11/2026)."""
    if not KIT.actif(PRODUIT): return ""
    return (f'<div class="mdh-hkit"><p class="mdh-lab">Kit dossier MDPH 2026</p><p class="mdh-hkit-t">Le kit pour monter votre dossier MDPH sans erreur</p>'
            '<ul><li>Les <b>checklists des pièces</b>, selon votre situation</li><li>Le <b>Cerfa 15692 expliqué</b> section par section</li>'
            '<li>Le <b>projet de vie</b> : méthode, grilles et exemples</li></ul>'
            f'<div class="mdh-hkit-pay"><p class="mdh-hkit-p">19 €<small>PDF de 26 pages</small></p><a class="mdh-btn mdh-sun" href="/{KIT.SLUG}/">Voir le kit</a></div>'
            '<p class="mdh-hkit-s">Paiement sécurisé par Stripe · téléchargement immédiat · remboursé sous 14 jours sur simple demande</p></div>')


def accueil():
    gn = DP.nat("global")
    rows = DP.classement_rows()
    data = [[r["nom"] + (" (" + r["code"] + ")" if r["code"].isdigit() else ""), r["code"], round(r["global"], 1), r["lien"] or "", DP.de(r["nom"])] for r in sorted(rows, key=lambda r: r["nom"])]
    dj = '<script type="application/json" id="mdh-deps">' + json.dumps(data, ensure_ascii=False) + "</script>"
    tools = tuiles_outils()
    guides = "".join(f'<li><a class="mdh-tile" href="{url(s)}"><b>{E(v[0])}</b><span>{E(CONTENUS[s].get("description", ""))}</span></a></li>' for s, v in GUIDES.items() if s in CONTENUS)
    deps = "".join(f'<li><a href="/delais-mdph/{DP.DEPS[c]["slug"]}/">{E(DP.DEPS[c]["nom"])} ({c})</a></li>' for c in sorted(DP.PAGES_DEP, key=lambda c: DP.DEPS[c]["nom"]))
    ico_s = '<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 20 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'

    def find(fid, ph):
        return (f'<form class="mdh-find" data-go action="/delais-mdph/" method="get" role="search"><div class="mdh-sfield">{ico_s}'
                f'<input id="{fid}" type="search" autocomplete="off" placeholder="{E(ph)}"><button class="mdh-btn mdh-find-go" type="submit">Voir le délai</button></div>'
                f'<ul class="mdh-sugg" hidden></ul></form><div class="mdh-find-res" aria-live="polite" hidden></div>')
    T = ["2025T1", "2025T2", "2025T3", "2025T4", "2026T1", "2026T2"]
    sv = [DP.nat("global", t) for t in T]
    lo, hi_ = min(sv), max(sv)
    sp = " ".join(f"{6 + i * 37.6:.1f},{36 - 28 * (v - lo) / ((hi_ - lo) or 1):.1f}" for i, v in enumerate(sv))
    body = f"""<section class="mdh-hero"><div class="mdh-w mdh-hgrid">
<div class="mdh-hcopy"><span class="mdh-badge">AAH · PCH · AEEH · RQTH · CMI</span>
<h1>Vos droits liés au handicap : délais des MDPH, outils et démarches</h1>
{hero_kit()}
<p class="mdh-lead">Le délai réel de votre MDPH, une estimation de votre AAH, les dates à ne pas manquer et des guides pas à pas. Gratuit, sans inscription, avec les chiffres officiels de la CNSA, de la CAF et de service-public.</p>
<div class="mdh-hsearch"><label for="hq" class="mdh-hs-l">Votre département</label>{find("hq", "Nom ou numéro, par exemple Nord ou 59")}</div>
<p class="mdh-btns"><a class="mdh-btn" href="/delais-mdph/">Voir le délai de ma MDPH</a><a class="mdh-btn mdh-sun" href="/outils/simulateur-aah/">Estimer mon AAH en 1 minute</a><a class="mdh-btn mdh-alt" href="/dossier-mdph/">Préparer mon dossier pas à pas</a></p>
{trust(None, outil=True)}
</div>
<div class="mdh-hvis"><figure>{img_html("accueil", "(max-width: 860px) 100vw, 520px", True)}</figure>
<div class="mdh-float mdh-float-a" aria-hidden="true"><p class="mdh-lab">Délai moyen national</p><p class="mdh-fl-n"><b>{DP.fr(gn)}</b> mois</p>
<svg viewBox="0 0 200 42" width="200" height="42"><polyline points="{sp}" fill="none" stroke="#1f3b63" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><circle cx="194" cy="{36 - 28 * (sv[-1] - lo) / ((hi_ - lo) or 1):.1f}" r="3.6" fill="#e8b06a"/></svg>
<p class="mdh-fl-s">{DP.tlab(DP.DERNIER)}, baromètre CNSA</p></div>
<div class="mdh-float mdh-float-b" aria-hidden="true"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#4f8a7b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/></svg>Rien n'est enregistré</div>
</div>
</div></section>
<div class="mdh-w">
<section class="mdh-sec" aria-labelledby="h-delai"><h2 id="h-delai">Combien de temps va attendre votre dossier ?</h2>
<p>Au {DP.tlab(DP.DERNIER)}, les MDPH ont mis en moyenne <b>{DP.mois_txt(gn)}</b> pour répondre, mais de {DP.mois_txt(rows[-1]['global'])} à {DP.mois_txt(rows[0]['global'])} selon le département. Choisissez le vôtre :</p>
<div class="mdh-hsearch mdh-hsearch-2">{find("hq2", "Tapez le nom ou le numéro de votre département")}</div>
{urgences(["4mois", "2mois", "6mois"])}
</section>
<section class="mdh-sec" id="outils" aria-labelledby="h-outils"><h2 id="h-outils">Les outils</h2>
<p>Tout se calcule dans votre navigateur : vos réponses ne sont ni envoyées ni enregistrées.</p>
<ul class="mdh-grid2">{tools}</ul>
<p><a href="/outils/">Voir tous les outils et quand les utiliser</a></p></section>
{produit_slot()}
<section class="mdh-sec" id="guides" aria-labelledby="h-guides"><h2 id="h-guides">Les guides pas à pas</h2>
<ul class="mdh-grid3">{guides}</ul></section>
<section class="mdh-sec" aria-labelledby="h-deps"><h2 id="h-deps">Les MDPH en détail</h2>
<p>Délais sur six trimestres, droits à vie, allocataires de l'AAH et de l'AEEH, coordonnées officielles. Les autres départements figurent dans <a href="/delais-mdph/">le classement complet</a>.</p>
<ul class="mdh-deps">{deps}</ul></section>
<section class="mdh-sec mdh-qui" aria-labelledby="h-qui"><h2 id="h-qui">À qui sert ce site</h2>
<p>Aux personnes en situation de handicap, aux parents d'un enfant handicapé et aux proches qui les aident. Il explique les règles et donne des repères chiffrés ; il ne remplace pas la MDPH, qui reçoit les dossiers gratuitement, ni un conseil personnalisé. <a href="/a-propos/">Qui écrit ce site et comment il est financé</a>.</p></section>
</div>
{dj}"""
    schema = [{"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": DOMAIN + "/", "inLanguage": "fr-FR", "publisher": {"@type": "Organization", "name": SITE}}, org(),
              {"@context": "https://schema.org", **person(), "jobTitle": "Auteur et éditeur de mes-droits-handicap.fr"}]
    return page("Droits handicap : délais des MDPH, AAH, PCH, aides (2026)", "Délai de votre MDPH, simulateur AAH, calcul de l'AEEH, dates de recours et de renouvellement : vos droits liés au handicap, avec les chiffres officiels.",
                "/", body, schema, "accueil", None, ("delais-mdph", "Voir le délai de ma MDPH"))


# --------------------------------------------------------------------------- pages de confiance
import confiance as CF


def main():
    global FOOTER, CONTENUS
    CONTENUS = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "contenu", "*.json"))):
        d = json.loads(SM.remplir(open(f, encoding="utf-8").read()))   # {{SMIC_MENSUEL}}, {{SEUIL_AAH}}… -> smic.py
        if d.get("slug") in GUIDES: CONTENUS[d["slug"]] = d
    FOOTER = footer()
    for p in glob.glob(os.path.join(OUT, "*")):
        if os.path.basename(p) not in ("img",):
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT, exist_ok=True)

    def write(path, content):
        fp = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" else os.path.join(OUT, "index.html")
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        open(fp, "w", encoding="utf-8").write(content)
    urls = []
    write("/", accueil()); urls.append(("/", MODIFS.get("/", MAJ_DONNEES)))
    path, h = classement(); write(path, h); urls.append((path, MODIFS.get(path, MAJ_DONNEES)))
    for c in DP.PAGES_DEP:
        path, h = page_dep(c); write(path, h); urls.append((path, MODIF_DEPS))
    for s in GUIDES:
        if s in CONTENUS:
            path, h = guide(CONTENUS[s]); write(path, h); urls.append((path, max(CONTENUS[s].get("date_verification", LANCEMENT), MODIFS.get(path, ""))))
    path, h = index_outils(); write(path, h); urls.append((path, MODIFS.get(path, LANCEMENT)))
    for k in OUTILS:
        path, h = page_outil(k); write(path, h); urls.append((path, OP.PAGES[k]["verif"]))
    for s, (t, dsc, h1, b, schema_extra) in CF.pages(SITE, AUTEUR, DOMAIN, KIT.actif(PRODUIT), CLARITY_ID, bool(GOATCOUNTER)).items():
        body = f'<div class="mdh-w mdh-prose">{crumbs([(h1, None)])}<h1>{E(h1)}</h1>{b}</div>'
        sch = [bc_schema([(h1, url(s))])] + schema_extra
        write(url(s), page(t, dsc, url(s), body, sch, "accueil")); urls.append((url(s), MODIFS.get(url(s), LANCEMENT)))
    if KIT.actif(PRODUIT):   # Kit dossier MDPH : rien de tout cela n'existe tant que PRODUIT vaut None
        KIT.extrait(ROOT, OUT)
        path, h = KIT.page_vente(sys.modules[__name__], KIT.apercus(ROOT, OUT)); write(path, h); urls.append((path, MAJ_DONNEES))
        path, h = KIT.page_cgv(sys.modules[__name__]); write(path, h); urls.append((path, KIT.CGV_DATE))
        path, h = KIT.page_merci(sys.modules[__name__]); write(path, h)   # noindex, hors sitemap, jamais liée
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(
        page("Page introuvable | Mes droits handicap", "Cette page n'existe pas ou a été déplacée.", "/404.html",
             '<div class="mdh-w mdh-prose"><h1>Page introuvable</h1><p>Cette adresse n\'existe pas ou plus. Vous cherchiez peut-être :</p><ul><li><a href="/delais-mdph/">le délai de votre MDPH</a></li><li><a href="/outils/simulateur-aah/">le simulateur AAH</a></li><li><a href="/dossier-mdph/">le guide du dossier MDPH</a></li><li><a href="/">l\'accueil</a></li></ul></div>',
             [], "accueil", None, None, "systeme", "noindex"))
    open(os.path.join(OUT, "style.css"), "w", encoding="utf-8").write(CSS)
    shutil.copy(os.path.join(ROOT, "_build", "outils.js"), os.path.join(OUT, "outils.js"))
    os.makedirs(os.path.join(OUT, "fonts"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "_build", "fonts", "lexend-latin.woff2"), os.path.join(OUT, "fonts", "lexend-latin.woff2"))
    shutil.copy(os.path.join(ROOT, "_build", "fonts", "fraunces-latin.woff2"), os.path.join(OUT, "fonts", "fraunces-latin.woff2"))
    open(os.path.join(OUT, "site.js"), "w", encoding="utf-8").write(SITE_JS)
    os.makedirs(os.path.join(OUT, "donnees"), exist_ok=True)
    open(os.path.join(OUT, "donnees", f"delais-mdph-{DP.DERNIER.lower()}.csv"), "w", encoding="utf-8").write(csv_delais())
    open(os.path.join(OUT, "favicon.svg"), "w", encoding="utf-8").write(LOGO.replace('width="38" height="38" ', 'xmlns="http://www.w3.org/2000/svg" ').replace(' aria-hidden="true"', ""))
    open(os.path.join(OUT, "CNAME"), "w").write("mes-droits-handicap.fr\n")
    open(os.path.join(OUT, INDEXNOW + ".txt"), "w").write(INDEXNOW)
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    open(os.path.join(OUT, "googlea92d4a2fb22dcdea.html"), "w").write("google-site-verification: googlea92d4a2fb22dcdea.html")
    BOTS_IA = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User",
               "Google-Extended", "Applebot-Extended", "Bingbot", "CCBot", "Meta-ExternalAgent", "MistralAI-User", "DuckAssistBot"]
    robots = "# Robots des moteurs de recherche et des assistants IA : bienvenus (citation des guides avec un lien).\n"
    robots += "".join(f"User-agent: {b}\nAllow: /\n\n" for b in BOTS_IA)
    robots += "User-agent: *\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\nAllow: /\n\n"
    robots += f"Sitemap: {DOMAIN}/sitemap.xml\n"
    open(os.path.join(OUT, "robots.txt"), "w").write(robots)
    sm = "".join(f"<url><loc>{DOMAIN}{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    llms = [f"# {SITE} (mes-droits-handicap.fr)", "",
            "> Site d'information indépendant sur les droits liés au handicap en France : délais des MDPH par département (baromètre CNSA), AAH, PCH, AEEH, RQTH, carte mobilité inclusion, recours et renouvellement. Chiffres officiels datés et sourcés sur chaque page. Auteur : Louis Lardeux.", "",
            "## Données", "", f"- [Délais des MDPH en 2026, classement]({DOMAIN}/delais-mdph/): délai moyen par territoire au {DP.tlab(DP.DERNIER)}, CSV : {DOMAIN}/donnees/delais-mdph-{DP.DERNIER.lower()}.csv"]
    llms += [f"- [MDPH {DP.de(DP.DEPS[c]['nom'])}]({DOMAIN}/delais-mdph/{DP.DEPS[c]['slug']}/)" for c in DP.PAGES_DEP]
    llms += ["", "## Outils (calcul dans le navigateur, rien n'est enregistré)", "", f"- [Tous les outils]({DOMAIN}/outils/)"] + [f"- [{v[2]}]({DOMAIN}{url(v[0])}): {v[3]}" for v in OUTILS.values()]
    llms += ["", "## Guides", ""] + [f"- [{strip(CONTENUS[s]['h1'])}]({DOMAIN}{url(s)}): {strip(CONTENUS[s].get('chapo', ''))}" for s in GUIDES if s in CONTENUS]
    llms += ["", "## Le site", "", f"- [À propos]({DOMAIN}/a-propos/)", f"- [Méthode et sources]({DOMAIN}/methode-et-sources/)"]
    if KIT.actif(PRODUIT): llms += [f"- [Kit dossier MDPH, guide pratique payant (19 €)]({DOMAIN}/{KIT.SLUG}/)", f"- [Conditions de vente]({DOMAIN}/{KIT.CGV}/)"]
    llms += [""]
    open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8").write("\n".join(llms))
    print(len(CONTENUS), "guides,", len(urls), "URL ->", OUT)


if __name__ == "__main__":
    main()
