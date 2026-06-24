"""
Fix .env — Roberto lancia questo script manualmente.
Corregge:
  1. PRINTIFY_SHOP_ID da 5295165689 → 12030061
  2. Rimuove righe non valide (hash R2 + curl example) in fondo al file
  3. Aggiunge VERSE_SECRET_KEY se mancante
"""
import re
import secrets
from pathlib import Path

ENV_PATH = Path(__file__).parent.parent / ".env"


def fix():
    text = ENV_PATH.read_text(encoding="utf-8")
    changes = []

    # 1. Fix PRINTIFY_SHOP_ID
    if "PRINTIFY_SHOP_ID=5295165689" in text:
        text = text.replace("PRINTIFY_SHOP_ID=5295165689", "PRINTIFY_SHOP_ID=12030061")
        changes.append("PRINTIFY_SHOP_ID corretto: 5295165689 → 12030061")

    # 2. Rimuovi righe non valide (hash R2 e curl example) mantenendo blank lines e comments
    invalid_patterns = [
        r"^bdc8d0264bbddd98c8edffc58fdb0f59.*$",
        r"^a922c8ff1bc584dfdef683ba2f13f150.*$",
        r"^https://[a-f0-9]+\.r2\.cloudflarestorage\.com.*$",
        r"^Example Usage:curl.*$",
        r"^\s+-H \"Authorization: Bearer cfat_.*$",
    ]
    lines = text.splitlines()
    clean_lines = []
    removed = 0
    for line in lines:
        skip = False
        for pat in invalid_patterns:
            if re.match(pat, line):
                skip = True
                removed += 1
                break
        if not skip:
            clean_lines.append(line)
    text = "\n".join(clean_lines)
    if removed:
        changes.append(f"{removed} righe non valide rimosse")

    # 3. Aggiungi VERSE_SECRET_KEY se mancante
    if "VERSE_SECRET_KEY=" not in text:
        secret = secrets.token_hex(32)
        text = text.rstrip("\n") + f"\n\nVERSE_SECRET_KEY={secret}\n"
        changes.append(f"VERSE_SECRET_KEY aggiunto (chiave random)")

    if not changes:
        print("[OK] .env già corretto, nessuna modifica necessaria.")
        return

    # Backup
    backup = ENV_PATH.with_suffix(".env.bak")
    backup.write_text(ENV_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[backup] {backup}")

    ENV_PATH.write_text(text, encoding="utf-8")
    for c in changes:
        print(f"[fix] {c}")
    print(f"\n[OK] .env aggiornato → {ENV_PATH}")


if __name__ == "__main__":
    fix()
