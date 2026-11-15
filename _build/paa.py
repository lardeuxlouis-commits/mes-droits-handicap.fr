#!/usr/bin/env python3
"""Relevé des « Autres questions posées » de Google via Firecrawl (proxy stealth). Usage : paa.py sortie.txt requête1 | requête2 ..."""
import json, re, sys, html, os, time, urllib.request, urllib.parse
K = open(os.path.expanduser("~/elio-keys/firecrawl.key")).read().strip()
def scrape(q):
    u = "https://www.google.com/search?" + urllib.parse.urlencode({"q": q, "hl": "fr", "gl": "fr"})
    body = json.dumps({"url": u, "formats": ["rawHtml", "markdown"], "proxy": "stealth", "location": {"country": "FR", "languages": ["fr"]}}).encode()
    r = urllib.request.Request("https://api.firecrawl.dev/v2/scrape", body, {"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    try: d = json.loads(urllib.request.urlopen(r, timeout=120).read())
    except Exception as e: return None
    return d.get("data")
out = open(sys.argv[1], "a", encoding="utf-8")
for q in sys.argv[2:]:
    qs = []
    for essai in range(6):
        d = scrape(q)
        if not d: time.sleep(3); continue
        h = d.get("rawHtml") or ""
        qs = list(dict.fromkeys(html.unescape(x) for x in re.findall(r'data-q="([^"]+)"', h)))
        if not qs:
            qs = list(dict.fromkeys(html.unescape(x).strip() for x in re.findall(r'<span>([^<>]{12,160}\?)</span>', h)))
        if qs: break
    out.write(q + " => " + " | ".join(qs) + "\n"); out.flush()
    print(q, len(qs))
