"""Graphiques SVG générés au build (aucun script, aucune bibliothèque tierce).

Style épuré : courbes lissées, aplat léger sous la série principale, grille en filets, étiquettes de fin.
Chaque graphique existe en deux dessins : large (g-d) et étroit pour mobile (g-m), l'un ou l'autre
affiché en CSS, pour garder un texte lisible à toutes les tailles.
Les animations (dévoilement de gauche à droite, barres qui poussent, points qui apparaissent) sont
pilotées en CSS par la classe « in » ajoutée par site.js à l'entrée dans l'écran : transform et opacity
uniquement. Sans JavaScript, ou avec prefers-reduced-motion, le graphique s'affiche directement.
"""
import html, itertools

E = lambda s: html.escape(str(s), quote=True)
C = {"brand": "#1f3b63", "sun": "#c98a3e", "mut": "#7b8494", "line": "#e7e1d6", "alert": "#c26a3d", "ok": "#4f8a7b", "nat": "#9aa6b6", "ink": "#1d2735"}
_id = itertools.count(1)
WD, WM = 680, 360          # largeur des dessins bureau et mobile (unités du viewBox)


def fr(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def _smooth(pts):
    """Courbe passant par tous les points (Catmull-Rom vers Bézier, tension douce)."""
    if len(pts) < 2: return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        t = 0.16
        c1 = (p1[0] + (p2[0] - p0[0]) * t, p1[1] + (p2[1] - p0[1]) * t)
        c2 = (p2[0] - (p3[0] - p1[0]) * t, p2[1] - (p3[1] - p1[1]) * t)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def _legend(items):
    out = ""
    for nom, col, dash in items:
        sw = (f'<svg width="22" height="8" aria-hidden="true"><line x1="1" y1="4" x2="21" y2="4" stroke="{col}" stroke-width="2.4" stroke-linecap="round"'
              f'{" stroke-dasharray=" + chr(34) + "3 4" + chr(34) if dash else ""}/></svg>')
        out += f'<li>{sw}{E(nom)}</li>'
    return f'<ul class="mdh-leg">{out}</ul>'


def _svg(cls, w, h, titre, inner):
    return f'<svg class="{cls}" viewBox="0 0 {w} {h}" role="img" aria-label="{E(titre)}"><title>{E(titre)}</title>{inner}</svg>'


def _fig(kind, titre, unite, d, m, legend=""):
    return f'<figure class="mdh-chart" data-g="{kind}">{legend}{d}{m}<figcaption>{E(titre)}, en {unite}.</figcaption></figure>'


def _hgrid(L, x2, Y, vmax, step, lab_x):
    g, v = [], 0
    while v <= vmax:
        g.append(f'<line x1="{L}" x2="{x2}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="g-h"{" style=" + chr(34) + "stroke-dasharray:none" + chr(34) if v == 0 else ""}/>'
                 f'<text x="{lab_x}" y="{Y(v) + 4:.1f}" text-anchor="end" class="g-t">{v}</text>')
        v += step
    return g


# --------------------------------------------------------------------------- courbes
def _lignes_svg(series, labels, titre, w, h, ymin, mob):
    vals = [v for _, _, s, _ in series for v in s if v is not None]
    k = next(_id)
    ymax = max(max(vals) * 1.15, 1)
    L, R, T, B = (32, 44, 16, 38) if mob else (34, 54, 18, 34)   # mobile : marges pour un texte de 17 unités (au moins 14 px rendus)
    n = len(labels)
    X = lambda i: L + (w - L - R) * (i / max(n - 1, 1))
    Y = lambda v: T + (h - T - B) * (1 - (v - ymin) / (ymax - ymin))
    step = (1 if ymax <= 5 else 2 if ymax <= 10 else 4 if ymax <= 20 else 5) if mob else (1 if ymax <= 8 else 2 if ymax <= 16 else 5)
    g = _hgrid(L, w - R + 6, Y, ymax, step, L - 7)
    nl = 4 if mob else 7
    every = max(1, -(-(n - 1) // (nl - 1)))
    for i, lab in enumerate(labels):
        if (i % every == 0 and (n - 1 - i) >= every * .6) or i == n - 1:
            g.append(f'<text x="{X(i):.1f}" y="{h - 9}" text-anchor="middle" class="g-t">{E(lab)}</text>')
    curves, ends, pts = [], [], []
    for j, (nom, col, s, dash) in enumerate(series):
        segs, seg = [], []
        for i, v in enumerate(s):
            if v is None:
                if len(seg) > 1: segs.append(seg)
                seg = []; continue
            seg.append((X(i), Y(v)))
        if len(seg) > 1: segs.append(seg)
        for p in segs:
            d = _smooth(p)
            if j == 0 and not dash:
                curves.append(f'<path d="{d} L{p[-1][0]:.1f},{Y(ymin):.1f} L{p[0][0]:.1f},{Y(ymin):.1f} Z" fill="url(#ga{k})"/>')
            curves.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{1.8 if dash else 2.4 if j else 2.8}"'
                          f'{" stroke-dasharray=" + chr(34) + "3 5" + chr(34) if dash else ""} stroke-linecap="round" stroke-linejoin="round"/>')
        last = max((i for i, v in enumerate(s) if v is not None), default=None)
        if last is not None:
            ends.append([X(last), Y(s[last]), s[last], col])
            pts.append(f'<circle cx="{X(last):.1f}" cy="{Y(s[last]):.1f}" r="{3.2 if dash else 4}" fill="#fff" stroke="{col}" stroke-width="2.2"/>')
    ends.sort(key=lambda e: e[1])
    gap = 22 if mob else 18
    for a in range(1, len(ends)):
        if ends[a][1] - ends[a - 1][1] < gap: ends[a][1] = ends[a - 1][1] + gap
    labs = "".join(f'<text x="{x + 8:.1f}" y="{ly + 4:.1f}" class="g-v" fill="{col}">{fr(v)}</text>' for x, ly, v, col in ends)
    defs = (f'<defs><linearGradient id="ga{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{series[0][1]}" stop-opacity=".16"/>'
            f'<stop offset="1" stop-color="{series[0][1]}" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="gc{k}"><rect class="g-reveal" x="0" y="0" width="{w}" height="{h}"/></clipPath></defs>')
    return _svg("g-m" if mob else "g-d", w, h, titre, f'{defs}{"".join(g)}<g clip-path="url(#gc{k})">{"".join(curves)}</g><g class="g-late">{"".join(pts)}{labs}</g>')


def lignes(series, labels, titre, unite="mois", h=260, w=WD, ymin=0):
    """series = [(nom, couleur, [valeurs ou None], pointillé)] ; labels = étiquettes de l'axe x."""
    if not [v for _, _, s, _ in series for v in s if v is not None]: return ""
    return _fig("line", titre, unite, _lignes_svg(series, labels, titre, w, h, ymin, False), _lignes_svg(series, labels, titre, WM, 230, ymin, True),
                _legend([(nm, cl, ds) for nm, cl, _, ds in series]))


# --------------------------------------------------------------------------- barres horizontales
def _barres_svg(items, titre, ref, ref_lab, w, hl, mob):
    vmax = max([v for _, v, _ in items] + ([ref] if ref else [])) * 1.06
    g = []
    if mob:   # étiquette au-dessus de chaque barre
        rh, L, R = 48, 0, 40   # texte de 17 unités sur mobile (au moins 14 px rendus)
        X = lambda v: L + (w - L - R) * v / vmax
        for i, (lab, v, lien) in enumerate(items):
            y = 4 + i * rh
            t = f'<text x="{L}" y="{y + 15}" class="g-l">{E(lab)}</text>'
            if lien: t = f'<a href="{E(lien)}">{t}</a>'
            col = C["alert"] if hl and lab == hl else C["brand"]
            g.append(t + f'<rect x="{L}" y="{y + 26}" width="{w - R - L}" height="10" rx="5" class="g-track"/>'
                     f'<rect x="{L}" y="{y + 26}" width="{max(X(v) - L, 10):.1f}" height="10" rx="5" fill="{col}" class="g-bar" style="--i:{i}"/>'
                     f'<text x="{X(v) + 6:.1f}" y="{y + 37}" class="g-v g-late" fill="{C["ink"]}">{fr(v)}</text>')
        h = 4 + rh * len(items) + (30 if ref else 4)
        top, bot = 2, h - 30
    else:
        rh, L, R = 30, 250, 56
        X = lambda v: L + (w - L - R) * v / vmax
        for i, (lab, v, lien) in enumerate(items):
            y = 6 + i * rh
            t = f'<text x="{L - 12}" y="{y + 17}" text-anchor="end" class="g-l">{E(lab)}</text>'
            if lien: t = f'<a href="{E(lien)}">{t}</a>'
            col = C["alert"] if hl and lab == hl else C["brand"]
            g.append(t + f'<rect x="{L}" y="{y + 6}" width="{w - R - L}" height="14" rx="7" class="g-track"/>'
                     f'<rect x="{L}" y="{y + 6}" width="{max(X(v) - L, 14):.1f}" height="14" rx="7" fill="{col}" class="g-bar" style="--i:{i}"/>'
                     f'<text x="{X(v) + 8:.1f}" y="{y + 17.5}" class="g-v g-late" fill="{C["ink"]}">{fr(v)}</text>')
        h = rh * len(items) + 34
        top, bot = 2, h - 22
    if ref:
        xr = X(ref)
        g.append(f'<line x1="{xr:.1f}" x2="{xr:.1f}" y1="{top}" y2="{bot}" stroke="{C["sun"]}" stroke-width="1.6" stroke-dasharray="3 4"/>'
                 f'<text x="{min(max(xr, L + (110 if mob else 80)), w - (110 if mob else 80)):.1f}" y="{h - 6}" text-anchor="middle" class="g-t" fill="#8a5a1c">{E(ref_lab)} : {fr(ref)}</text>')
    return _svg("g-m" if mob else "g-d", w, h, titre, "".join(g))


def barres(items, titre, ref=None, ref_lab="moyenne nationale", w=WD, unite="mois", hl=None):
    """items = [(étiquette, valeur, lien ou None)] : barres horizontales arrondies, ligne de référence."""
    if not items: return ""
    return _fig("bar", titre, unite, _barres_svg(items, titre, ref, ref_lab, w, hl, False), _barres_svg(items, titre, ref, ref_lab, WM, hl, True))


# --------------------------------------------------------------------------- colonnes local / national
def _compare_svg(rows, titre, w, mob):
    h, L, R, T, B = (220, 32, 4, 24, 34) if mob else (250, 34, 12, 26, 40)
    vmax = max(max(a, b) for _, a, b in rows) * 1.18
    Y = lambda v: T + (h - T - B) * (1 - v / vmax)
    band = (w - L - R) / len(rows)
    bw = min(34, band * (.3 if mob else .28))
    g = _hgrid(L, w - R, Y, vmax, (1 if vmax <= 5 else 2 if vmax <= 10 else 4) if mob else (1 if vmax <= 8 else 2), L - 7)
    for i, (lab, a, b) in enumerate(rows):
        cx = L + band * (i + .5)
        gap = 3 if mob else 6
        for j, (val, col) in enumerate(((a, C["brand"]), (b, C["nat"]))):
            x = cx - bw - gap / 2 + j * (bw + gap)
            g.append(f'<rect x="{x:.1f}" y="{Y(val):.1f}" width="{bw:.1f}" height="{Y(0) - Y(val):.1f}" rx="{4 if mob else 6}" fill="{col}" class="g-col" style="--i:{i * 2 + j}"/>')
            if not mob or j == 0:
                g.append(f'<text x="{x + bw / 2:.1f}" y="{Y(val) - 6:.1f}" text-anchor="middle" class="g-v g-late" fill="{C["ink"] if j == 0 else C["mut"]}">{fr(val)}</text>')
        g.append(f'<text x="{cx:.1f}" y="{h - 12}" text-anchor="middle" class="g-l">{E(lab)}</text>')
    return _svg("g-m" if mob else "g-d", w, h, titre, "".join(g))


def compare(rows, titre, nom_loc, w=WD, unite="mois"):
    """rows = [(type, valeur locale, valeur nationale)] : paires de colonnes local / national."""
    rows = [r for r in rows if r[1] is not None and r[2] is not None]
    if not rows: return ""
    return _fig("col", titre, unite, _compare_svg(rows, titre, w, False), _compare_svg(rows, titre, WM, True),
                _legend([(nom_loc, C["brand"], False), ("Moyenne nationale", C["nat"], False)]))


# --------------------------------------------------------------------------- essaim de points
def _repartition_svg(points, titre, ref, hl, hl_lab, seuil, w, mob):
    L, R, T = (10, 10, 34) if mob else (18, 18, 30)
    vmax = max(v for _, v in points) * 1.04
    X = lambda v: L + (w - L - R) * v / vmax
    rad = 3.6 if mob else 5
    gap = 1.0
    placed = []
    for c, v in sorted(points, key=lambda p: p[1]):
        x, k = X(v), 0
        while True:
            off = (k + 1) // 2 * (1 if k % 2 else -1)
            if all(abs(px - x) >= 2 * rad + gap or po != off for px, po, _, _ in placed): break
            k += 1
        placed.append((x, off, c, v))
    nl = max(abs(o) for _, o, _, _ in placed)
    mid = T + 16 + (26 if mob else 20) + nl * (2 * rad + 1)   # mobile : place pour l'étiquette mise en avant sous les titres du haut
    h = int(mid + nl * (2 * rad + 1) + 46)
    ax = h - 32
    g = [f'<line x1="{L}" x2="{w - R}" y1="{ax}" y2="{ax}" class="g-h" style="stroke-dasharray:none"/>']
    v = 0
    while v <= vmax:
        g.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{ax - 4}" y2="{ax}" class="g-h" style="stroke-dasharray:none"/>'
                 f'<text x="{min(max(X(v), L + 14), w - R - 14):.1f}" y="{h - 14}" text-anchor="middle" class="g-t">{v}{"" if mob else " mois"}</text>')
        v += 2
    xs = X(seuil)
    g.append(f'<rect x="{xs:.1f}" y="{T - 8}" width="{w - R - xs:.1f}" height="{ax - T + 8}" rx="10" class="g-zone"/>'
             f'<text x="{w - R - 8:.1f}" y="{T + 7}" text-anchor="end" class="g-t" fill="#8a5a1c">au-delà de {seuil} mois{"" if mob else " : refus implicite possible"}</text>')
    xr = X(ref)
    g.append(f'<line x1="{xr:.1f}" x2="{xr:.1f}" y1="{T + 14}" y2="{ax}" stroke="{C["ink"]}" stroke-width="1.2" stroke-dasharray="2 4"/>'
             f'<text x="{xr - 6:.1f}" y="{T + 7}" text-anchor="end" class="g-t">{"France" if mob else "moyenne France"} : {fr(ref)}</text>')
    dots, top = [], []
    for i, (x, off, c, v) in enumerate(placed):
        y = mid + off * (2 * rad + 1)
        if c in hl: top.append((x, y, c, v)); continue
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" class="g-dot" style="--i:{i}"/>')
    for x, y, c, v in top:
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad + 3}" fill="{C["brand"]}" stroke="#fff" stroke-width="2.2" class="g-late"/>')
    if top and hl_lab:
        x, y, c, v = max(top, key=lambda t: t[3])
        lab = f"{hl_lab} : {fr(v)}"
        anchor = "end" if x > w * .55 else "start"
        dx = -12 if anchor == "end" else 12
        dots.append(f'<text x="{x + dx:.1f}" y="{y - 11:.1f}" text-anchor="{anchor}" class="g-v g-late g-halo" fill="{C["brand"]}">{E(lab)}</text>')
    return _svg("g-m" if mob else "g-d", w, h, titre, "".join(g) + "".join(dots))


def repartition(points, titre, ref, hl=(), hl_lab=None, seuil=4, w=WD, unite="mois"):
    """points = [(code, valeur)] : chaque territoire est un point sur l'axe des délais (essaim compact).
    hl = codes à mettre en avant ; ref = moyenne nationale ; seuil = 4 mois (refus implicite)."""
    if not points: return ""
    return _fig("dots", titre, unite, _repartition_svg(points, titre, ref, hl, hl_lab, seuil, w, False),
                _repartition_svg(points, titre, ref, hl, hl_lab, seuil, WM, True))
