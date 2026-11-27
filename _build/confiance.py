"""Pages de confiance : à propos, méthode et sources, mentions légales, confidentialité.
Éditeur : mêmes informations que les mentions légales de aidermesparents.fr (même éditeur), adaptées au domaine."""
import departements as DP

CONTACT = "contact@mes-droits-handicap.fr"
# Téléphone de l'éditeur, exigé par la LCEN (art. 6 III) pour une personne physique : À COMPLÉTER PAR LOUIS.
# None = la ligne n'est pas affichée (rien d'incomplet n'apparaît en ligne). Exemple : TEL_EDITEUR = "06 00 00 00 00"
TEL_EDITEUR = "07 56 80 68 54"
# Téléphone de GitHub, Inc. : numéro de l'équipe commerciale, seul numéro publié par GitHub (ancienne documentation
# docs.github.com, Enterprise Server 3.0, « call +1 (877) 448-4820 »). GitHub précise ne pas faire de support par téléphone.
TEL_HEBERGEUR = "+1 877 448 4820"


def pages(SITE, AUTEUR, DOMAIN, kit=False, clarity=None, gc=False):
    """kit=True seulement quand le Kit dossier MDPH est en vente (PRODUIT renseigné dans build.py) : sinon les textes restent identiques."""
    S = DP.SRC
    mail = f'<a href="mailto:{CONTACT}">{CONTACT}</a>'
    sources_li = "".join(f'<li><b>{s["titre"]}</b> : {s["periode"] + ", " if s.get("periode") else ""}{s["publie"]}. <a href="{s["url"]}" rel="noopener" target="_blank">Lien</a></li>' for s in S.values())
    FIN = "<p>Aujourd'hui, le site n'a aucune source de revenus : pas de publicité, pas d'affiliation, rien à vendre. Il est possible qu'à l'avenir un service payant optionnel soit proposé (par exemple une aide à l'organisation de son dossier) ; il ne le sera qu'après relecture par un avocat, il sera clairement présenté comme tel et ne changera jamais le contenu gratuit des guides ni des outils.</p>"
    FIN_KIT = ("<p>Le site n'affiche pas de publicité et ne fait pas d'affiliation. Il est financé par la vente d'un guide pratique optionnel, le <a href=\"/kit-dossier-mdph/\">Kit dossier MDPH</a> (19 €), "
               "clairement présenté comme payant. Les guides et les outils du site restent gratuits et complets, et le dépôt du dossier est toujours gratuit auprès de votre MDPH.</p>")
    apropos = f"""<div class="mdh-author mdh-author-xl"><img class="mdh-ava" src="/img/louis-lardeux.jpg" width="96" height="96" alt="Photo de {AUTEUR}"><span><b>{AUTEUR}</b><br>Auteur et éditeur de mes-droits-handicap.fr<br><a href="https://www.linkedin.com/in/louis-lardeux-96b600254/" rel="noopener me" target="_blank">Mon profil LinkedIn</a></span></div>
<p><b>Ce site n'est pas un service public.</b> Il n'est rattaché à aucune MDPH, à aucun département, à la CAF ni à la CNSA. Toutes les démarches sont gratuites sur le site officiel de votre MDPH et sur <a href="https://mdphenligne.cnsa.fr/" rel="noopener" target="_blank">mdphenligne.cnsa.fr</a> : personne n'a besoin de payer un intermédiaire pour déposer un dossier.</p>
<h2>Mon histoire</h2><p>Je m'appelle Louis Lardeux, entrepreneur dans la métropole lilloise. J'ai lancé mes-droits-handicap.fr après un constat qui m'a marqué : les délais des MDPH sont publiés chaque trimestre par la CNSA, mais dans un tableur que presque personne ne lit. Pendant ce temps, des familles attendent des mois une réponse, sans savoir si c'est normal, ni à partir de quand elles peuvent agir.</p><p>J'ai voulu rendre ces chiffres utiles : le délai réel de votre MDPH, la date à partir de laquelle l'absence de réponse vaut refus, les recours possibles, et des guides qui expliquent l'AAH, la PCH ou la RQTH sans jargon. Le tout au même endroit, lisible sur un téléphone, en quelques minutes.</p><p>Mon engagement : des sources officielles citées et datées sous chaque bloc, des pages mises à jour à chaque publication de la CNSA, et des guides qui restent gratuits. Si ce site vous aide à faire avancer un dossier, il a rempli son rôle.</p>
<h2>Pourquoi ce site</h2>
<p>Les règles existent et les chiffres sont publics, mais ils sont éparpillés : les délais des MDPH dans un tableur de la CNSA, les montants sur service-public, les allocataires sur le portail de la CAF, les formulaires sur un quatrième site. Quand on est fatigué par la maladie, par le handicap d'un enfant ou par des mois d'attente, cet éparpillement coûte cher. Ce site rassemble ces informations, les vérifie et les explique simplement.</p>
<h2>Qui écrit</h2>
<p>Je m'appelle {AUTEUR}. Je ne suis ni travailleur social, ni avocat, ni médecin. Mon travail consiste à lire les textes et les données officielles, à les vérifier une par une et à les rendre compréhensibles. Les guides donnent une information générale : ils n'analysent jamais une décision individuelle et ne rédigent pas de recours à la place de quelqu'un. Pour une situation précise, les associations (APF France handicap, UNAFAM, Unapei et bien d'autres), les points-justice et les avocats sont là pour ça, et les pages le rappellent.</p>
<h2>Comment les pages sont vérifiées</h2>
<ul><li>Uniquement des <b>sources officielles</b> : service-public.gouv.fr, monparcourshandicap.gouv.fr, Légifrance, CNSA, CAF, DREES, Insee. Elles sont citées sous chaque bloc et en bas de chaque page, avec leur date.</li>
<li>Une <b>date de vérification</b> sur chaque page. Les montants sont revus à chaque revalorisation (en général au 1er avril pour l'AAH et l'AEEH).</li>
<li>Les <b>outils</b> reprennent les barèmes officiels ; chacun a été vérifié à la main sur plusieurs cas avant publication.</li>
<li>Les <b>délais par département</b> sont mis à jour à chaque publication trimestrielle du baromètre de la CNSA. Détail : <a href="/methode-et-sources/">méthode et sources</a>.</li></ul>
<h2>Comment le site est financé</h2>
{FIN_KIT if kit else FIN}
<h2>Vos données</h2>
<p>Les outils calculent tout dans votre navigateur : vos réponses, qui peuvent concerner votre santé, ne sont ni envoyées ni enregistrées. Détail : <a href="/confidentialite/">confidentialité</a>.</p>
<h2>Une erreur ?</h2>
<p>Si une information vous semble fausse ou dépassée, écrivez à {mail} en indiquant la page. Je vérifie et je corrige. N'envoyez pas de document médical ni d'information sur votre dossier : je ne peux pas analyser de situation individuelle.</p>"""
    methode = f"""<p>Chaque chiffre affiché sur ce site vient d'une source publique identifiée, datée et citée sous le bloc où il apparaît. Quand une donnée manque pour un département, la ligne ou la phrase n'apparaît pas : rien n'est estimé ni complété.</p>
<h2>Les jeux de données utilisés</h2>
<ul>{sources_li}</ul>
<h2>Les délais des MDPH</h2>
<p>Le baromètre des MDPH de la CNSA publie chaque trimestre, pour chaque MDPH, le délai moyen de traitement des demandes en mois : toutes demandes, demandes concernant des enfants, des adultes, l'AAH et la PCH. Il est calculé à partir des systèmes d'information des MDPH. Quelques points de lecture :</p>
<ul><li>C'est une <b>moyenne</b> sur les décisions du trimestre : un dossier peut aller plus vite ou plus lentement.</li>
<li>Quand une MDPH n'a pas transmis ses chiffres (mention « en cours » dans le fichier), la case est notée « n.c. » et le département n'est pas classé pour ce critère.</li>
<li>La CNSA publie une ligne pour la Corse et une pour l'Alsace, et deux lignes pour le Rhône (Métropole de Lyon, Rhône hors Métropole) : le classement suit ce découpage.</li></ul>
<h2>Les autres indicateurs</h2>
<ul><li><b>Droits à vie</b> : part des AAH (taux d'au moins 80 %), RQTH et cartes mobilité inclusion attribuées sans limitation de durée (CNSA).</li>
<li><b>Allocataires</b> : nombre de personnes bénéficiaires de l'AAH et de l'AEEH versées par la CAF (hors MSA), et répartition de l'AAH selon le taux d'incapacité (CNAF).</li>
<li><b>PCH</b> : personnes ayant un droit ouvert au 31 décembre 2024 (DREES, enquête Aide sociale).</li>
<li><b>Satisfaction</b> : enquête nationale « Ma MDPH, mon avis compte ». Quand moins de 100 personnes ont répondu dans un département, la page le signale.</li>
<li><b>Coordonnées</b> : annuaire officiel de l'administration ; les horaires peuvent changer, vérifiez avant de vous déplacer.</li>
<li><b>Ratios « pour 1 000 habitants »</b> : calculés avec les estimations de population de l'Insee au 1er janvier 2026.</li></ul>
<h2>Mise à jour</h2>
<p>Les données sont relevées par un script public dans le dépôt du site (<code>_build/donnees.py</code>), relancé à chaque nouvelle publication : baromètre CNSA chaque trimestre, données CAF chaque mois, montants des prestations à chaque revalorisation. Dernier relevé : 15/11/2026. Le classement est téléchargeable en CSV depuis <a href="/delais-mdph/">la page des délais</a>.</p>
<h2>Les textes et les montants</h2>
<p>Les montants (AAH, AEEH, PCH), les délais légaux (4 mois, 2 mois, 6 mois) et les formulaires (Cerfa 15692*01 et 15695*01) sont vérifiés sur service-public.gouv.fr, monparcourshandicap.gouv.fr, la CNSA et Légifrance. Chaque guide liste ses sources avec leur date.</p>"""
    tel_ed = f", téléphone : {TEL_EDITEUR}" if TEL_EDITEUR else ""
    mentions = f"""<h2>Éditeur</h2><p>Louis Lardeux, entrepreneur individuel (micro-entreprise), SIREN 999 443 880, 63 rue Dostoïevski, A 307, 06560 Valbonne Sophia Antipolis. Contact : {mail}{tel_ed}.</p>
<p>Directeur de la publication : Louis Lardeux.</p>
<h2>Hébergement</h2><p>GitHub Pages, service de GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis. Téléphone (standard commercial) : {TEL_HEBERGEUR}. Contact : <a href="https://support.github.com/contact" rel="noopener" target="_blank">support.github.com/contact</a>.</p>
<h2>Nature du site</h2><p>mes-droits-handicap.fr est un site d'information indépendant. Il n'est pas un service public et n'est rattaché à aucune MDPH, collectivité, caisse ou administration. Les démarches sont gratuites auprès de la MDPH et sur mdphenligne.cnsa.fr. Les contenus ont une vocation d'information générale : ils ne constituent ni un conseil juridique ni un avis médical, et ne remplacent pas la décision de l'organisme compétent, qui seul fait foi.</p>
<h2>Données publiques réutilisées</h2><p>Les données de la CNSA, de la CNAF, de la DREES, de l'Insee et de l'annuaire de l'administration sont réutilisées dans le respect de leurs conditions (Licence Ouverte d'Etalab), avec mention de la source et de la date.</p>
<h2>Illustrations</h2><p>Les photos d'illustration sont générées par intelligence artificielle. Elles ne représentent pas de personnes réelles et ne sont pas des témoignages.</p>"""
    ACHAT = ("<h2>Achat du Kit dossier MDPH</h2><p>Le paiement du kit est traité par Stripe, sur sa propre page : nous ne voyons pas votre numéro de carte. Stripe nous transmet votre adresse e-mail, "
             "votre nom et le montant payé, conservés pour la comptabilité et pour vous renvoyer le kit si besoin. Aucune information de santé n'est demandée. "
             "Après le paiement, la page de téléchargement garde sur votre appareil (stockage local du navigateur) l'identifiant de la commande, pour que vous puissiez y revenir ; rien n'est envoyé.</p>")
    if clarity:
        audience = ("<h2>Mesure d'audience</h2><p>Sur les pages d'information (guides, délais), et seulement si vous cliquez sur « Accepter » dans le bandeau, "
                    "Microsoft Clarity mesure la navigation (clics, défilement) pour améliorer les guides. Tout le texte des pages est masqué et aucune saisie n'est enregistrée. "
                    "Clarity n'est jamais chargé sur les pages des outils. Si vous refusez, rien n'est chargé. Votre choix est gardé 6 mois dans votre navigateur.</p>")
        intro = "<p>Ce site n'affiche aucune publicité et ne vous demande aucune donnée pour être consulté. Il ne dépose de cookie de mesure d'audience que si vous l'acceptez.</p>"
    elif gc:
        audience = ("<h2>Mesure d'audience</h2><p>Sur les pages d'information (guides, délais), un compteur de visites, GoatCounter, compte les pages vues, "
                    "le site d'où vous venez, le type d'appareil et le pays. Il ne dépose aucun cookie, n'enregistre pas votre adresse IP en clair et ne permet pas de vous identifier : "
                    "aucun accord n'est donc nécessaire. Il n'est jamais chargé sur les pages des outils.</p>")
        intro = "<p>Ce site ne dépose aucun cookie, n'affiche aucune publicité et ne vous demande aucune donnée pour être consulté.</p>"
    else:
        audience = ("<h2>Mesure d'audience</h2><p>Aujourd'hui, aucune mesure d'audience n'est installée : aucun compteur, aucun outil de statistiques, aucun cookie. "
                    "Si cela change un jour, cette page sera mise à jour avant, et tout outil qui en aurait besoin ne serait chargé qu'avec votre accord.</p>")
        intro = "<p>Ce site ne dépose aucun cookie, n'affiche aucune publicité et ne vous demande aucune donnée pour être consulté.</p>"
    confid = f"""{intro}
<h2>Les outils</h2><p>Les quatre outils (simulateur AAH, calcul de l'AEEH, date de refus implicite, calendrier de renouvellement) fonctionnent entièrement dans votre navigateur. Les informations que vous saisissez, y compris celles qui touchent à votre santé ou à votre handicap, ne sont ni envoyées à un serveur, ni enregistrées, ni mesurées. Aucun script externe n'est chargé sur ces pages. Le rappel d'agenda (.ics) est créé sur votre appareil.</p>
{audience}
{ACHAT if kit else ""}<h2>Polices de caractères</h2><p>Les polices Lexend et Fraunces sont hébergées sur le site lui-même : aucun serveur tiers n'est contacté pour les afficher.</p>
<h2>Hébergement et journaux techniques</h2><p>Le site est hébergé par GitHub Pages. Comme tout hébergeur, GitHub enregistre dans ses journaux techniques l'adresse IP des visiteurs, pour la sécurité et le bon fonctionnement du service. L'éditeur du site n'a pas accès à ces journaux. Détail : <a href="https://docs.github.com/site-policy/privacy-policies/github-privacy-statement" rel="noopener" target="_blank">déclaration de confidentialité de GitHub</a>.</p>
<h2>Vos droits</h2><p>L'éditeur du site ne détient aucune donnée personnelle vous concernant : il n'y a rien à consulter ni à effacer de son côté. Si vous nous écrivez, votre message est conservé dans notre messagerie le temps de vous répondre. Pour toute question : {mail}. Vous pouvez aussi saisir la CNIL.</p>"""
    return {
        "a-propos": ("À propos : qui écrit ce site et son financement", "Qui écrit mes-droits-handicap.fr, comment chaque information est vérifiée, comment le site est financé et ce qu'il n'est pas.", "À propos de ce site", apropos,
                     [{"@context": "https://schema.org", "@type": "AboutPage", "name": "À propos", "url": DOMAIN + "/a-propos/", "mainEntity": {"@type": "Person", "name": AUTEUR, "url": DOMAIN + "/a-propos/", "jobTitle": "Auteur et éditeur de mes-droits-handicap.fr", "image": DOMAIN + "/img/louis-lardeux.jpg", "sameAs": ["https://www.linkedin.com/in/louis-lardeux-96b600254/"]}}]),
        "methode-et-sources": ("Méthode et sources des données | Mes droits handicap", "D'où viennent les délais des MDPH, les chiffres d'allocataires et les montants, à quelle date, avec quelles limites.", "Méthode et sources : d'où viennent les chiffres", methode, []),
        "mentions-legales": ("Mentions légales | Mes droits handicap", "Mentions légales du site mes-droits-handicap.fr.", "Mentions légales", mentions, []),
        "confidentialite": ("Confidentialité | Mes droits handicap", "Aucun cookie, outils calculés dans votre navigateur : vos réponses ne sont ni envoyées ni enregistrées.", "Confidentialité", confid, []),
    }
