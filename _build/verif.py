#!/usr/bin/env python3
"""Contrôles SEO, qualité et anti-gabarit sur docs/ : à lancer après build.py. Sortie non nulle s'il y a une erreur."""
import glob, os, re, json, collections, html, statistics, sys

OUT = os.environ.get("MDH_OUT") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
DOMAIN = "https://mes-droits-handicap.fr"
pb = []; titres = collections.Counter(); descs = collections.Counter(); h1s = collections.Counter()
existe = lambda p: p == "/" or os.path.exists(os.path.join(OUT, p.strip("/"), "index.html")) or os.path.exists(os.path.join(OUT, p.strip("/")))
infos = {}


def texte_main(h):
    m = re.search(r"<main[^>]*>(.*)</main>", h, re.S)
    t = m.group(1) if m else h
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<figure class=\"mdh-chart\".*?</figure>", " ", t, flags=re.S)
    t = re.sub(r"<(p|li|h[1-6]|td|th|summary|div|section|aside|pre|caption)[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"[ \t ]+", " ", t)


for f in sorted(glob.glob(OUT + "/**/index.html", recursive=True)):
    p = "/" + os.path.relpath(os.path.dirname(f), OUT).replace(".", "") + "/"
    p = p.replace("//", "/")
    h = open(f, encoding="utf-8").read()
    t = html.unescape(re.search(r"<title>(.*?)</title>", h).group(1)); d = html.unescape(re.search(r'name="description" content="(.*?)"', h).group(1))
    titres[t] += 1; descs[d] += 1
    n1 = len(re.findall(r"<h1[ >]", h)); h1s[re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S).group(1)] += 1
    if n1 != 1: pb.append((p, f"{n1} H1"))
    if len(t) > 60: pb.append((p, f"title {len(t)} car."))
    if len(d) > 155: pb.append((p, f"description {len(d)} car."))
    can = re.search(r'rel="canonical" href="([^"]+)"', h)
    if not can or can.group(1) != DOMAIN + p: pb.append((p, "canonical"))
    for og in ("og:title", "og:description", "og:url", "og:image", "og:type"):
        if f'property="{og}"' not in h: pb.append((p, f"{og} manquant"))
    visible = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    if re.search("[—–]", visible): pb.append((p, "tiret long"))
    if re.search(r"[a-zà-ÿ,] - [a-zà-ÿ]", html.unescape(re.sub(r"<[^>]+>", " ", visible))): pb.append((p, "tiret de ponctuation"))
    for a in re.findall(r'href="(/[^"#?]*)', h):
        if a.startswith("//"): continue
        if not existe(a): pb.append((p, f"lien cassé {a}"))
    for img in re.findall(r"<img [^>]*>", h):
        if 'alt="' not in img: pb.append((p, "image sans alt"))
    for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try: json.loads(s)
        except Exception: pb.append((p, "JSON-LD invalide"))
    if p.startswith("/outils/"):
        if re.search(r'<script[^>]+src="(https?:)?//', h): pb.append((p, "script tiers sur une page outil"))
        if "goatcounter" in h: pb.append((p, "compteur sur une page outil"))
    txt = texte_main(h)
    infos[p] = {"mots": len(re.findall(r"\w+", txt)), "txt": txt}

for c, txt in ((titres, "title"), (descs, "description"), (h1s, "H1")):
    for k, v in c.items():
        if v > 1: pb.append(("*", f"{txt} en double : {k[:60]}"))

# --- anti-gabarit : part des mots situés dans des phrases présentes sur au moins 2 pages départementales
deps = {p: i for p, i in infos.items() if re.fullmatch(r"/delais-mdph/[^/]+/", p)}


def phrases(t):
    out = []
    for ligne in t.split("\n"):
        for s in re.split(r"(?<=[.!?:;])\s+", ligne.strip()):
            s = s.strip()
            if len(re.findall(r"\w+", s)) >= 3: out.append(s)
    return out


def mesure(norm):
    vus = collections.Counter()
    P = {p: [norm(s) for s in phrases(i["txt"])] for p, i in deps.items()}
    for p, ss in P.items():
        for s in set(ss): vus[s] += 1
    parts = {}
    for p, ss in P.items():
        tot = sum(len(re.findall(r"\w+", s)) for s in ss) or 1
        com = sum(len(re.findall(r"\w+", s)) for s in ss if vus[s] > 1)
        parts[p] = com / tot
    return parts


if deps:
    brut = mesure(lambda s: s)
    stricte = mesure(lambda s: re.sub(r"\d+([,.]\d+)?", "#", s))
    mots = [i["mots"] for i in deps.values()]
    print(f"Pages départements : {len(deps)} | mots (texte du main) min {min(mots)}, médiane {statistics.median(mots):.0f}")
    print(f"  phrases communes (exactes)          : médiane {statistics.median(brut.values()) * 100:.1f} %, max {max(brut.values()) * 100:.1f} %")
    print(f"  phrases communes (chiffres masqués) : médiane {statistics.median(stricte.values()) * 100:.1f} %, max {max(stricte.values()) * 100:.1f} %")
    for p in deps:
        if brut[p] > 0.20: pb.append((p, f"phrases communes {brut[p] * 100:.0f} %"))
        if deps[p]["mots"] < 900: pb.append((p, f"{deps[p]['mots']} mots (< 900)"))
guides = {p: i for p, i in infos.items() if p.strip("/") in ("dossier-mdph", "projet-de-vie-mdph", "certificat-medical-mdph", "dossier-mdph-trop-long", "recours-mdph", "renouvellement-mdph", "aah", "rqth", "aeeh", "pch", "carte-mobilite-inclusion")}
if guides:
    print("Guides :", ", ".join(f"{p.strip('/')} {i['mots']}" for p, i in sorted(guides.items())))
print("Pages :", len(infos))
print(len(set(x[0] for x in pb)), "pages avec problème" if pb else "aucun problème")
for p, m in sorted(set(pb)): print(" ", p, "|", m)
sys.exit(1 if pb else 0)
