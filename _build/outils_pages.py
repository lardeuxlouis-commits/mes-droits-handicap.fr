"""Textes et paramètres des 4 pages outils. Les paramètres sont injectés dans la page (window.MDH_PARAMS) :
outils.js ne fait aucune requête réseau."""
import json
import departements as DP

VERIF = "2026-11-15"

# Paramètres officiels (sources en bas de chaque page outil). À revoir au 1er avril (revalorisation AAH et AEEH).
PARAMS = {
    "trimestre": DP.tlab(DP.DERNIER),
    "aah": {
        "max": 1041.59, "date": "1er avril 2026",       # service-public F12242
        "majEnfant": 0.5,                               # plafond majoré de 50 % par enfant à charge
        "smicBrut": 1867.02, "seuilPart": 0.3,          # D821-9 : seuil = 30 % du Smic brut mensuel (12,31 €/h x 151,67 h), soit 560,11 €
        "ab1": 0.8, "ab2": 0.4,                         # 80 % jusqu'au seuil, 40 % au-delà
        "abNet": 0.1,                                   # personnes sans activité : revenus de l'année N-2, abattement forfaitaire de 10 %
        "anneeRef": "2024",
    },
    "aeeh": {
        "base": 153.01, "date": "1er avril 2026",
        "comp": [114.76, 310.80, 439.91, 681.71, 871.26, 1298.44],
        "maj": [0, 62.16, 86.07, 272.55, 349.06, 511.63],
        "s1": 267.77, "s2": 463.82, "s3": 592.92, "s3b": 282.11, "s4": 834.72, "s4b": 394.82, "s4c": 523.92, "s5": 342.55,
    },
}


def delais_json():
    out = {}
    for c in DP.TERR:
        d = DP.DEPS[c]
        g = d["delais"]["global"].get(DP.DERNIER)
        out[c] = {"n": d["nom"] + (f" ({c})" if c.isdigit() else ""), "g": round(g, 1), "de": DP.de(d["nom"])}
    return '<script type="application/json" id="mdh-delais">' + json.dumps(out, ensure_ascii=False) + "</script>"


def params_js():
    return "<script>window.MDH_PARAMS=" + json.dumps(PARAMS, ensure_ascii=False) + ";</script>"


SP = "https://www.service-public.gouv.fr/particuliers/vosdroits/"
gn = DP.fr(DP.nat("global"))
n_plus4 = sum(1 for c in DP.TERR if DP.DEPS[c]["delais"]["global"][DP.DERNIER] > 4)
A = PARAMS["aah"]; AE = PARAMS["aeeh"]


def eur(x):
    return f"{x:,.2f}".replace(",", " ").replace(".", ",") + " €"


PAGES = {
    "delai": {
        "title": "Refus implicite MDPH : calculez la date des 4 mois",
        "desc": "Sans réponse de la MDPH 4 mois après le dépôt, la demande vaut refus. Calculez cette date, vos délais de recours et la décision attendue chez vous.",
        "h1": "4 mois sans réponse de la MDPH : calculez la date du refus implicite",
        "chapo": f"Quand la MDPH ne répond pas dans les <b>4 mois</b> qui suivent le dépôt d'un dossier complet, la demande est considérée comme refusée. Ce refus implicite ouvre un délai de <b>2 mois</b> pour contester. Indiquez votre date de dépôt : l'outil calcule ces dates et, si vous le souhaitez, la date de décision attendue selon le délai moyen de votre MDPH.",
        "img": "demarches", "urg": ["4mois", "2mois", "delai"],
        "avant": delais_json() + params_js(),
        "corps": f"""<section aria-labelledby="regle"><h2 id="regle">D'où vient la règle des 4 mois ?</h2>
<p>Le code de l'action sociale et des familles prévoit que le silence gardé par la commission des droits et de l'autonomie (CDAPH) pendant 4 mois vaut décision de rejet. Le point de départ est la date de dépôt du dossier <b>complet</b> : si la MDPH vous a demandé une pièce manquante, c'est souvent la date de réception de cette pièce qui compte. L'accusé de réception ou le suivi en ligne sur mdphenligne.cnsa.fr vous donne cette date.</p>
<p>Ce refus implicite n'est pas une décision sur le fond. La MDPH continue d'instruire votre dossier et peut rendre sa décision après les 4 mois ; dans les faits, c'est ce qui arrive le plus souvent. Mais la date compte : elle fait partir le délai pour contester, et elle donne un argument concret pour relancer.</p></section>
<section aria-labelledby="chiffres"><h2 id="chiffres">Combien de MDPH dépassent 4 mois ?</h2>
<p>Au {DP.tlab(DP.DERNIER)}, le délai moyen national est de {gn} mois et <b>{n_plus4} territoires</b> dépassent 4 mois en moyenne, d'après le baromètre de la CNSA. Dans ces départements, une partie importante des dossiers atteint la date du refus implicite avant d'être tranchée. <a href="/delais-mdph/">Le classement des délais</a> donne le chiffre de chaque MDPH.</p></section>
<section aria-labelledby="ensuite"><h2 id="ensuite">Que faire une fois la date passée ?</h2>
<ol class="mdh-steps"><li>Vérifiez l'état de votre dossier (espace en ligne de la MDPH, téléphone, courriel) : il est peut-être en attente d'une pièce.</li>
<li>Relancez par écrit en rappelant la date de dépôt et la date des 4 mois : <a href="/dossier-mdph-trop-long/">comment relancer et signaler une urgence</a>.</li>
<li>Si l'attente vous met en difficulté, vous pouvez contester le refus implicite par un recours amiable (RAPO) dans les 2 mois : <a href="/recours-mdph/">contester une décision de la MDPH</a>.</li></ol>
<p class="mdh-note">Ce site donne une information générale. Pour une situation précise, une association de personnes handicapées, un point-justice ou un avocat peut vous accompagner.</p></section>""",
        "faq": [("Le silence de la MDPH vaut-il refus ?", "Oui : au bout de 4 mois sans décision après le dépôt d'un dossier complet, la demande est considérée comme rejetée. La MDPH peut toutefois statuer ensuite, et c'est souvent ce qui se passe."),
                ("À partir de quand comptent les 4 mois ?", "À partir du dépôt du dossier complet. Si une pièce manquait, le délai part en général de sa réception. Gardez l'accusé de réception ou la capture de votre suivi en ligne."),
                ("Combien de temps pour contester un refus implicite ?", "2 mois à partir de la date du refus implicite, par un recours administratif préalable (RAPO) adressé à la MDPH. Si la MDPH rend ensuite une décision explicite, un nouveau délai de 2 mois court à partir de sa notification."),
                ("Mes droits sont-ils coupés pendant l'attente ?", "Pour un renouvellement, la CAF peut verser une avance d'AAH et la demande prolonge la RQTH le temps de la décision. Pour une première demande, rien n'est versé avant la décision, mais l'AAH, l'AEEH et la PCH sont ouvertes à partir de la date de dépôt si elles sont accordées.")],
        "suite": '<li><a href="/delais-mdph/">Délais des MDPH par département</a></li><li><a href="/dossier-mdph-trop-long/">Dossier sans réponse : que faire</a></li><li><a href="/recours-mdph/">Contester une décision</a></li><li><a href="/outils/fin-de-droits-mdph/">Calendrier de renouvellement</a></li>',
        "sources": [("Service-public.fr, formulaire de demande à la MDPH (Cerfa 15692), délai de 4 mois", SP + "R19993"),
                    ("CNSA, baromètre des MDPH", "https://www.cnsa.fr/donnees/barometre-des-mdph")],
        "verif": VERIF,
    },
    "fin": {
        "title": "Fin de droits MDPH : votre date de renouvellement",
        "desc": "Date de fin de vos droits MDPH : l'outil donne quand redéposer (6 mois avant), quand voir le médecin, et crée un rappel pour votre agenda.",
        "h1": "Fin de droits MDPH : votre calendrier de renouvellement",
        "chapo": "Pour éviter une coupure de l'AAH, de la PCH, de l'AEEH ou de la carte mobilité inclusion, la demande de renouvellement est à déposer <b>6 mois avant</b> la date de fin des droits (4 mois au moins pour la RQTH), comme le recommandent les sites officiels, avec un certificat médical de moins d'un an. Indiquez la date qui figure sur votre notification : l'outil calcule votre calendrier et crée un rappel pour votre agenda.",
        "img": "accueil", "urg": ["6mois", "delai", "4mois"],
        "avant": delais_json() + params_js(),
        "corps": f"""<section aria-labelledby="pourquoi"><h2 id="pourquoi">Pourquoi 6 mois avant ?</h2>
<p>Le délai moyen de traitement est de {gn} mois en France au {DP.tlab(DP.DERNIER)}, et il dépasse 4 mois dans {n_plus4} territoires. Déposer 6 mois avant la fin laisse à la MDPH le temps de décider sans interruption de vos droits. Le formulaire de demande (Cerfa 15692) prévoit d'ailleurs une case pour signaler un renouvellement.</p>
<p>Le certificat médical (Cerfa 15695) doit dater de moins d'un an au moment du dépôt. Prendre rendez-vous environ 3 mois avant la date de dépôt évite de courir après le médecin au dernier moment.</p></section>
<section aria-labelledby="vie"><h2 id="vie">Et si mes droits sont accordés à vie ?</h2>
<p>Depuis 2019, certains droits peuvent être attribués sans limitation de durée quand le handicap n'est pas susceptible d'évoluer favorablement : l'AAH pour un taux d'au moins 80 %, la RQTH, la carte mobilité inclusion mention invalidité, l'AEEH jusqu'aux 20 ans de l'enfant. Dans ce cas, votre notification ne comporte pas de date de fin et vous n'avez rien à redéposer, sauf changement de situation. <a href="/renouvellement-mdph/">Le guide du renouvellement</a> détaille ces cas.</p></section>
<section aria-labelledby="ics"><h2 id="ics">Le rappel d'agenda</h2>
<p>Le bouton « Ajouter le rappel à mon agenda » crée un petit fichier .ics directement dans votre navigateur. Il s'ouvre avec l'agenda de votre téléphone ou de votre ordinateur et vous alerte 30 jours avant la date conseillée de dépôt. Aucune adresse, aucun compte : le fichier reste sur votre appareil.</p></section>""",
        "faq": [("Quand faire le renouvellement de l'AAH ?", "Environ 6 mois avant la date de fin indiquée sur la notification de la MDPH : c'est la recommandation officielle, pas une obligation légale. Vous pouvez déposer plus tôt si votre situation a changé."),
                ("Que se passe-t-il si je dépose en retard ?", "Vos droits peuvent s'interrompre à la date de fin en attendant la nouvelle décision : aucun texte ne prévoit un maintien général. La CAF peut verser une avance d'AAH, sans obligation. Déposez le plus vite possible."),
                ("Faut-il un nouveau certificat médical pour un renouvellement ?", "Oui, un certificat médical (Cerfa 15695) de moins d'un an au dépôt. Si votre état n'a pas changé, le médecin peut le signaler, ce qui simplifie l'évaluation."),
                ("Comment savoir si mes droits sont à vie ?", "La notification de la MDPH l'indique : un droit accordé sans limitation de durée n'a pas de date de fin.")],
        "suite": '<li><a href="/renouvellement-mdph/">Renouveler ses droits</a></li><li><a href="/certificat-medical-mdph/">Le certificat médical</a></li><li><a href="/delais-mdph/">Délai de ma MDPH</a></li><li><a href="/outils/delai-reponse-mdph/">Date de refus implicite</a></li>',
        "sources": [("Monparcourshandicap.gouv.fr, le dépôt du dossier et le traitement de la demande par la MDPH", "https://www.monparcourshandicap.gouv.fr/aides/le-depot-du-dossier-et-le-traitement-de-la-demande-par-la-maison-departementale-des-personnes"),
                    ("Service-public.fr, formulaire de demande à la MDPH (Cerfa 15692)", SP + "R19993"),
                    ("Service-public.fr, certificat médical MDPH (Cerfa 15695)", SP + "R19996"),
                    ("CNSA, baromètre des MDPH", "https://www.cnsa.fr/donnees/barometre-des-mdph")],
        "verif": VERIF,
    },
    "aeeh": {
        "title": "Calcul AEEH 2026 : base, complément et majoration",
        "desc": f"Estimez l'AEEH de votre enfant : {eur(AE['base'])} de base en 2026, plus un complément de la 1re à la 6e catégorie selon vos frais et votre temps de travail.",
        "h1": "Calcul de l'AEEH : base et complément selon votre situation",
        "chapo": f"L'AEEH de base est de <b>{eur(AE['base'])} par mois</b> depuis le {AE['date']}. Selon vos dépenses liées au handicap, votre réduction d'activité ou l'embauche d'une aide, un complément de la 1re à la 6e catégorie s'y ajoute, de {eur(AE['comp'][0])} à {eur(AE['comp'][5])}. Répondez à quatre questions pour estimer la catégorie et le total.",
        "img": "enfant", "urg": ["delai", "4mois", "6mois"],
        "avant": params_js(),
        "corps": f"""<section aria-labelledby="bareme"><h2 id="bareme">Le barème utilisé</h2>
<div class="mdh-tw"><table><thead><tr><th>Catégorie</th><th class="mdh-n">Complément</th><th class="mdh-n">Total avec la base</th><th class="mdh-n">Majoration parent isolé</th></tr></thead><tbody>
{"".join(f'<tr><td>{i + 1}</td><td class="mdh-n">{eur(AE["comp"][i])}</td><td class="mdh-n">{eur(AE["base"] + AE["comp"][i])}</td><td class="mdh-n">{eur(AE["maj"][i]) if AE["maj"][i] else "aucune"}</td></tr>' for i in range(6))}
</tbody></table></div>
<p>Montants mensuels en vigueur depuis le {AE['date']}. La catégorie dépend de trois éléments, et une seule condition suffit : le montant des dépenses liées au handicap, la réduction ou l'arrêt de l'activité d'un parent, ou l'embauche d'une tierce personne (nombre d'heures par semaine). La 6e catégorie suppose en plus des contraintes permanentes de surveillance et de soins.</p></section>
<section aria-labelledby="limites"><h2 id="limites">Ce que l'outil ne peut pas savoir</h2>
<ul><li>C'est la CDAPH, à la MDPH, qui fixe la catégorie après évaluation : l'outil applique les seuils réglementaires, pas l'appréciation de l'équipe.</li>
<li>Seules comptent les dépenses liées au handicap et non remboursées : gardez factures et justificatifs.</li>
<li>Le droit d'option entre le complément d'AEEH et la PCH change le calcul : <a href="/aeeh/">le guide de l'AEEH</a> l'explique.</li></ul></section>""",
        "faq": [("Quel est le montant de l'AEEH en 2026 ?", f"{eur(AE['base'])} par mois pour l'AEEH de base depuis le {AE['date']}, à quoi peut s'ajouter un complément de {eur(AE['comp'][0])} (1re catégorie) à {eur(AE['comp'][5])} (6e catégorie)."),
                ("Comment est déterminée la catégorie du complément ?", "Par les dépenses mensuelles liées au handicap, la réduction ou l'arrêt d'activité d'un parent et le recours à une tierce personne rémunérée. La MDPH apprécie ces éléments sur justificatifs."),
                ("La majoration parent isolé est-elle automatique ?", "Non. Elle s'ajoute à partir de la 2e catégorie quand le parent qui élève seul l'enfant réduit ou arrête son activité, ou embauche une tierce personne."),
                ("L'AEEH dépend-elle des revenus des parents ?", "Non, l'AEEH n'est pas soumise à condition de ressources. Elle est versée par la CAF ou la MSA après décision de la MDPH.")],
        "suite": '<li><a href="/aeeh/">AEEH et compléments</a></li><li><a href="/pch/">PCH : ce qu\'elle finance</a></li><li><a href="/projet-de-vie-mdph/">Le projet de vie, avec exemples</a></li><li><a href="/delais-mdph/">Délai de ma MDPH</a></li>',
        "sources": [("Service-public.fr, Allocation d'éducation de l'enfant handicapé (AEEH), F14809", SP + "F14809"),
                    ("Monparcourshandicap.gouv.fr, AEEH et compléments", "https://www.monparcourshandicap.gouv.fr/aides/lallocation-deducation-de-lenfant-handicape-aeeh")],
        "verif": VERIF,
    },
    "aah": {
        "title": "Simulateur AAH 2026 : estimez votre allocation",
        "desc": f"Estimez votre AAH en 1 minute : {eur(A['max'])} par mois au maximum depuis le {A['date']}, avec ou sans salaire. Calcul local, rien n'est enregistré.",
        "h1": "Simulateur AAH 2026 : estimez votre allocation en 1 minute",
        "chapo": f"L'AAH à taux plein est de <b>{eur(A['max'])} par mois</b> depuis le {A['date']}. Elle diminue quand vous avez d'autres revenus, avec des abattements qui favorisent le travail. Depuis octobre 2023, les revenus du conjoint ne comptent plus. Cet outil donne une estimation ; le simulateur officiel de l'État reste la référence.",
        "img": "travail", "urg": ["delai", "4mois", "6mois"],
        "avant": params_js(),
        "corps": f"""<section aria-labelledby="calcul"><h2 id="calcul">Comment l'estimation est calculée</h2>
<ul><li><b>Vous ne travaillez pas</b> : la CAF retient vos revenus de l'année N-2 (ici {A['anneeRef']}) après un abattement forfaitaire de 10 %. L'AAH complète vos ressources jusqu'au plafond, sans dépasser {eur(A['max'])} par mois.</li>
<li><b>Vous travaillez en milieu ordinaire</b> : vos revenus sont déclarés chaque trimestre. Si vous commencez ou reprenez un travail en touchant déjà l'AAH, le salaire n'est pas compté pendant 6 mois au plus. Votre salaire n'est compté qu'en partie : abattement de {round(A['ab1'] * 100)} % jusqu'à 30 % du Smic brut ({eur(A['smicBrut'] * A['seuilPart'])} par mois), puis de {round(A['ab2'] * 100)} % au-delà.</li>
<li><b>Enfants à charge</b> : le plafond de ressources ({eur(A['max'] * 12)} par an pour une personne) augmente de {round(A['majEnfant'] * 100)} % par enfant.</li>
<li><b>Le conjoint</b> : ses revenus ne sont plus pris en compte depuis le 1er octobre 2023 (déconjugalisation).</li></ul></section>
<section aria-labelledby="exemple"><h2 id="exemple">Exemples</h2>
<aside class="mdh-ex"><p class="mdh-lab">Sans activité</p><p>Revenus de {A['anneeRef']} : 3 000 € (une petite rente). Après abattement de 10 %, 2 700 € sont retenus, soit 225 € par mois. AAH estimée : {eur(A['max'])} moins 225 €, soit {eur(A['max'] - 225)} par mois.</p></aside>
<aside class="mdh-ex"><p class="mdh-lab">Avec un salaire</p><p>Salaire net de 900 € par mois. Les {eur(A['smicBrut'] * A['seuilPart'])} premiers ne comptent que pour {round((1 - A['ab1']) * 100)} % ({eur(A['smicBrut'] * A['seuilPart'] * (1 - A['ab1']))}), le reste pour {round((1 - A['ab2']) * 100)} % ({eur((900 - A['smicBrut'] * A['seuilPart']) * (1 - A['ab2']))}). Revenu retenu : {eur(A['smicBrut'] * A['seuilPart'] * (1 - A['ab1']) + (900 - A['smicBrut'] * A['seuilPart']) * (1 - A['ab2']))} par mois. AAH estimée : {eur(A['max'] - (A['smicBrut'] * A['seuilPart'] * (1 - A['ab1']) + (900 - A['smicBrut'] * A['seuilPart']) * (1 - A['ab2'])))} par mois, en plus du salaire.</p></aside></section>
<section aria-labelledby="limites"><h2 id="limites">Les limites de cette estimation</h2>
<p>La CAF applique d'autres règles que l'outil ne connaît pas : abattements particuliers (chômage, cessation d'activité), pension d'invalidité, hospitalisation ou séjour en établissement de plus de 60 jours, rémunération en ESAT. Pour un calcul complet, utilisez le <a href="https://www.mesdroitssociaux.gouv.fr/" rel="noopener" target="_blank">simulateur officiel mesdroitssociaux.gouv.fr</a>. Les conditions de taux d'incapacité et de résidence sont expliquées dans <a href="/aah/">le guide de l'AAH</a>.</p></section>""",
        "faq": [("Quel est le montant de l'AAH en 2026 ?", f"{eur(A['max'])} par mois au maximum depuis le {A['date']}. Le montant versé est réduit si vous avez d'autres ressources."),
                ("Peut-on cumuler l'AAH et un salaire ?", "Oui. Une partie seulement du salaire est prise en compte grâce aux abattements, si bien que travailler augmente toujours le revenu total."),
                ("Les revenus du conjoint comptent-ils pour l'AAH ?", "Non, plus depuis le 1er octobre 2023. Seules vos propres ressources sont prises en compte."),
                ("Ce simulateur remplace-t-il celui de la CAF ?", "Non. Il donne un ordre de grandeur. Le simulateur officiel de l'État sur mesdroitssociaux.gouv.fr et la CAF font foi.")],
        "suite": '<li><a href="/aah/">AAH : montant et cumul avec un salaire</a></li><li><a href="/rqth/">RQTH : les avantages</a></li><li><a href="/delais-mdph/">Délai de ma MDPH</a></li><li><a href="/dossier-mdph/">Remplir le dossier MDPH</a></li>',
        "sources": [("Service-public.fr, Allocation aux adultes handicapés (AAH), F12242", SP + "F12242"),
                    ("Décret n° 2026-229 du 30 mars 2026 portant revalorisation de l'AAH (Légifrance)", "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000053734356"),
                    ("Code de la sécurité sociale, article D821-9 (abattements sur les revenus d'activité)", "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000023097737"),
                    ("Code de la sécurité sociale, article R821-4-1 (calcul trimestriel)", "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000054333604"),
                    ("Mes droits sociaux, simulateur officiel", "https://www.mesdroitssociaux.gouv.fr/")],
        "verif": VERIF,
    },
}
