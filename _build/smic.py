"""Smic et seuils qui en dépendent : SEUL endroit où ces valeurs sont écrites.

Les guides (contenu/*.json) utilisent des repères {{SMIC_MENSUEL}}, {{SEUIL_AAH}}… remplacés au build,
et les outils lisent les mêmes constantes (outils_pages.py). Rien n'est recopié en dur ailleurs.

À METTRE À JOUR AU 01/12/2026 DÈS PARUTION DU DÉCRET au Journal officiel (hausse de 1,6 % annoncée le 13/11/2026,
valeurs attendues autour de 12,51 € de l'heure et 1 897 € par mois, NON publiées tant que le décret n'est pas paru) :
1. changer SMIC_HORAIRE, SMIC_MENSUEL, SMIC_DATE et SMIC_SOURCE ;
2. relancer build.py puis verif.py, et vérifier les exemples des guides AAH et AEEH ;
3. revoir aussi les tarifs de l'aidant familial de la PCH (contenu/pch.json), indexés sur le Smic net.
"""

SMIC_HORAIRE = 12.31          # € brut de l'heure, en vigueur au 1er novembre 2026
SMIC_MENSUEL = 1867.02        # € brut par mois (151,67 h), en vigueur au 1er novembre 2026
SMIC_DATE = "1er novembre 2026"   # date de validité affichée sur le site (« valeurs au 1er novembre 2026 »)
SMIC_SOURCE = ("Service-public.fr, Smic (F2300), vérifié le 1er juin 2026", "https://www.service-public.gouv.fr/particuliers/vosdroits/F2300")

SEUIL_AAH_PART = 0.30         # D821-9 CSS : abattement de 80 % jusqu'à 30 % du Smic brut mensuel
SEUIL_AEEH_PART = 0.55        # AEEH : revenus professionnels de l'enfant au plus 55 % du Smic brut mensuel
ESAT_CUMUL_PART = 1.00        # D821-5 CSS : AAH + rémunération garantie au plus 100 % du Smic brut mensuel
ESAT_CUMUL_MAJ = 0.15         # majoration de 15 % avec un enfant ou un ascendant à charge


def eur(x, dec=2):
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",") + " €"


def valeurs():
    seuil = round(SMIC_MENSUEL * SEUIL_AAH_PART, 2)
    # Exemple du guide AAH : salaire de 1 200 € nets imposables par mois, en milieu ordinaire
    p1 = round(seuil * 0.2, 2); reste = round(1200 - seuil, 2); p2 = round(reste * 0.6, 2); tot = p1 + p2
    from outils_pages import PARAMS   # montant de l'AAH (revalorisé au 1er avril), import tardif pour éviter une boucle
    amax = PARAMS["aah"]["max"]
    return {
        "SMIC_HORAIRE": eur(SMIC_HORAIRE), "SMIC_MENSUEL": eur(SMIC_MENSUEL), "SMIC_DATE": SMIC_DATE,
        "SEUIL_AAH": eur(seuil), "SEUIL_AEEH": eur(SMIC_MENSUEL * SEUIL_AEEH_PART),
        "ESAT_CUMUL": eur(SMIC_MENSUEL * ESAT_CUMUL_PART), "ESAT_CUMUL_MAJ": eur(SMIC_MENSUEL * ESAT_CUMUL_PART * (1 + ESAT_CUMUL_MAJ)),
        "EX1200_P1": eur(p1), "EX1200_RESTE": eur(reste), "EX1200_P2": eur(p2),
        "EX1200_TOTAL": eur(round(tot), 0), "EX1200_AAH": eur(round(amax - tot), 0),
    }


def remplir(txt):
    """Remplace les repères {{NOM}} d'un texte (JSON brut d'un guide). Un repère inconnu fait échouer le build."""
    import re
    v = valeurs()

    def rep(m):
        if m.group(1) not in v: raise KeyError(f"repère Smic inconnu : {m.group(1)}")
        return v[m.group(1)]
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", rep, txt)
