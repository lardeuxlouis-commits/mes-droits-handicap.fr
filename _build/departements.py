"""Pages départementales (20 seulement) et classement national des délais.

Chaque phrase chiffrée est construite à partir des valeurs du département : la formulation dépend de
l'écart à la moyenne nationale et de l'évolution, puis une tournure est tirée du code du département.
Aucune donnée absente n'est remplacée : la phrase ou la ligne disparaît.
"""
import json, os, re, hashlib, html, datetime as dt
import graph as G

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "_data", "mdph.json"), encoding="utf-8"))
SRC = DATA["sources"]
NAT = DATA["national"]
DEPS = DATA["departements"]
try:
    LOC = json.load(open(os.path.join(ROOT, "_data", "locales.json"), encoding="utf-8"))
except Exception:
    LOC = {}
MOIS, MOIS_N1 = DATA["mois_caf"], DATA["mois_caf_n1"]
AUJ = dt.date(2026, 11, 15)
E = lambda s: html.escape(str(s if s is not None else ""), quote=True)

# Les 20 pages : choisies pour le volume de recherche « mdph + département » et la lenteur constatée
PAGES_DEP = ["93", "13", "59", "75", "92", "54", "91", "24", "69", "33", "62", "94", "77", "78", "95", "31", "06", "34", "44", "38"]
VOISINS = {"93": ["75", "92", "94", "95", "77"], "13": ["84", "83", "30", "04"], "59": ["62", "02", "80"], "75": ["92", "93", "94"],
           "92": ["75", "78", "95", "91", "93", "94"], "54": ["57", "55", "88", "6EA"], "91": ["92", "94", "77", "78", "45", "28"],
           "24": ["87", "19", "46", "47", "33", "16", "17"], "69": ["01", "42", "38", "71"], "33": ["17", "24", "47", "40"], "62": ["59", "80"],
           "94": ["75", "92", "93", "77", "91"], "77": ["93", "94", "91", "95", "60", "02", "51", "10", "89", "45"], "78": ["92", "95", "91", "28", "27"],
           "95": ["92", "93", "78", "77", "60", "27"], "31": ["32", "82", "81", "11", "09", "65"], "06": ["83", "04"], "34": ["30", "12", "81", "11"],
           "44": ["35", "56", "49", "85"], "38": ["69M", "69D", "01", "73", "05", "26", "42"]}
# Toutes les autres MDPH (21/11/2026) : voisins calculés sur les contours des départements (france-geojson), conservés dans _data/voisins-geo.json
_GEO = json.load(open(os.path.join(ROOT, "_data", "voisins-geo.json"), encoding="utf-8"))
_MAP = {"67": "6EA", "68": "6EA", "2A": "20", "2B": "20"}
def _vois(code):
    srcs = {"6EA": ["67", "68"], "20": ["2A", "2B"], "69": ["69"]}.get(code, [code])
    out = []
    for s0 in srcs:
        for v in _GEO.get(s0, []):
            v = _MAP.get(v, v)
            vs = ["69M", "69D"] if v == "69" else [v]
            for x in vs:
                if x != code and x not in out and x not in srcs: out.append(x)
    return out
TRIM = ["2025T1", "2025T2", "2025T3", "2025T4", "2026T1", "2026T2"]
DERNIER = "2026T2"
TYPES = [("global", "toutes demandes"), ("aah", "AAH"), ("pch", "PCH"), ("enfants", "enfants"), ("adultes", "adultes")]


def tlab(t, court=False):
    a, q = t.split("T")
    if court: return f"T{q} {a[2:]}"
    return f"{'1er' if q == '1' else q + 'e'} trimestre {a}"


def fr(x, d=1):
    s = f"{x:.{d}f}".replace(".", ",")
    return s[:-2] if d and s.endswith(",0") else s


def n_(x):
    return f"{int(round(x)):,}".replace(",", " ")


def pct(x, d=0):
    return fr(x * 100, d) + " %"


def V(code, salt, opts):
    return opts[int(hashlib.md5((code + salt).encode()).hexdigest(), 16) % len(opts)]


def mois_txt(m):
    """4,3 -> « 4,3 mois » ; on garde une décimale, c'est la précision utile."""
    return fr(m) + " mois"


def date_fr(d):
    M = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    return f"{d.day if d.day > 1 else '1er'} {M[d.month - 1]} {d.year}"


# ---------------------------------------------------------------- grammaire des noms de département
SPECIAL = {"Paris": ("à Paris", "de Paris"), "Rhône et Métropole de Lyon": ("dans le Rhône et la Métropole de Lyon", "du Rhône et de la Métropole de Lyon"),
           "Métropole de Lyon": ("dans la Métropole de Lyon", "de la Métropole de Lyon"), "Réunion": ("à La Réunion", "de La Réunion"),
           "Mayotte": ("à Mayotte", "de Mayotte"), "Hérault": ("dans l'Hérault", "de l'Hérault"), "Corse": ("en Corse", "de Corse"), "Alsace": ("en Alsace", "d'Alsace"),
           "Martinique": ("en Martinique", "de la Martinique"), "Guadeloupe": ("en Guadeloupe", "de la Guadeloupe"), "Guyane": ("en Guyane", "de la Guyane")}
PLUR = ("Alpes-de-Haute-Provence", "Hautes-Alpes", "Alpes-Maritimes", "Ardennes", "Bouches-du-Rhône", "Côtes-d'Armor", "Deux-Sèvres",
        "Hautes-Pyrénées", "Hauts-de-Seine", "Landes", "Pyrénées-Atlantiques", "Pyrénées-Orientales", "Vosges", "Yvelines")
FEM = ("Ardèche", "Ariège", "Aube", "Aude", "Charente", "Charente-Maritime", "Corrèze", "Côte-d'Or", "Dordogne", "Gironde", "Loire-Atlantique", "Lozère",
       "Mayenne", "Meurthe-et-Moselle", "Moselle", "Saône-et-Loire", "Savoie", "Seine-Maritime", "Seine-Saint-Denis", "Seine-et-Marne", "Vendée",
       "Haute-Garonne", "Haute-Savoie", "Haute-Vienne", "Haute-Loire", "Haute-Marne", "Haute-Saône", "Haute-Corse", "Corse-du-Sud", "Isère", "Eure", "Essonne",
       "Ille-et-Vilaine", "Eure-et-Loir", "Indre-et-Loire", "Indre", "Allier", "Ain", "Aisne", "Oise", "Orne", "Aveyron")   # Hérault : H muet, traité dans SPECIAL
DANS_LA = ("Loire", "Vienne", "Marne", "Manche", "Meuse", "Somme", "Sarthe", "Creuse", "Drôme", "Nièvre", "Haute-Marne")


def dans(nom):
    if nom in SPECIAL: return SPECIAL[nom][0]
    if nom in PLUR: return "dans les " + nom
    if nom in DANS_LA: return "dans la " + nom
    if nom[0] in "AEIOUÉÈÎÏÔY": return "dans l'" + nom
    if nom in FEM: return "en " + nom
    return "dans le " + nom


def de(nom):
    if nom in SPECIAL: return SPECIAL[nom][1]
    if nom in PLUR: return "des " + nom
    if nom in DANS_LA: return "de la " + nom
    if nom[0] in "AEIOUÉÈÎÏÔY": return "de l'" + nom
    if nom in FEM: return "de la " + nom
    return "du " + nom


def la_mdph(nom):
    return "la MDPH " + de(nom)


def cap(s):
    return s[:1].upper() + s[1:]


# ---------------------------------------------------------------- classement
def territoires():
    """Territoires classés au dernier trimestre (les codes de la CNSA : Corse = 20, Alsace = 6EA, Rhône = 69D et 69M)."""
    out = []
    for c, d in DEPS.items():
        if c in ("67", "68", "69"): continue
        g = d["delais"]["global"].get(DERNIER)
        if g is None: continue
        out.append(c)
    return out


TERR = territoires()
# Extension du 21/11/2026 : une page par MDPH du baromètre CNSA (Rhône et Métropole de Lyon sur la page 69)
for _c in TERR:
    _p = "69" if _c in ("69M", "69D") else _c
    if _p not in PAGES_DEP: PAGES_DEP.append(_p)
    if _p not in VOISINS: VOISINS[_p] = _vois(_p)


def rang(code, typ="global"):
    vals = sorted(((DEPS[c]["delais"][typ].get(DERNIER), c) for c in TERR if DEPS[c]["delais"][typ].get(DERNIER) is not None), reverse=True)
    for i, (_, c) in enumerate(vals):
        if c == code: return i + 1, len(vals)
    return None


def nat(typ, t=DERNIER):
    return NAT["delais"][typ].get(t)


def lien_dep(code):
    if code in PAGES_DEP: return f"/delais-mdph/{DEPS[code]['slug']}/"
    if code in ("69M", "69D") and "69" in PAGES_DEP: return f"/delais-mdph/{DEPS['69']['slug']}/"
    return None


def nom_court(code):
    n = DEPS[code]["nom"]
    return n


# ---------------------------------------------------------------- blocs de texte
COURT = {"delais": "CNSA, baromètre des MDPH", "dsld": "CNSA, baromètre des MDPH", "satisfaction": "CNSA, enquête de satisfaction", "activite": "CNSA, enquête d'activité",
         "caf": "CNAF, data.caf.fr", "caf_inca": "CNAF, AAH par taux d'incapacité", "pch": "DREES, enquête Aide sociale", "insee": "Insee", "annuaire": "annuaire de l'administration"}


def src_line(*keys, nom=None):
    parts = []
    for k in keys:
        s = SRC[k]
        per = f" ({s['periode']})" if s.get("periode") else " (relevé du 15/11/2026)"
        parts.append(f'<a href="{E(s["url"])}" rel="noopener" target="_blank">{E(COURT[k])}</a>{E(per)}')
    if nom: return f'<p class="mdh-src">Chiffres {de(nom)} tirés de ' + ", ".join(parts) + ".</p>"
    return '<p class="mdh-src">Source : ' + ", ".join(parts) + ".</p>"


def phr_rang(code, r, nom):
    i, n = r
    if i <= 5: return V(code, "r", [f"C'est l'un des cinq délais les plus longs de France ({i}e sur {n}).", f"Seules {i - 1} MDPH font plus long en France : le département se classe {i}e sur {n}.", f"Au classement national, {nom} arrive {i}e sur {n}, dans le groupe des plus lents."]) if i > 1 else f"C'est le délai le plus long des {n} territoires classés."
    if i <= n // 4: return V(code, "r", [f"Le département se situe dans le quart des MDPH les plus lentes ({i}e sur {n}).", f"Avec ce chiffre, il pointe au {i}e rang sur {n}, du plus long au plus court.", f"Rang national : {i}e sur {n}, parmi les délais les plus longs."])
    if i > n - n // 4: return V(code, "r", [f"Ce délai le place parmi les MDPH les plus rapides du pays ({n - i + 1}e plus court sur {n}).", f"C'est le {n - i + 1}e délai le plus court sur {n} territoires.", f"Au classement, le département figure dans le quart le plus rapide : {i}e sur {n} du plus long au plus court."])
    return V(code, "r", [f"Au classement national, il occupe le {i}e rang sur {n}, du plus long au plus court, donc dans la moitié {'haute' if i <= n / 2 else 'basse'}.", f"La MDPH {de(nom)} se situe au milieu du classement, {i}e sur {n}.", f"Rang : {i}e sur {n} territoires classés par la CNSA."])


def bloc_delais(code, codes, nom):
    """Délais : texte selon l'écart à la moyenne et la tendance, mini graphique, tableau 6 trimestres."""
    out, faq = [], []
    D = DEPS[codes[0]]["delais"]
    g, gn = D["global"].get(DERNIER), nat("global")
    an = D["global"].get("2025T2")
    Dans = cap(dans(nom))
    if len(codes) > 1:
        # Rhône : deux territoires dans le baromètre
        a, b = DEPS["69M"], DEPS["69D"]
        ga, gb = a["delais"]["global"][DERNIER], b["delais"]["global"][DERNIER]
        out.append(f"<p>La CNSA publie deux séries pour ce territoire, car la maison départementale et métropolitaine des personnes handicapées (MDMPH) traite les dossiers de deux collectivités. "
                   f"Au {tlab(DERNIER)}, le délai moyen de traitement atteint <b>{mois_txt(ga)}</b> pour les habitants de la Métropole de Lyon et <b>{mois_txt(gb)}</b> pour ceux du reste du Rhône, "
                   f"contre {mois_txt(gn)} en moyenne nationale. {phr_rang('69M', rang('69M'), 'la Métropole de Lyon').replace('Le département', 'La Métropole')} "
                   f"Côté Rhône hors Métropole, le rang est {rang('69D')[0]}e sur {rang('69D')[1]}.</p>")
        ser = [("Métropole de Lyon", G.C["brand"], [a["delais"]["global"].get(t) for t in TRIM], False),
               ("Rhône hors Métropole", G.C["alert"], [b["delais"]["global"].get(t) for t in TRIM], False),
               ("Moyenne nationale", G.C["sun"], [nat("global", t) for t in TRIM], True)]
        out.append(G.lignes(ser, [tlab(t, True) for t in TRIM], "Délai moyen de traitement, toutes demandes"))
        out.append(G.compare([(lab, a["delais"][k].get(DERNIER), nat(k)) for k, lab in (("global", "Toutes"), ("aah", "AAH"), ("pch", "PCH"), ("enfants", "Enfants"), ("adultes", "Adultes"))],
                             f"Délais de la Métropole de Lyon et moyenne nationale par type de demande au {tlab(DERNIER)}", "Métropole de Lyon"))
        rows = []
        for t in TRIM:
            rows.append(f"<tr><td>{tlab(t)}</td>" + "".join(f'<td class="mdh-n">{fr(x) if x is not None else "n.c."}</td>' for x in (a["delais"]["aah"].get(t), b["delais"]["aah"].get(t), a["delais"]["pch"].get(t), b["delais"]["pch"].get(t))) + "</tr>")
        out.append('<div class="mdh-tw"><table><caption class="mdh-note" style="text-align:left;padding:8px 12px">Délais en mois (n.c. : non communiqué)</caption><thead><tr><th>Trimestre</th><th class="mdh-n">AAH Métropole</th><th class="mdh-n">AAH Rhône</th><th class="mdh-n">PCH Métropole</th><th class="mdh-n">PCH Rhône</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
        faq.append((f"Quel est le délai de la MDPH du Rhône en 2026 ?", f"Au {tlab(DERNIER)}, la CNSA indique {mois_txt(ga)} en moyenne pour la Métropole de Lyon et {mois_txt(gb)} pour le Rhône hors Métropole, contre {mois_txt(gn)} en France. Ce sont des moyennes : un dossier précis peut aller plus vite ou plus lentement."))
        out.append(src_line("delais", nom=nom))
        return out, faq, max(ga, gb)
    if g is None: return out, faq, None
    e = (g - gn) / gn
    if e > 0.25:
        p1 = V(code, "a", [f"{Dans}, la MDPH a mis en moyenne <b>{mois_txt(g)}</b> pour traiter une demande au {tlab(DERNIER)}. C'est nettement plus que la moyenne nationale ({mois_txt(gn)}), soit environ {fr((g - gn) * 30.4, 0)} jours d'attente en plus.",
                           f"Comptez en moyenne <b>{mois_txt(g)}</b> entre le dépôt d'un dossier complet et la décision {dans(nom)} (chiffre CNSA du {tlab(DERNIER)}). La moyenne française est de {mois_txt(gn)} : l'écart est de {fr(e * 100, 0)} %.",
                           f"Au {tlab(DERNIER)}, le délai moyen de traitement {de(nom)} s'établit à <b>{mois_txt(g)}</b>, bien au-dessus des {mois_txt(gn)} constatés en moyenne en France."])
    elif e > 0.07:
        p1 = V(code, "a", [f"{Dans}, une demande est traitée en <b>{mois_txt(g)}</b> en moyenne au {tlab(DERNIER)}, un peu plus que la moyenne nationale ({mois_txt(gn)}).",
                           f"Le délai moyen de la MDPH {de(nom)} atteint <b>{mois_txt(g)}</b> au {tlab(DERNIER)}, légèrement au-dessus des {mois_txt(gn)} observés en France.",
                           f"Au {tlab(DERNIER)}, il fallait compter <b>{mois_txt(g)}</b> en moyenne {dans(nom)}, contre {mois_txt(gn)} pour l'ensemble des MDPH."])
    elif e < -0.25:
        p1 = V(code, "a", [f"{Dans}, la MDPH répond en moyenne en <b>{mois_txt(g)}</b> au {tlab(DERNIER)}, bien plus vite que la moyenne nationale ({mois_txt(gn)}).",
                           f"Bonne nouvelle pour les habitants {de(nom)} : le délai moyen de traitement est de <b>{mois_txt(g)}</b> au {tlab(DERNIER)}, quand la France entière est à {mois_txt(gn)}.",
                           f"Au {tlab(DERNIER)}, la MDPH {de(nom)} a rendu ses décisions en <b>{mois_txt(g)}</b> en moyenne, soit {fr(abs(e) * 100, 0)} % de moins que la moyenne nationale ({mois_txt(gn)})."])
    elif e < -0.07:
        p1 = V(code, "a", [f"{Dans}, le délai moyen est de <b>{mois_txt(g)}</b> au {tlab(DERNIER)}, un peu plus court que la moyenne nationale ({mois_txt(gn)}).",
                           f"La MDPH {de(nom)} traite une demande en <b>{mois_txt(g)}</b> en moyenne au {tlab(DERNIER)}, légèrement plus vite que l'ensemble des MDPH ({mois_txt(gn)}).",
                           f"Au {tlab(DERNIER)}, comptez <b>{mois_txt(g)}</b> en moyenne {dans(nom)}, un peu moins que les {mois_txt(gn)} de la moyenne française."])
    else:
        p1 = V(code, "a", [f"{Dans}, le délai moyen de traitement est de <b>{mois_txt(g)}</b> au {tlab(DERNIER)}, très proche de la moyenne nationale ({mois_txt(gn)}).",
                           f"Au {tlab(DERNIER)}, la MDPH {de(nom)} mettait <b>{mois_txt(g)}</b> en moyenne pour répondre, à peu près comme l'ensemble des MDPH ({mois_txt(gn)}).",
                           f"Comptez <b>{mois_txt(g)}</b> en moyenne {dans(nom)} au {tlab(DERNIER)}, un niveau voisin de la moyenne française de {mois_txt(gn)}."])
    r = rang(code)
    p1 += " " + phr_rang(code, r, nom)
    # tendance sur un an
    if an is not None:
        dlt = g - an
        if dlt <= -0.6:
            p1 += " " + V(code, "t", [f"La situation s'améliore : un an plus tôt, au {tlab('2025T2')}, il fallait {mois_txt(an)}.", f"Le délai a reculé de {fr(abs(dlt))} mois en un an ({mois_txt(an)} au {tlab('2025T2')}).", f"C'est {fr(abs(dlt))} mois de moins qu'au {tlab('2025T2')} ({mois_txt(an)})."])
        elif dlt >= 0.6:
            p1 += " " + V(code, "t", [f"Le délai s'est allongé de {fr(dlt)} mois en un an : il était de {mois_txt(an)} au {tlab('2025T2')}.", f"La tendance est à la hausse : {mois_txt(an)} un an plus tôt, au {tlab('2025T2')}.", f"Un an auparavant, au {tlab('2025T2')}, la MDPH répondait en {mois_txt(an)} : l'attente a donc augmenté."])
        else:
            p1 += " " + V(code, "t", [f"Le délai est stable sur un an ({mois_txt(an)} au {tlab('2025T2')}).", f"Sur un an, peu de changement : {mois_txt(an)} au {tlab('2025T2')}.", f"Il était déjà de {mois_txt(an)} au {tlab('2025T2')}."])
    out.append(f"<p>{p1}</p>")
    # AAH / PCH / enfants / adultes
    det = []
    for typ, lab in (("aah", "l'AAH"), ("pch", "la PCH")):
        v, vn = D[typ].get(DERNIER), nat(typ)
        if v is None: continue
        ec = (v - vn) / vn
        qual = "plus long que" if ec > 0.07 else "plus court que" if ec < -0.07 else "comparable à"
        det.append((typ, lab, v, vn, qual))
    if det:
        s = []
        for typ, lab, v, vn, qual in det:
            s.append(V(code, typ, [f"pour {lab}, {mois_txt(v)} ({qual} la moyenne nationale de {mois_txt(vn)})",
                                   f"{mois_txt(v)} pour {lab}, {qual} les {mois_txt(vn)} observés en France",
                                   f"{lab} : {mois_txt(v)}, {qual} la moyenne ({mois_txt(vn)})"]))
        intro = V(code, "d", [f"{cap(dans(nom))}, selon le type de demande, l'attente varie :", f"À la MDPH {de(nom)}, le délai dépend de ce que vous demandez :", f"Dans le détail, au même trimestre et {dans(nom)} :"])
        txt = intro + " " + " ; ".join(s) + "."
        ae, aa = D["enfants"].get(DERNIER), D["adultes"].get(DERNIER)
        if ae is not None and aa is not None:
            if abs(ae - aa) >= 0.5:
                txt += " " + V(code, "ea", [f"Les demandes pour un enfant sont traitées en {mois_txt(ae)}, celles des adultes en {mois_txt(aa)} : les familles {'attendent moins' if ae < aa else 'attendent davantage'}.",
                                            f"Côté enfants, le délai est de {mois_txt(ae)}, contre {mois_txt(aa)} pour les adultes.",
                                            f"{cap(dans(nom))}, un dossier d'enfant prend {mois_txt(ae)} en moyenne, un dossier d'adulte {mois_txt(aa)}."])
            else:
                txt += " " + V(code, "ea", [f"Enfants ({mois_txt(ae)}) et adultes ({mois_txt(aa)}) attendent à peu près autant.", f"Il y a peu d'écart entre enfants ({mois_txt(ae)}) et adultes ({mois_txt(aa)}).", f"Les délais des enfants ({mois_txt(ae)}) et des adultes ({mois_txt(aa)}) sont proches."])
        out.append(f"<p>{txt}</p>")
    # pic et creux sur 6 trimestres
    serie = [(t, D["global"].get(t)) for t in TRIM if D["global"].get(t) is not None]
    if len(serie) >= 4:
        hi = max(serie, key=lambda x: x[1]); lo = min(serie, key=lambda x: x[1])
        if hi[1] - lo[1] >= 0.8:
            out.append("<p>" + V(code, "pc", [f"Sur les six derniers trimestres, le délai a varié entre {mois_txt(lo[1])} ({tlab(lo[0])}) et {mois_txt(hi[1])} ({tlab(hi[0])}), et une moyenne trimestrielle peut bouger vite, d'où l'intérêt de déposer sans attendre.",
                                               f"Le point haut des six derniers trimestres a été atteint au {tlab(hi[0])} ({mois_txt(hi[1])}), le point bas au {tlab(lo[0])} ({mois_txt(lo[1])}).",
                                               f"Entre {tlab(TRIM[0])} et {tlab(DERNIER)}, l'attente est allée de {mois_txt(lo[1])} au plus court à {mois_txt(hi[1])} au plus long."]) + "</p>")
    ser = [("Toutes demandes", G.C["brand"], [D["global"].get(t) for t in TRIM], False), ("AAH", G.C["alert"], [D["aah"].get(t) for t in TRIM], False),
           ("PCH", G.C["ok"], [D["pch"].get(t) for t in TRIM], False), ("Moyenne nationale", G.C["sun"], [nat("global", t) for t in TRIM], True)]
    out.append(G.lignes(ser, [tlab(t, True) for t in TRIM], f"Délais moyens de traitement {de(nom)}, 6 derniers trimestres"))
    out.append(G.compare([(lab, D[k].get(DERNIER), nat(k)) for k, lab in (("global", "Toutes"), ("aah", "AAH"), ("pch", "PCH"), ("enfants", "Enfants"), ("adultes", "Adultes"))],
                         f"Délais {de(nom)} et moyenne nationale par type de demande au {tlab(DERNIER)}", "MDPH " + de(nom)))
    rows = "".join(f"<tr><td>{tlab(t)}</td>" + "".join(f'<td class="mdh-n">{fr(D[k].get(t)) if D[k].get(t) is not None else "n.c."}</td>' for k in ("global", "aah", "pch", "enfants", "adultes")) + "</tr>" for t in TRIM)
    out.append('<div class="mdh-tw"><table><thead><tr><th>Trimestre</th><th class="mdh-n">Toutes</th><th class="mdh-n">AAH</th><th class="mdh-n">PCH</th><th class="mdh-n">Enfants</th><th class="mdh-n">Adultes</th></tr></thead><tbody>' + rows + "</tbody></table></div>")
    out.append(f'<p class="mdh-note">Délais {de(nom)} en mois, du dépôt du dossier complet à la décision (n.c. : chiffre non transmis).</p>')
    out.append(src_line("delais", nom=nom))
    faq.append((f"Combien de temps met la MDPH {de(nom)} pour répondre ?", f"Au {tlab(DERNIER)}, le délai moyen de traitement était de {mois_txt(g)} {dans(nom)}, contre {mois_txt(gn)} en moyenne en France (baromètre de la CNSA)."
                + (V(code, "fa", [f" Pour une demande d'AAH {dans(nom)}, il était de {mois_txt(D['aah'][DERNIER])}.", f" Les demandes d'AAH y ont pris {mois_txt(D['aah'][DERNIER])} en moyenne.", f" Délai propre à l'AAH : {mois_txt(D['aah'][DERNIER])}."]) if D["aah"].get(DERNIER) is not None else "") + V(code, "fz", [f" Votre propre dossier {de(nom)} peut s'en écarter.", f" Un dossier complet dès le dépôt a plus de chances d'être traité {dans(nom)} dans la moyenne.", f" Ce chiffre de la MDPH {de(nom)} ne dit rien d'un dossier en particulier."])))
    return out, faq, g


def bloc_attente(code, nom, g):
    """Ce que le délai veut dire concrètement, avec les dates calculées à partir d'aujourd'hui."""
    if g is None: return []
    dep = AUJ + dt.timedelta(days=round(g * 30.44))
    implicite = dt.date(AUJ.year + (AUJ.month + 3) // 12, (AUJ.month + 3) % 12 + 1, AUJ.day)  # 4 mois de date à date
    out = []
    if g > 4:
        out.append("<p>" + V(code, "w", [f"Un dossier complet déposé le {date_fr(AUJ)} obtiendrait sa décision vers le <b>{date_fr(dep)}</b> si le délai moyen restait le même. Or la loi prévoit qu'au bout de <b>4 mois</b> sans réponse, la demande est considérée comme refusée (refus implicite), et {dans(nom)} ce cas de figure n'a rien d'exceptionnel.",
                                         f"Avec {mois_txt(g)} de délai moyen, on dépasse les 4 mois au-delà desquels le silence de l'administration vaut refus. Pour un dépôt le {date_fr(AUJ)}, ce refus implicite tomberait le {date_fr(implicite)}, alors que la décision ne viendrait en moyenne que vers le {date_fr(dep)}.",
                                         f"Le délai moyen {de(nom)} dépasse la limite de 4 mois fixée par les textes. Concrètement, un dossier déposé aujourd'hui ({date_fr(AUJ)}) vaudrait refus implicite le {date_fr(implicite)}, et la réponse réelle arriverait plutôt autour du {date_fr(dep)}."]) + "</p>")
        out.append("<p>" + V(code, "w2", [f"Ce refus implicite n'empêche pas la MDPH {de(nom)} de rendre ensuite sa décision, et il ouvre surtout la possibilité de contester si votre situation ne peut pas attendre.",
                                          f"La plupart des personnes attendent la vraie décision de la MDPH {de(nom)}, qui arrive souvent après, mais si l'attente vous met en difficulté, la date du refus implicite fait courir un délai de recours.",
                                          f"Ce silence n'est pas une décision sur le fond, et la MDPH {de(nom)} peut encore statuer, mais c'est un repère utile quand l'attente devient trop lourde."]) + f' <a href="/outils/delai-reponse-mdph/">Calculez vos dates exactes</a> et voyez <a href="/dossier-mdph-trop-long/">comment relancer la MDPH {de(nom)}</a>.</p>')
    else:
        out.append("<p>" + V(code, "w", [f"Pour un dossier complet déposé le {date_fr(AUJ)}, la décision arriverait vers le <b>{date_fr(dep)}</b> si le délai moyen se maintenait, donc avant la limite de 4 mois prévue par les textes ({date_fr(implicite)}).",
                                         f"À ce rythme, un dossier déposé aujourd'hui serait tranché autour du <b>{date_fr(dep)}</b>. Pour ce dossier déposé {dans(nom)}, la limite légale de 4 mois, au-delà de laquelle le silence vaut refus, tomberait le {date_fr(implicite)}.",
                                         f"En moyenne, la MDPH {de(nom)} répond donc avant les 4 mois prévus par la loi : déposé le {date_fr(AUJ)}, un dossier recevrait sa décision vers le <b>{date_fr(dep)}</b>."]) + "</p>")
        out.append("<p>" + V(code, "w2", [f"Une moyenne cache des écarts {dans(nom)}, car un dossier incomplet, une demande d'orientation ou une évaluation à domicile allongent l'attente.",
                                          f"Cela reste une moyenne, et {dans(nom)} comme ailleurs un certificat médical ancien ou une pièce manquante peuvent retarder votre dossier de plusieurs semaines.",
                                          f"Attention, c'est un délai moyen calculé sur tous les dossiers {de(nom)}, et les demandes complexes prennent plus de temps."]) + f' Pour limiter ce risque {dans(nom)}, <a href="/dossier-mdph/">préparez un dossier complet</a> et <a href="/outils/delai-reponse-mdph/">notez vos dates</a>.</p>')
    return out


def bloc_droits_vie(code, nom):
    d = DEPS[code]["dsld"]
    a, an, a1 = d["aah"].get(DERNIER), NAT["dsld"]["aah"].get(DERNIER), d["aah"].get("2024T2")
    out = []
    if a is None or an is None: return out, []
    c = (a - an) / an
    s = V(code, "v", [f"Au {tlab(DERNIER)}, <b>{pct(a)}</b> des AAH accordées {dans(nom)} aux personnes ayant un taux d'incapacité d'au moins 80 % l'ont été sans limitation de durée, ce qu'on appelle un droit à vie.",
                      f"Les droits à vie progressent lentement {dans(nom)}, où {pct(a)} des AAH attribuées au {tlab(DERNIER)} à des personnes avec un taux d'au moins 80 % n'ont pas de date de fin.",
                      f"{cap(dans(nom))}, la part des AAH (taux d'au moins 80 %) accordées sans limitation de durée au {tlab(DERNIER)} atteint <b>{pct(a)}</b>."])
    s += " " + (f"La moyenne nationale est de {pct(an)}, et la MDPH {de(nom)} {'en accorde nettement plus' if c > 0.12 else 'en accorde nettement moins' if c < -0.12 else 'est dans la moyenne'}."
                if V(code, "v2", [0, 1]) else f"C'est {'plus' if c > 0.05 else 'moins' if c < -0.05 else 'à peu près autant'} qu'en moyenne en France ({pct(an)}) pour la MDPH {de(nom)}.")
    if a1 is not None and abs(a - a1) >= 0.05:
        s += " " + V(code, "v4", [f"Deux ans plus tôt, au {tlab('2024T2')}, la part était de {pct(a1)} {dans(nom)}.", f"Au {tlab('2024T2')}, la MDPH {de(nom)} en était à {pct(a1)}.", f"La part était de {pct(a1)} deux ans plus tôt ({tlab('2024T2')})."])
    out.append(f"<p>{s}</p>")
    autres = []
    for k, lab in (("rqth", "la RQTH"), ("cmi_inv", "la carte mobilité inclusion mention invalidité"), ("cmi_stat", "la mention stationnement")):
        v, vn = d[k].get(DERNIER), NAT["dsld"][k].get(DERNIER)
        if v is not None and vn is not None: autres.append(f"{pct(v)} pour {lab} (France : {pct(vn)})")
    if autres:
        out.append("<p>" + V(code, "v3", [f"Même indicateur pour les autres droits {dans(nom)} : ", "Pour les autres décisions, la part accordée sans limitation de durée est de ", f"Ailleurs dans les décisions de la MDPH {de(nom)} : "]) + ", ".join(autres) + f'. Pour un habitant {de(nom)} titulaire d\'un droit à vie, plus besoin de <a href="/renouvellement-mdph/">redéposer un dossier à chaque échéance</a>.</p>')
    out.append(src_line("dsld", nom=nom))
    return out, [(f"La MDPH {de(nom)} accorde-t-elle l'AAH à vie ?", V(code, "fq", [f"Oui, pour les habitants {de(nom)} dont le taux d'incapacité atteint 80 % et dont la situation ne peut pas s'améliorer, soit {pct(a)} des AAH qui leur ont été accordées {dans(nom)} au {tlab(DERNIER)} l'ont été sans date de fin (France : {pct(an)}).",
                                                                                      f"La MDPH {de(nom)} le fait dans {pct(a)} des cas au {tlab(DERNIER)} pour les personnes ayant un taux d'au moins 80 %, contre {pct(an)} au niveau national, d'après la CNSA. Pour en bénéficier {dans(nom)} comme ailleurs, le handicap ne doit pas pouvoir évoluer favorablement.",
                                                                                      f"D'après la CNSA, {pct(a)} des AAH attribuées {dans(nom)} au {tlab(DERNIER)} aux personnes avec un taux de 80 % ou plus n'ont pas de limite de durée, quand la moyenne française est de {pct(an)}."]))]


def bloc_caf(code, nom):
    d = DEPS[code]
    caf, pop = d.get("caf") or {}, d.get("pop")
    x, x1 = caf.get(MOIS) or {}, caf.get(MOIS_N1) or {}
    if not x.get("aah"): return [], []
    out, faq = [], []
    m = "mars 2026"
    ntot, nn = NAT["caf"][MOIS]["aah"], NAT["pop"]["total"]
    s = V(code, "c", [f"En {m}, <b>{n_(x['aah'])}</b> personnes touchaient l'AAH par la CAF {dans(nom)}.",
                      f"La CAF versait l'AAH à <b>{n_(x['aah'])}</b> allocataires {dans(nom)} en {m}.",
                      f"{cap(dans(nom))}, l'allocation aux adultes handicapés concernait <b>{n_(x['aah'])}</b> personnes en {m} (allocataires de la CAF)."])
    if pop:
        t, tn = x["aah"] / pop["total"] * 1000, ntot / nn * 1000
        s += " " + V(code, "c2", [f"Rapporté à la population {de(nom)}, cela fait {fr(t)} allocataires pour 1 000 habitants, contre {fr(tn)} en France.",
                                  f"Soit {fr(t)} pour 1 000 habitants ({fr(tn)} pour 1 000 au niveau national).",
                                  f"Cela représente {fr(t)} personnes pour 1 000 habitants, la moyenne française étant de {fr(tn)}."])
    if x1.get("aah"):
        ev = (x["aah"] / x1["aah"] - 1) * 100
        evn = (ntot / NAT["caf"][MOIS_N1]["aah"] - 1) * 100
        s += " " + V(code, "c3", [f"Le nombre d'allocataires a évolué de {'+' if ev >= 0 else ''}{fr(ev)} % en un an ({'+' if evn >= 0 else ''}{fr(evn)} % en France).",
                                  f"En un an, l'évolution est de {'+' if ev >= 0 else ''}{fr(ev)} % {dans(nom)}, pour {'+' if evn >= 0 else ''}{fr(evn)} % au niveau national.",
                                  f"Sur un an, la CAF {de(nom)} compte {'+' if ev >= 0 else ''}{fr(ev)} % d'allocataires de l'AAH (France : {'+' if evn >= 0 else ''}{fr(evn)} %)."])
    out.append(f"<p>{s}</p>")
    inca = d.get("caf_inca")
    if inca and (inca["80"] + inca["50_79"]):
        p80 = inca["80"] / (inca["80"] + inca["50_79"] + inca["autre"])
        out.append("<p>" + V(code, "i", [f"Parmi les allocataires {de(nom)}, {pct(p80)} ont un taux d'incapacité d'au moins 80 %, les autres un taux de 50 à 79 % avec une restriction substantielle et durable d'accès à l'emploi.",
                                         f"{cap(dans(nom))}, {pct(p80)} de ces allocataires ont un taux d'incapacité de 80 % ou plus, et les autres relèvent du taux de 50 à 79 %, qui exige une restriction durable d'accès à l'emploi.",
                                         f"Taux d'incapacité : {n_(inca['80'])} allocataires à 80 % ou plus, {n_(inca['50_79'])} entre 50 et 79 %."]) + f' Le <a href="/aah/">guide de l\'AAH</a> détaille le montant 2026 et le cumul avec un salaire pour les allocataires {de(nom)}.</p>')
    if x.get("aeeh"):
        s = V(code, "e", [f"Côté enfants, <b>{n_(x['aeeh'])}</b> enfants {de(nom)} ouvraient droit à l'AEEH (allocation d'éducation de l'enfant handicapé) en {m}",
                          f"L'AEEH, versée aux parents d'un enfant handicapé, concernait <b>{n_(x['aeeh'])}</b> enfants {dans(nom)} en {m}",
                          f"Pour les familles {de(nom)}, la CAF comptait <b>{n_(x['aeeh'])}</b> enfants bénéficiaires de l'AEEH en {m}"])
        if pop and pop.get("moins20"):
            t = x["aeeh"] / pop["moins20"] * 1000; tn = NAT["caf"][MOIS]["aeeh"] / NAT["pop"]["moins20"] * 1000
            s += f", soit {fr(t)} pour 1 000 jeunes de moins de 20 ans ({fr(tn)} en France)"
        if x1.get("aeeh"):
            ev = (x["aeeh"] / x1["aeeh"] - 1) * 100
            s += ". " + V(code, "e2", [f"Ce nombre a {'augmenté' if ev > 0 else 'baissé'} de {fr(abs(ev))} % en un an", f"{cap(dans(nom))}, l'AEEH a {'progressé' if ev > 0 else 'reculé'} de {fr(abs(ev))} % sur un an", f"Sur un an, l'évolution est de {'+' if ev > 0 else '-'}{fr(abs(ev))} %"])
        out.append(f"<p>{s}. " + f'Pour une famille {de(nom)}, <a href="/outils/calcul-aeeh/">le calcul de l\'AEEH et de son complément</a> prend une minute.</p>')
    out.append(src_line("caf", "caf_inca", "insee", nom=nom))
    faq.append((f"Combien de personnes touchent l'AAH {dans(nom)} ?", f"En {m}, la CAF versait l'AAH à {n_(x['aah'])} personnes {dans(nom)}" + (f" et l'AEEH pour {n_(x['aeeh'])} enfants" if x.get("aeeh") else "") + f", hors allocataires de la MSA. " + V(code, "fq2", [f"Un an plus tôt, en mars 2025, ils étaient {n_(x1['aah']) if x1.get('aah') else 'n.c.'} pour l'AAH.", f"En mars 2025, la CAF {de(nom)} en comptait {n_(x1['aah']) if x1.get('aah') else 'n.c.'} pour l'AAH.", f"{cap(dans(nom))}, le chiffre de mars 2025 était de {n_(x1['aah']) if x1.get('aah') else 'n.c.'} allocataires de l'AAH."])))
    return out, faq


def bloc_pch(code, codes, nom):
    if len(codes) > 1:
        vals = [(DEPS[c]["pch"]["droits"].get("2024"), DEPS[c]["nom"]) for c in codes]
        if not all(v for v, _ in vals): return []
        return [f"<p>Fin 2024, {n_(vals[0][0])} personnes avaient un droit ouvert à la prestation de compensation du handicap (PCH) dans la Métropole de Lyon et {n_(vals[1][0])} dans le reste du Rhône (la PCH est versée par chaque collectivité). "
                'Ce que finance la PCH : <a href="/pch/">le guide de la PCH</a>.</p>', src_line("pch", nom=nom)]
    d = DEPS[code]["pch"]
    v, v19, pay, j = d["droits"].get("2024"), d["droits"].get("2019"), d["payes"].get("2024"), d["moins20"].get("2024")
    if not v: return []
    pop = DEPS[code].get("pop")
    s = V(code, "p", [f"Au 31 décembre 2024, <b>{n_(v)}</b> personnes avaient un droit ouvert à la PCH {dans(nom)}.",
                      f"Le département finançait la PCH de <b>{n_(v)}</b> personnes fin 2024 (droits ouverts au 31 décembre).",
                      f"Fin 2024, la prestation de compensation du handicap était ouverte à <b>{n_(v)}</b> habitants {de(nom)}."])
    if pop:
        t = v / pop["total"] * 1000
        tn = NAT["pch"]["droits"].get("2024") / NAT["pop"]["total"] * 1000 if NAT["pch"]["droits"].get("2024") else None
        if tn: s += f" Cela fait {fr(t)} pour 1 000 habitants, {'plus' if t > tn * 1.07 else 'moins' if t < tn * 0.93 else 'autant'} {'que la moyenne nationale' if abs(t / tn - 1) > .07 else 'que la moyenne nationale'} ({fr(tn)})."
    if v19:
        ev = (v / v19 - 1) * 100
        s += " " + V(code, "p2", [f"Ce nombre a {'progressé' if ev > 0 else 'reculé'} de {fr(abs(ev), 0)} % depuis fin 2019.", f"Depuis 2019, l'évolution est de {'+' if ev > 0 else ''}{fr(ev, 0)} %.", f"Il était de {n_(v19)} fin 2019."])
    if pay: s += " " + V(code, "p3", [f"En décembre 2024, {n_(pay)} personnes {de(nom)} ont effectivement reçu un paiement.", f"{cap(dans(nom))}, la PCH a été payée à {n_(pay)} personnes en décembre 2024.", f"Paiements réels en décembre 2024 : {n_(pay)} bénéficiaires {dans(nom)}."])
    if j: s += " " + V(code, "p4", [f"Les moins de 20 ans représentaient {n_(j)} droits ouverts.", f"Parmi ces droits, {n_(j)} concernaient des jeunes de moins de 20 ans {dans(nom)}.", f"{n_(j)} droits ouverts l'étaient pour des moins de 20 ans."])
    return [f"<p>{s} " + f'Le <a href="/pch/">guide de la PCH</a> explique ce qu\'elle peut financer pour un habitant {de(nom)} (aide humaine, matériel, logement, véhicule).</p>', src_line("pch", "insee", nom=nom)]


def bloc_activite(code, codes, nom):
    d = DEPS["69" if len(codes) > 1 else code]
    out = []
    a24, a19 = d["activite"].get("2024"), d["activite"].get("2019")
    if a24:
        s = V(code, "ac", [f"En 2024, la MDPH a rendu <b>{n_(a24)}</b> décisions et avis.", f"La MDPH {de(nom)} a produit <b>{n_(a24)}</b> décisions et avis au cours de l'année 2024.", f"Volume de travail en 2024 : <b>{n_(a24)}</b> décisions et avis rendus."])
        if a19:
            ev = (a24 / a19 - 1) * 100
            s += " " + V(code, "ac2", [f"C'est {fr(abs(ev), 0)} % de {'plus' if ev > 0 else 'moins'} qu'en 2019 ({n_(a19)}).", f"En 2019, elle en rendait {n_(a19)}, soit une évolution de {'+' if ev > 0 else ''}{fr(ev, 0)} %."])
        if d.get("pop"):
            s += " " + V(code, "ac4", [f"Rapporté à la population, cela fait {fr(a24 / d['pop']['total'] * 1000, 0)} décisions pour 1 000 habitants {de(nom)}.", f"Soit {fr(a24 / d['pop']['total'] * 1000, 0)} décisions pour 1 000 habitants.", f"C'est {fr(a24 / d['pop']['total'] * 1000, 0)} décisions pour 1 000 habitants {dans(nom)}."])
        out.append(f"<p>{s} " + V(code, "ac3", [f"Ce total compte chaque décision séparément : un seul dossier déposé {dans(nom)} peut en produire plusieurs (AAH, carte, RQTH).", f"Attention à la lecture : un même habitant {de(nom)} reçoit souvent plusieurs décisions pour un dossier.", f"Une demande peut donner lieu à plusieurs décisions de la MDPH {de(nom)}, une par droit demandé."]) + "</p>")
        out.append(src_line("activite", "insee", nom=nom))
    sat = d["satisfaction"]
    g25, gn = (sat["globale"].get("2025") or {}), (NAT["satisfaction"]["globale"].get("2025") or {})
    if g25.get("taux") is not None and g25.get("repondants"):
        nb = g25["repondants"]
        s = V(code, "s", [f"Dans l'enquête « Ma MDPH, mon avis compte » de 2025, <b>{pct(g25['taux'])}</b> des personnes qui ont répondu se disent satisfaites de la MDPH {de(nom)}",
                          f"Satisfaction des usagers en 2025 : <b>{pct(g25['taux'])}</b> de réponses positives {dans(nom)}",
                          f"En 2025, <b>{pct(g25['taux'])}</b> des répondants {de(nom)} ont déclaré être satisfaits de leur MDPH"])
        if gn.get("taux"): s += f" (moyenne nationale : {pct(gn['taux'])})"
        s += f", sur {n_(nb)} réponses."
        if nb < 100: s += f" Le nombre de réponses {dans(nom)} est faible, ce chiffre est donc à lire avec prudence."
        acc, bes = (sat["accueil"].get("2025") or {}).get("taux"), (sat["besoins"].get("2025") or {}).get("taux")
        if acc is not None and bes is not None and nb >= 100:
            s += " " + V(code, "s2", [f"L'accueil de la MDPH {de(nom)} recueille {pct(acc)} d'avis favorables, la prise en compte des besoins {pct(bes)}.", f"Dans le détail : {pct(acc)} de satisfaits pour l'accueil, {pct(bes)} pour l'écoute des besoins."])
        out.append(f"<p>{s}</p>")
        out.append(src_line("satisfaction", nom=nom))
    return out


def bloc_contacts(code, nom):
    ann = [{k: (v.replace(" – ", "-").replace("–", "-").replace("—", ",") if isinstance(v, str) else v) for k, v in c.items()} for c in (DEPS[code].get("annuaire") or [])]
    out = []
    for c in ann[:2]:
        li = []
        if c.get("adresse"): li.append(f"<li>Adresse : {E(c['adresse'])}</li>")
        if c.get("tel"): li.append(f'<li>Téléphone : <a href="tel:{E(c["tel"].replace(" ", ""))}">{E(c["tel"])}</a></li>')
        if c.get("courriel"): li.append(f'<li>Courriel : <a href="mailto:{E(c["courriel"])}">{E(c["courriel"])}</a></li>')
        if c.get("horaires"): li.append("<li>Horaires d'accueil : " + E(" ; ".join(c["horaires"])) + "</li>")
        if c.get("accessible"): li.append(f"<li>Accueil téléphonique accessible aux personnes sourdes ou malentendantes {dans(nom)}, selon l'annuaire</li>")
        links = []
        if c.get("site"): links.append(f'<a href="{E(c["site"])}" rel="noopener" target="_blank">site de la MDPH {E(de(nom))}</a>')
        if c.get("fiche"): links.append(f'<a href="{E(c["fiche"])}" rel="noopener" target="_blank">fiche {E(c.get("commune") or "")} sur l\'annuaire</a>')
        out.append(f'<div class="mdh-contact"><b>{E(c["nom"])}</b><ul>{"".join(li)}</ul>{" · ".join(links)}'
                   + (f'<p class="mdh-note">Fiche {E(c.get("commune") or "")} actualisée le {E(c["maj"])}.</p>' if c.get("maj") else "") + "</div>")
    if out: out.append(src_line("annuaire", nom=nom))
    return out


def _src_lab(u):
    """Libellé court d'une source : domaine et dernier segment lisible de l'adresse."""
    m = re.match(r"https://(?:www\.)?([^/]+)(/[^?#]*)?", u)
    dom, chemin = (m.group(1), m.group(2) or "") if m else (u, "")
    seg = [x for x in chemin.split("/") if x and not re.fullmatch(r"[0-9]+|index\.\w+", x)]
    fin = re.sub(r"\.(html?|php|aspx?)$", "", seg[-1]).replace("-", " ").replace("_", " ") if seg else ""
    return dom + (", " + fin if fin and len(fin) <= 60 else "")


def bloc_local(code, nom):
    L = LOC.get(code) or {}
    out = []
    faits = [f for f in L.get("faits", []) if f.get("texte") and str(f.get("url", "")).startswith("https://")]
    if L.get("recit"):
        out += [f"<p>{E(x.strip())}</p>" for x in L["recit"].split("\n") if x.strip()]
        # Le récit reprend déjà les faits : on ne les répète pas en liste, on renvoie seulement vers leurs sources (anti-doublon, audit du 19/11/2026).
        vus = []
        for f in faits:
            if f["url"] not in [v[0] for v in vus]: vus.append((f["url"], f.get("date")))
        if vus:
            out.append('<p class="mdh-src">Sources de ce paragraphe : ' + " ; ".join(f'<a href="{E(u)}" rel="noopener" target="_blank">{E(_src_lab(u))}</a>' + (f" ({E(d)})" if d else "") for u, d in vus) + ".</p>")
    elif faits:
        out.append("<ul>" + "".join(f'<li>{E(f["texte"])} <span class="mdh-src">(<a href="{E(f["url"])}" rel="noopener" target="_blank">source</a>{", " + E(f["date"]) if f.get("date") else ""})</span></li>' for f in faits[:8]) + "</ul>")
    return out


def bloc_voisins(code, nom, g):
    vs = [c for c in VOISINS.get(code, []) if c in DEPS and DEPS[c]["delais"]["global"].get(DERNIER) is not None]
    if not vs or g is None: return []
    vs.sort(key=lambda c: DEPS[c]["delais"]["global"][DERNIER])
    rows = []
    for c in vs:
        v = DEPS[c]["delais"]["global"][DERNIER]
        l = lien_dep(c)
        nm = E(DEPS[c]["nom"]) + (f" ({c})" if c[0].isdigit() and len(c) <= 3 and c.isdigit() else "")
        rows.append(f"<tr><td>{f'<a href={chr(34)}{l}{chr(34)}>{nm}</a>' if l else nm}</td><td class=\"mdh-n\">{fr(v)}</td><td class=\"mdh-n\">{fr(DEPS[c]['delais']['aah'].get(DERNIER)) if DEPS[c]['delais']['aah'].get(DERNIER) is not None else 'n.c.'}</td></tr>")
    plus_rapide = vs[0]
    v0 = DEPS[plus_rapide]["delais"]["global"][DERNIER]
    txt = V(code, "n", [f"Parmi les départements voisins, c'est {dans(DEPS[plus_rapide]['nom'])} que l'attente est la plus courte ({mois_txt(v0)}).",
                        f"Autour {de(nom)}, le délai le plus court revient à la MDPH {de(DEPS[plus_rapide]['nom'])}, avec {mois_txt(v0)}.",
                        f"Chez les voisins {de(nom)}, l'écart peut être important, de {mois_txt(v0)} {dans(DEPS[plus_rapide]['nom'])} à {mois_txt(DEPS[vs[-1]]['delais']['global'][DERNIER])} {dans(DEPS[vs[-1]]['nom'])}."])
    return [f"<p>{txt} Si vous habitez {dans(nom)}, c'est la MDPH {de(nom)} qui reste compétente pour votre dossier, même si un département voisin répond plus vite.</p>",
            '<div class="mdh-tw"><table><thead><tr><th>Département voisin</th><th class="mdh-n">Délai global</th><th class="mdh-n">Délai AAH</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>",
            src_line("delais", nom=nom)]


def h2_varies(code, codes, nom, g):
    """Intertitres choisis selon ce que disent les données du département (audit du 19/11/2026 : les 11 H2 étaient identiques
    sur les 20 pages). Chaque intertitre reste une phrase vraie, vérifiable dans le bloc qui suit."""
    D = DEPS[codes[0]]["delais"]["global"]
    an = D.get("2025T2")
    ev = None if g is None or an is None else g - an
    h = {}
    if g is None: h["delais"] = f"Combien de temps attendre une réponse de la MDPH {de(nom)} ?"
    elif g > 4 and ev is not None and ev >= 0.3: h["delais"] = f"MDPH {de(nom)}, un délai en hausse au-delà des 4 mois"
    elif g > 4 and ev is not None and ev <= -0.3: h["delais"] = f"MDPH {de(nom)}, un délai en baisse mais encore au-delà de 4 mois"
    elif g > 4: h["delais"] = f"MDPH {de(nom)}, un délai moyen au-delà des 4 mois légaux"
    elif ev is not None and ev <= -0.3: h["delais"] = f"MDPH {de(nom)}, un délai en baisse sur un an"
    elif ev is not None and ev >= 0.3: h["delais"] = f"MDPH {de(nom)}, un délai en hausse, mais sous les 4 mois"
    else: h["delais"] = f"Combien de temps attendre une réponse de la MDPH {de(nom)} ?"
    h["attente"] = (f"Déposer {dans(nom)}, quand le refus implicite arrive avant la décision moyenne" if g is not None and g > 4
                    else f"Déposer {dans(nom)}, avec une décision attendue avant les 4 mois" if g is not None else f"Déposer {dans(nom)}, quelles dates retenir ?")
    dv = DEPS[codes[0] if len(codes) == 1 else "69M"]["dsld"]["aah"].get(DERNIER); dn = NAT["dsld"]["aah"].get(DERNIER)
    c = None if dv is None or not dn else (dv - dn) / dn
    h["vie"] = (f"Plus de droits à vie {dans(nom)} qu'en moyenne" if c is not None and c > 0.12
                else f"Moins de droits à vie {dans(nom)} qu'en moyenne" if c is not None and c < -0.12 else f"Les droits accordés à vie {dans(nom)}")
    vs = [DEPS[x]["delais"]["global"].get(DERNIER) for x in VOISINS.get(code, []) if x in DEPS]
    vs = [v for v in vs if v is not None]
    if g is not None and vs and g < min(vs): h["voisins"] = f"La MDPH {de(nom)} plus rapide que ses voisines"
    elif g is not None and vs and g > max(vs): h["voisins"] = f"La MDPH {de(nom)} plus lente que ses voisines"
    else: h["voisins"] = f"Les délais autour {de(nom)}"
    return h


def page_dep(code):
    d = DEPS[code]
    nom = d["nom"]
    codes = ["69M", "69D"] if code == "69" else [code]
    sections, faq = [], []
    blocs_delais, f1, g = bloc_delais(code, codes, nom)
    faq += f1
    h = h2_varies(code, codes, nom, g)
    sections.append(("delais", h["delais"], blocs_delais))
    sections.append(("attente", h["attente"], bloc_attente(code, nom, g)))
    loc = bloc_local(code, nom)
    if loc: sections.append(("orientation", f"Déposer et suivre son dossier {dans(nom)}", loc))
    dv, f2 = bloc_droits_vie(codes[0], nom) if len(codes) == 1 else bloc_droits_vie("69M", "la Métropole de Lyon")
    if dv: sections.append(("droits-a-vie", h["vie"], dv)); faq += f2
    cf, f3 = bloc_caf(code, nom)
    if cf: sections.append(("allocataires", f"Combien de personnes touchent l'AAH et l'AEEH {dans(nom)} ?", cf)); faq += f3
    pc = bloc_pch(code, codes, nom)
    if pc: sections.append(("pch", f"La PCH {dans(nom)}", pc))
    ac = bloc_activite(code, codes, nom)
    if ac: sections.append(("activite", f"Activité et satisfaction : la MDPH {de(nom)} en chiffres", ac))
    vo = bloc_voisins(code, nom, g)
    if vo: sections.append(("voisins", h["voisins"], vo))
    ct = bloc_contacts(code, nom)
    if ct: sections.append(("contact", f"Contacter la MDPH {de(nom)}", ct))
    an = (DEPS[code].get("annuaire") or [{}])[0] if DEPS[code].get("annuaire") else {}
    if an.get("tel"):
        faq.append((f"Quel est le numéro de téléphone de la MDPH {de(nom)} ?", f"Selon l'annuaire officiel de l'administration, la MDPH {de(nom)} est joignable au {an['tel']}" + (f" ({'; '.join(an['horaires'])})" if an.get("horaires") else "") + f". Avant de vous déplacer à {an.get('commune') or 'l’accueil'}, vérifiez les horaires sur le site de la MDPH."))
    return {"code": code, "nom": nom, "codes": codes, "g": g, "sections": sections, "faq": faq}


def classement_rows():
    rows = []
    for c in TERR:
        x = DEPS[c]["delais"]
        r = {"code": c, "nom": "Rhône (hors Métropole de Lyon)" if c == "69D" else DEPS[c]["nom"], "lien": lien_dep(c)}
        for k, _ in TYPES: r[k] = x[k].get(DERNIER)
        r["an"] = x["global"].get("2025T2")
        rows.append(r)
    rows.sort(key=lambda r: -r["global"])
    return rows


def repartition(hl=(), lab=None):
    """Essaim des délais moyens de tous les territoires au dernier trimestre, territoire(s) mis en avant."""
    pts = [(c, DEPS[c]["delais"]["global"][DERNIER]) for c in TERR]
    t = f"Délai moyen de chacun des {len(pts)} territoires au {tlab(DERNIER)}" + (f", {lab} en bleu foncé" if lab else "")
    return G.repartition(pts, t, nat("global"), hl, lab)
