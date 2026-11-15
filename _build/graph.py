"""Graphiques SVG générés au build (aucun script, aucune bibliothèque tierce)."""
import html

E = lambda s: html.escape(str(s), quote=True)
C = {"brand": "#4a2f7e", "sun": "#d9951c", "mut": "#8a8499", "line": "#e3dfec", "alert": "#a8401b", "ok": "#1d6e4f"}


def fr(x, d=1):
    s = f"{x:.{d}f}".replace(".", ",")
    return s


def lignes(series, labels, titre, unite="mois", h=230, w=640, ymin=0):
    """series = [(nom, couleur, [valeurs ou None], pointillé)] ; labels = étiquettes de l'axe x."""
    vals = [v for _, _, s, _ in series for v in s if v is not None]
    if not vals: return ""
    ymax = max(vals) * 1.12
    ymax = max(ymax, 1)
    L, R, T, B = 34, 12, 14, 30
    n = len(labels)
    X = lambda i: L + (w - L - R) * (i / max(n - 1, 1))
    Y = lambda v: T + (h - T - B) * (1 - (v - ymin) / (ymax - ymin))
    g = []
    step = 1 if ymax <= 8 else 2 if ymax <= 16 else 5
    v = 0
    while v <= ymax:
        g.append(f'<line x1="{L}" x2="{w - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{C["line"]}"/><text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end" font-size="11" fill="{C["mut"]}">{v}</text>')
        v += step
    every = max(1, n // 7)
    for i, lab in enumerate(labels):
        if i % every == 0 or i == n - 1:
            g.append(f'<text x="{X(i):.1f}" y="{h - 10}" text-anchor="middle" font-size="11" fill="{C["mut"]}">{E(lab)}</text>')
    leg = []
    for k, (nom, col, s, dash) in enumerate(series):
        pts, seg = [], []
        for i, v in enumerate(s):
            if v is None:
                if len(seg) > 1: pts.append(seg)
                seg = []; continue
            seg.append(f"{X(i):.1f},{Y(v):.1f}")
        if len(seg) > 1: pts.append(seg)
        da = 'stroke-dasharray="5 4" ' if dash else ""
        for p in pts:
            g.append(f'<polyline fill="none" stroke="{col}" stroke-width="{2.2 if dash else 3}" {da}stroke-linejoin="round" stroke-linecap="round" points="{" ".join(p)}"/>')
        last = max((i for i, v in enumerate(s) if v is not None), default=None)
        if last is not None:
            g.append(f'<circle cx="{X(last):.1f}" cy="{Y(s[last]):.1f}" r="4" fill="{col}"/>')
        leg.append(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px"><span style="width:18px;height:3px;background:{col};display:inline-block"></span>{E(nom)}</span>')
    return (f'<figure class="mdh-chart"><svg viewBox="0 0 {w} {h}" role="img" aria-label="{E(titre)}"><title>{E(titre)}</title>{"".join(g)}</svg>'
            f'<figcaption>{"".join(leg)}<br>{E(titre)}, en {unite}.</figcaption></figure>')


def barres(items, titre, ref=None, ref_lab="moyenne nationale", w=640, unite="mois", hl=None):
    """items = [(étiquette, valeur, lien ou None)] : barres horizontales."""
    if not items: return ""
    rh, L, R = 24, 200, 52
    h = rh * len(items) + 26
    vmax = max(v for _, v, _ in items) * 1.05
    X = lambda v: L + (w - L - R) * v / vmax
    g = []
    for i, (lab, v, lien) in enumerate(items):
        y = 8 + i * rh
        col = C["alert"] if hl and lab == hl else C["brand"]
        t = f'<text x="{L - 8}" y="{y + 15}" text-anchor="end" font-size="12.5" fill="#1f1b2d">{E(lab)}</text>'
        if lien: t = f'<a href="{E(lien)}">{t}</a>'
        g.append(t + f'<rect x="{L}" y="{y + 3}" width="{X(v) - L:.1f}" height="{rh - 8}" rx="4" fill="{col}"/>'
                 f'<text x="{X(v) + 6:.1f}" y="{y + 15}" font-size="12" fill="#1f1b2d">{fr(v)}</text>')
    if ref:
        g.append(f'<line x1="{X(ref):.1f}" x2="{X(ref):.1f}" y1="4" y2="{h - 18}" stroke="{C["sun"]}" stroke-width="2" stroke-dasharray="4 3"/>'
                 f'<text x="{min(X(ref), w - 150):.1f}" y="{h - 4}" text-anchor="{"middle" if X(ref) < w - 150 else "start"}" font-size="11.5" fill="#6b4500">{E(ref_lab)} : {fr(ref)}</text>')
    return (f'<figure class="mdh-chart"><svg viewBox="0 0 {w} {h}" role="img" aria-label="{E(titre)}"><title>{E(titre)}</title>{"".join(g)}</svg>'
            f'<figcaption>{E(titre)}, en {unite}.</figcaption></figure>')
