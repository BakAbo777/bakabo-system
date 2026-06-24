"""Inizializza il database SQLite e carica i poeti storici."""
import sqlite3, json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from verse_engine.config import settings

DB_PATH  = Path(settings.verse_db_path)
SCHEMA   = ROOT / "data" / "schema.sql"
POETS    = ROOT / "data" / "poets.json"


def init():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    with open(SCHEMA) as f:
        conn.executescript(f.read())
    conn.commit()
    print(f"[OK] Schema applicato -> {DB_PATH}")

    # Carica poeti
    poets = json.loads(POETS.read_text(encoding="utf-8"))
    inserted = 0
    for p in poets:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO poet_archive
                (slug, name, country_code, era, city, year_birth, year_death,
                 rep_poem_title, rep_poem_excerpt, rep_poem_lang,
                 score_image, score_voice, score_tension, score_bks, score_body,
                 photo_url, bio_short)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                p["slug"], p["name"], p["country_code"], p["era"], p.get("city"),
                p.get("year_birth"), p.get("year_death"),
                p.get("rep_poem_title"), p.get("rep_poem_excerpt"), p.get("rep_poem_lang", "it"),
                p["score_image"], p["score_voice"], p["score_tension"],
                p["score_bks"], p["score_body"],
                p.get("photo_url", ""), p.get("bio_short", ""),
            ))
            inserted += 1
        except Exception as e:
            print(f"  SKIP {p['slug']}: {e}")
    conn.commit()
    conn.close()
    print(f"[OK] {inserted}/{len(poets)} poeti caricati")


if __name__ == "__main__":
    init()
