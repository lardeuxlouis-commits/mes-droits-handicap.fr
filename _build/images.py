#!/usr/bin/env python3
"""Génère les 6 illustrations (WaveSpeed Seedream v4). La clé n'est jamais affichée."""
import json, os, sys, time, urllib.request
K = open(os.path.expanduser("~/elio-keys/wavespeed.key")).read().strip()
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_images-brutes")
BASE = (" Natural documentary photograph, soft warm daylight from a window, calm and dignified everyday life in France, "
        "muted palette with touches of violet and warm yellow, shallow depth of field, people seen from the side or from behind or with faces not in focus, "
        "no text, no logo, no flag, no official building, not sad, not staged, realistic.")
P = {
 "accueil": "A woman in her forties and her adult son who uses a manual wheelchair sit at a bright kitchen table, sorting papers and a laptop together, a mug of tea, relaxed and focused.",
 "enfant": "A father helps his young daughter wearing hearing aids with her homework at a wooden desk in a sunny living room, colored pencils, a calm moment of complicity.",
 "travail": "A man with a prosthetic leg works at a standing desk in a modern bright office, colleagues blurred in the background, ordinary working day.",
 "domicile": "A home care assistant helps an adult woman with a walker prepare vegetables in her own kitchen, both busy with the task, warm and respectful.",
 "demarches": "Close view of hands filling in a paper form with a pen next to an open laptop and a folder of documents on a table, a white cane resting against the table edge.",
 "mobilite": "A young woman using a power wheelchair rolls onto an accessible city tram platform on a sunny morning, seen from behind, urban street, everyday commute.",
}
def post(url, data):
    r = urllib.request.Request(url, json.dumps(data).encode(), {"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())
def get(url):
    r = urllib.request.Request(url, headers={"Authorization": "Bearer " + K})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())
for nom in (sys.argv[1:] or P):
    if os.path.exists(os.path.join(OUT, nom + ".jpg")): continue
    try: d = post("https://api.wavespeed.ai/api/v3/bytedance/seedream-v4", {"prompt": P[nom] + BASE, "size": "2048*1366"})
    except Exception as e: print(nom, "erreur", e); continue
    pid = d["data"]["id"]
    for _ in range(60):
        time.sleep(4)
        r = get(f"https://api.wavespeed.ai/api/v3/predictions/{pid}/result")["data"]
        if r["status"] == "completed":
            urllib.request.urlretrieve(r["outputs"][0], os.path.join(OUT, nom + ".jpg")); print(nom, "ok"); break
        if r["status"] == "failed": print(nom, "échec", r.get("error")); break
print("solde", get("https://api.wavespeed.ai/api/v3/balance")["data"])
