#!/usr/bin/env python3
"""Données officielles par département -> _data/mdph.json (script de mise à jour trimestrielle).

Usage : python3 _build/donnees.py [--frais]
  --frais : retélécharge toutes les sources (sinon le cache _build/.cache/ est réutilisé).

Sources (toutes publiques, aucune donnée personnelle) :
  CNSA, baromètre des MDPH : délais de traitement, droits sans limitation de durée, satisfaction, activité
  CNAF, data.caf.fr : allocataires AAH et AEEH par département, AAH selon le taux d'incapacité
  DREES, enquête Aide sociale : bénéficiaires de la PCH au 31 décembre
  Insee : population au 1er janvier 2026
  Annuaire de l'administration (DILA) : coordonnées et horaires des MDPH
Après une mise à jour : relancer build.py puis verif.py. Les dates affichées viennent de SOURCES ci-dessous :
les mettre à jour à chaque nouveau millésime.
"""
import json, os, re, sys, ssl, zipfile, glob, urllib.request, urllib.parse, unicodedata
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "_build", ".cache")
OUT = os.path.join(ROOT, "_data", "mdph.json")
FRAIS = "--frais" in sys.argv
os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (mes-droits-handicap.fr, mise a jour des donnees publiques)"}
CNSA_ZIP = "https://data.cnsa.fr//Content/app/4nloMAqQ/ThirdParties/Zip_file/{}.zip"
CAF = "https://data.caf.fr/api/explore/v2.1/catalog/datasets"
DREES_PAPH = ("https://data.drees.solidarites-sante.gouv.fr/api/explore/v2.1/catalog/datasets/"
              "les-beneficiaires-de-l-aide-sociale-departementale-aux-personnes-agees-ou-handic/attachments/"
              "paph_les_beneficiaires_de_l_aide_sociale_departementale_series_longues_1996_2024_xlsx")
INSEE = "https://www.insee.fr/fr/statistiques/fichier/8721456/estim-pop-dep-sexe-gca-1975-2026.xlsx"
ANNUAIRE = "https://api-lannuaire.service-public.fr/api/explore/v2.1/catalog/datasets/api-lannuaire-administration/records"

# Ce qui est affiché sous chaque bloc (titre, lien, date de la donnée, date de publication ou de relevé)
SOURCES = {
    "delais": {"titre": "CNSA, baromètre des MDPH, délais moyens de traitement des demandes", "url": "https://www.cnsa.fr/donnees/barometre-des-mdph",
               "periode": "2e trimestre 2026", "publie": "fichier historique daté du 05/10/2026, relevé le 15/11/2026"},
    "dsld": {"titre": "CNSA, baromètre des MDPH, droits attribués sans limitation de durée", "url": "https://www.cnsa.fr/donnees/barometre-des-mdph",
             "periode": "2e trimestre 2026", "publie": "fichier historique daté du 05/10/2026, relevé le 15/11/2026"},
    "satisfaction": {"titre": "CNSA, baromètre des MDPH, enquête de satisfaction « Ma MDPH, mon avis compte »", "url": "https://www.cnsa.fr/donnees/barometre-des-mdph",
                     "periode": "année 2025", "publie": "fichier historique daté du 02/10/2026, relevé le 15/11/2026"},
    "activite": {"titre": "CNSA, baromètre des MDPH, nombre de décisions et avis rendus (enquête annuelle d'activité)", "url": "https://www.cnsa.fr/donnees/barometre-des-mdph",
                 "periode": "année 2024", "publie": "fichier historique daté du 02/10/2026, relevé le 15/11/2026"},
    "caf": {"titre": "CNAF, allocataires selon la prestation par département (data.caf.fr)", "url": "https://data.caf.fr/explore/dataset/s_ben_dep/",
            "periode": "mars 2026", "publie": "jeu mis à jour le 28/09/2026, relevé le 15/11/2026"},
    "caf_inca": {"titre": "CNAF, allocataires de l'AAH selon le taux d'incapacité (data.caf.fr)", "url": "https://data.caf.fr/explore/dataset/aah_s_tx_inca_dep/",
                 "periode": "mars 2026", "publie": "jeu mis à jour le 28/09/2026, relevé le 15/11/2026"},
    "pch": {"titre": "DREES, enquête Aide sociale, bénéficiaires de la PCH (séries longues)", "url": "https://data.drees.solidarites-sante.gouv.fr/explore/dataset/les-beneficiaires-de-l-aide-sociale-departementale-aux-personnes-agees-ou-handic/",
            "periode": "31 décembre 2024", "publie": "mise à jour du 03/09/2026, relevé le 15/11/2026"},
    "insee": {"titre": "Insee, estimations de population au 1er janvier 2026", "url": "https://www.insee.fr/fr/statistiques/8721456",
              "periode": "1er janvier 2026", "publie": "parues le 13/01/2026"},
    "annuaire": {"titre": "Annuaire de l'administration (Direction de l'information légale et administrative)", "url": "https://lannuaire.service-public.gouv.fr/",
                 "periode": "", "publie": "coordonnées relevées le 15/11/2026"},
}


def get(url, fn):
    fp = os.path.join(CACHE, fn)
    if FRAIS or not os.path.exists(fp):
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=180).read()
        open(fp, "wb").write(data)
    return fp


def get_json(url, fn):
    return json.load(open(get(url, fn), encoding="utf-8"))


def code_norm(c):
    if c is None: return None
    c = str(c).strip()
    if c.upper() in ("NATIONALE", "FR"): return "FR"
    if re.fullmatch(r"\d", c): c = "0" + c
    if c in ("69M", "69D", "6EA"): return c
    if re.fullmatch(r"\d{2,3}|2A|2B", c): return c
    m = re.match(r"\s*(\d{2,3}|2A|2B|6EA|69M|69D)\s*-", c)
    return m.group(1) if m else None


def num(v):
    return float(v) if isinstance(v, (int, float)) else None


def periode(lab):
    """« 2e trimestre 2026 » -> '2026T2' ; 2019 -> '2019' ; « De janvier à août 2020 » -> '2020S1'."""
    if lab is None: return None
    s = str(lab).strip()
    m = re.match(r"(\d)(?:er|e)\s+trimestre\s+(\d{4})", s)
    if m: return f"{m.group(2)}T{m.group(1)}"
    if re.fullmatch(r"(19|20)\d\d", s): return s
    if "janvier à août 2020" in s: return "2020S1"
    return None


def cnsa_xlsx(nom):
    z = get(CNSA_ZIP.format(nom), nom + ".zip")
    d = os.path.join(CACHE, "cnsa_" + nom)
    if FRAIS or not os.path.isdir(d):
        zipfile.ZipFile(z).extractall(d)
    return glob.glob(os.path.join(d, "**", "*.xlsx"), recursive=True)[0]


def serie_trimestres(ws):
    """Feuilles DMT / DSLD : ligne des périodes (« Période ») puis une ligne par département avec son code."""
    rows = list(ws.iter_rows(values_only=True))
    hp = next(i for i, r in enumerate(rows) if r and len(r) > 1 and r[1] == "Période")
    cols = [(j, periode(v)) for j, v in enumerate(rows[hp]) if periode(v)]
    out = {}
    for r in rows[hp + 1:]:
        if not r: continue
        c = code_norm(r[0]) or code_norm(r[1])
        if not c or c in out: continue
        out[c] = {p: num(r[j]) for j, p in cols if j < len(r)}
    return out


def annuel(ws, label_row="Année"):
    """Feuilles satisfaction / activité : 1re colonne « 01 - Ain », années en ligne d'en-tête."""
    rows = list(ws.iter_rows(values_only=True))
    hy = next(i for i, r in enumerate(rows) if r and r[0] == label_row)
    ann, cur = [], None
    for j, v in enumerate(rows[hy]):
        if j == 0: ann.append(None); continue
        if isinstance(v, (int, float)) or (isinstance(v, str) and re.fullmatch(r"\d{4}", v.strip())): cur = int(v)
        ann.append(cur)
    sub = rows[hy + 1]
    out = {}
    for r in rows[hy + 2:]:
        if not r or r[0] is None: continue
        lab = str(r[0])
        c = "FR" if lab.strip().startswith("Moyenne nationale") else code_norm(lab)
        if not c: continue
        d = {}
        for j in range(1, len(r)):
            a = ann[j] if j < len(ann) else None
            if a is None: continue
            k = str(sub[j] or "").lower()
            key = "taux" if "taux" in k else "repondants" if "répondants à la question" in k else "participants" if ("participants" in k or "total" in k) else "valeur"
            d.setdefault(a, {})[key] = num(r[j])
        out[c] = d
    return out


def caf_records(ds, where, fn):
    q = urllib.parse.urlencode({"where": where})
    return get_json(f"{CAF}/{ds}/exports/json?{q}", fn)


def xl_table(path, sheet, header_key="Code département"):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and any(isinstance(c, str) and header_key in c for c in r))
    head = [str(c).strip() if c is not None else "" for c in rows[hi]]
    ic = next(i for i, h in enumerate(head) if header_key in h)
    out = {}
    for r in rows[hi + 1:]:
        c = r[ic] if ic < len(r) else None
        lab = " ".join(str(x) for x in r[:3] if x)
        if "France entière" in lab or "métropolitaine et DROM" in lab: c = "FR"
        c = code_norm(c) if c != "FR" else "FR"
        if not c or c in out: continue
        out[c] = {int(h): r[i] for i, h in enumerate(head) if re.fullmatch(r"(19|20)\d\d", h) and i < len(r) and isinstance(r[i], (int, float))}
    return out


def slug(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def J(x):
    if isinstance(x, str):
        try: return json.loads(x)
        except Exception: return x
    return x


def horaires(pl):
    pl = J(pl) or []
    out = []
    for p in pl if isinstance(pl, list) else []:
        j1, j2 = p.get("nom_jour_debut"), p.get("nom_jour_fin")
        jours = j1 if j1 == j2 or not j2 else f"{j1} au {j2.lower()}"
        h = lambda a, b: f"{a[:5].replace(':', 'h')} à {b[:5].replace(':', 'h')}" if a and b else ""
        plages = [x for x in (h(p.get("valeur_heure_debut_1"), p.get("valeur_heure_fin_1")), h(p.get("valeur_heure_debut_2"), p.get("valeur_heure_fin_2"))) if x]
        if jours and plages:
            out.append(jours + " : " + " et ".join(plages) + (f" ({p['commentaire']})" if p.get("commentaire") else ""))
    return out


def annuaire():
    res, off = [], 0
    while True:
        q = urllib.parse.urlencode({"where": 'pivot like "maison_handicapees"', "limit": 100, "offset": off})
        page = get_json(f"{ANNUAIRE}?{q}", f"annuaire_mdph_{off}.json")
        res += page["results"]; off += 100
        if off >= page["total_count"]: break
    out = {}
    for r in res:
        insee = str(r.get("code_insee_commune") or "")
        dep = insee[:3] if insee.startswith("97") else insee[:2]
        if dep == "20": dep = "2A" if insee[:3] in ("2A0", "2A1", "2A2", "2A3", "2A4") or insee.startswith("2A") else "2B"
        adr = (J(r.get("adresse")) or [{}])[0]
        tel = J(r.get("telephone")) or []
        site = J(r.get("site_internet")) or []
        c = {"nom": r.get("nom"), "adresse": ", ".join(x for x in [adr.get("complement1"), adr.get("complement2"), adr.get("numero_voie"), adr.get("service_distribution"),
                                                                 " ".join(y for y in [adr.get("code_postal"), adr.get("nom_commune")] if y)] if x and x.strip()),
             "commune": adr.get("nom_commune", ""), "tel": tel[0]["valeur"] if tel and isinstance(tel, list) else "",
             "courriel": r.get("adresse_courriel") or "", "site": site[0]["valeur"] if site and isinstance(site, list) else "",
             "horaires": horaires(r.get("plage_ouverture")), "fiche": r.get("url_service_public") or "",
             "accessible": bool(J(r.get("telephone_accessible"))), "maj": (r.get("date_modification") or "")[:10]}
        out.setdefault(dep, []).append(c)
    return out


def main():
    # --- CNSA
    dmt = openpyxl.load_workbook(cnsa_xlsx("Historique_Delais_traitement"), read_only=True, data_only=True)
    delais = {k: serie_trimestres(dmt[f"DMT {s}"]) for k, s in (("global", "global"), ("enfants", "enfants"), ("adultes", "adultes"), ("aah", "AAH"), ("pch", "PCH"))}
    dsld_wb = openpyxl.load_workbook(cnsa_xlsx("Historique_Droits_a_vie"), read_only=True, data_only=True)
    dsld = {k: serie_trimestres(dsld_wb[f"DSLD {s}"]) for k, s in (("aah", "AAH"), ("rqth", "RQTH"), ("cmi_inv", "CMI invalidité"), ("cmi_prio", "CMI priorité"), ("cmi_stat", "CMI stationnement"))}
    sat_wb = openpyxl.load_workbook(cnsa_xlsx("Historique_Satisfaction"), read_only=True, data_only=True)
    sat = {k: annuel(sat_wb[s]) for k, s in (("globale", "satisfaction globale"), ("accueil", "satisfaction - accueil"), ("besoins", "satisfaction - express° besoins"), ("aides", "satisfaction - aides"))}
    act = annuel(openpyxl.load_workbook(cnsa_xlsx("Historique_Activite"), read_only=True, data_only=True).worksheets[0])
    noms = {}
    ws = dmt["DMT global"]
    for r in ws.iter_rows(values_only=True):
        c = code_norm(r[0]) or code_norm(r[1])
        if c and c != "FR" and r[1]: noms[c] = re.sub(r"^\S+\s*-\s*", "", str(r[1])).strip()

    # --- CNAF (mois le plus récent et même mois un an plus tôt)
    dates = get_json(f"{CAF}/s_ben_dep/records?select=dtreffre&group_by=dtreffre&order_by=dtreffre%20desc&limit=13", "caf_dates.json")["results"]
    mois = dates[0]["dtreffre"][:7]; mois_n1 = f"{int(mois[:4]) - 1}{mois[4:]}"
    caf = {}
    for m in (mois, mois_n1):
        for r in caf_records("s_ben_dep", f"dtreffre = date'{m}-01'", f"caf_{m}.json"):
            c = code_norm(r["numdep"])
            if c: caf.setdefault(c, {})[m] = {"aah": num(r.get("indben_aah")) or (float(r["indben_aah"]) if r.get("indben_aah") else None),
                                               "aeeh": float(r["indben_aeeh"]) if r.get("indben_aeeh") not in (None, "") else None,
                                               "aeeh_foyers": num(r.get("indfoy_aeeh"))}
    inca = {}
    for r in get_json(f"{CAF}/aah_s_tx_inca_dep/exports/json?" + urllib.parse.urlencode({"where": f"dtreffre = date'{mois}-01'"}), f"caf_inca_{mois}.json"):
        c = code_norm(r["numdep"])
        if not c: continue
        t = r.get("aah_tx_inca") or ""
        k = "80" if "80" in t and "supérieur" in t else "50_79" if "50" in t else "autre"
        inca.setdefault(c, {"80": 0, "50_79": 0, "autre": 0})[k] += r.get("indben_aah") or 0

    # --- DREES PCH
    paph = get(DREES_PAPH, "paph_series.xlsx")
    pch = xl_table(paph, "Tab7-ph"); pch_paye = xl_table(paph, "Tab7b-ph"); pch_jeunes = xl_table(paph, "Tab7c-ph")

    # --- Insee
    wb = openpyxl.load_workbook(get(INSEE, "insee_gca_2026.xlsx"), read_only=True, data_only=True)
    pop = {}
    for r in wb["2026"].iter_rows(values_only=True):
        if not r or r[0] is None: continue
        lab = str(r[0]).strip()
        if lab == "France métropolitaine et DOM": pop["FR"] = {"total": r[7], "moins20": r[2]}; continue
        c = code_norm(lab)
        if c and isinstance(r[7], (int, float)): pop[c] = {"total": r[7], "moins20": r[2]}

    ann = annuaire()

    # Territoires regroupés : la CNSA publie la Corse (20) et l'Alsace (6EA) en un seul bloc ; on additionne les sources départementales.
    AGG = {"20": ("2A", "2B"), "6EA": ("67", "68")}
    for c, parts in AGG.items():
        if all(p in pop for p in parts): pop[c] = {k: sum(pop[p][k] for p in parts) for k in ("total", "moins20")}
        if all(p in caf for p in parts): caf[c] = {m: {k: sum(((caf[p].get(m) or {}).get(k) or 0) for p in parts) for k in ("aah", "aeeh", "aeeh_foyers")} for m in (mois, mois_n1)}
        if all(p in inca for p in parts): inca[c] = {k: sum(inca[p][k] for p in parts) for k in ("80", "50_79", "autre")}
        ann[c] = sum((ann.get(p, []) for p in parts), [])
    noms["69"] = "Rhône et Métropole de Lyon"  # page unique : la MDMPH est commune aux deux collectivités
    deps = {}
    for c, nom in noms.items():
        d = {"code": c, "nom": nom, "slug": slug(nom) + "-" + c.lower()}
        d["delais"] = {k: v.get(c, {}) for k, v in delais.items()}
        d["dsld"] = {k: v.get(c, {}) for k, v in dsld.items()}
        d["satisfaction"] = {k: v.get(c, {}) for k, v in sat.items()}
        d["activite"] = {a: x.get("valeur") for a, x in act.get(c, {}).items()}
        d["caf"] = caf.get(c, {}); d["caf_inca"] = inca.get(c)
        d["pch"] = {"droits": pch.get(c, {}), "payes": pch_paye.get(c, {}), "moins20": pch_jeunes.get(c, {})}
        d["pop"] = pop.get(c)
        d["annuaire"] = ann.get(c, [])
        deps[c] = d
    nat = {"delais": {k: v.get("FR", {}) for k, v in delais.items()}, "dsld": {k: v.get("FR", {}) for k, v in dsld.items()},
           "satisfaction": {k: v.get("FR", {}) for k, v in sat.items()}, "pop": pop.get("FR"),
           "caf": {m: {k: sum((caf[c].get(m) or {}).get(k) or 0 for c in caf) for k in ("aah", "aeeh")} for m in (mois, mois_n1)},
           "pch": {"droits": pch.get("FR", {}), "payes": pch_paye.get("FR", {})},
           "activite": {a: x.get("valeur") for a, x in act.get("FR", {}).items()}}
    json.dump({"sources": SOURCES, "mois_caf": mois, "mois_caf_n1": mois_n1, "national": nat, "departements": deps},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(deps), "départements ->", OUT, "| CAF", mois, "| sans annuaire :", [c for c in deps if not deps[c]["annuaire"]])


if __name__ == "__main__":
    main()
