"""
Deploy sezioni BKS Verse → tema Shopify TM04 live.
Usa la stessa logica di I:\BAK ABO\scripts\deploy_theme_section.py
ma punta alle risorse in BAKABO SYSTEM/shopify/.
"""
import sys
import os
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from pathlib import Path

ROOT   = Path(__file__).parent.parent
SHOPIFY_DIR = ROOT / "shopify"

# Legge .env dal BAK ABO (dove sono le chiavi reali)
BAKABO_ENV = Path("I:/BAK ABO/.env")
env = {}
if BAKABO_ENV.exists():
    for line in BAKABO_ENV.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

STORE   = env.get("SHOPIFY_MYSHOPIFY_DOMAIN", env.get("SHOPIFY_STORE", "11628e-2.myshopify.com"))
TOKEN   = env.get("SHOPIFY_ADMIN_TOKEN", env.get("SHOPIFY_ADMIN_API_KEY", ""))
VERSION = env.get("SHOPIFY_API_VERSION", "2025-01")
THEME   = env.get("SHOPIFY_THEME_ID", "202392961362")

if not TOKEN:
    print("[ERRORE] SHOPIFY_ADMIN_TOKEN non trovata in I:\\BAK ABO\\.env")
    sys.exit(1)

BASE_URL = f"https://{STORE}/admin/api/{VERSION}/themes/{THEME}/assets.json"
HEADERS  = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}

FILES_TO_DEPLOY = [
    ("assets/bks-verse.css",                   SHOPIFY_DIR / "assets/bks-verse.css"),
    ("assets/bks-verse.js",                    SHOPIFY_DIR / "assets/bks-verse.js"),
    ("sections/bks-verse-intro.liquid",        SHOPIFY_DIR / "sections/bks-verse-intro.liquid"),
    ("sections/bks-verse-submit.liquid",       SHOPIFY_DIR / "sections/bks-verse-submit.liquid"),
    ("sections/bks-verse-leaderboard.liquid",  SHOPIFY_DIR / "sections/bks-verse-leaderboard.liquid"),
    ("sections/bks-verse-hall.liquid",         SHOPIFY_DIR / "sections/bks-verse-hall.liquid"),
    ("templates/page.bks-verse.json",          SHOPIFY_DIR / "templates/page.bks-verse.json"),
    ("templates/page.bks-verse-hall.json",     SHOPIFY_DIR / "templates/page.bks-verse-hall.json"),
]


def deploy_file(shopify_key: str, local_path: Path) -> bool:
    content = local_path.read_text(encoding="utf-8")
    payload = {"asset": {"key": shopify_key, "value": content}}
    resp = requests.put(BASE_URL, json=payload, headers=HEADERS, timeout=20, verify=False)
    ok = resp.status_code in (200, 201)
    status = "OK" if ok else f"ERR {resp.status_code}"
    print(f"  [{status}] {shopify_key}")
    if not ok:
        print(f"         {resp.text[:120]}")
    return ok


if __name__ == "__main__":
    print(f"\nDeploy BKS Verse -> tema {THEME} su {STORE}")
    print(f"Files: {len(FILES_TO_DEPLOY)}\n")

    ok_count = 0
    for shopify_key, local_path in FILES_TO_DEPLOY:
        if not local_path.exists():
            print(f"  [SKIP] {local_path.name} non trovato")
            continue
        if deploy_file(shopify_key, local_path):
            ok_count += 1

    print(f"\n{'='*48}")
    print(f"Deploiati: {ok_count}/{len(FILES_TO_DEPLOY)}")
    if ok_count == len(FILES_TO_DEPLOY):
        print("Tutto OK. Crea le pagine su Shopify Admin con i template:")
        print("  page.bks-verse       → /pages/verse")
        print("  page.bks-verse-hall  → /pages/verse-hall")
    print(f"{'='*48}\n")
