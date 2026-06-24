from fastapi import APIRouter
import sqlite3
from verse_engine.config import settings

router = APIRouter()


def _get_conn():
    conn = sqlite3.connect(settings.verse_db_path)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/global")
def global_ranking(limit: int = 30):
    """Classifica unificata: poeti storici + members BKS."""
    conn = _get_conn()

    # Poeti storici — score_total calcolato in Python per compatibilità SQLite
    poets = conn.execute("""
        SELECT name, country_code, rep_poem_title as poem_title,
               (score_image + score_voice + score_tension + score_bks + score_body) as total,
               score_image, score_voice, score_tension, score_bks, score_body,
               'storico' as type, era, city
        FROM poet_archive
    """).fetchall()

    # Top member submissions approvate
    members = conn.execute("""
        SELECT member_email, NULL as member_display, poem_text,
               (score_image + score_voice + score_tension + score_bks + score_body) as total,
               score_image, score_voice, score_tension, score_bks, score_body,
               'member' as type, submitted_at
        FROM verse_submissions
        WHERE status IN ('approved', 'hall')
        ORDER BY total DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()

    ranking = []
    for p in poets:
        d = dict(p)
        d["display_name"] = d["name"]
        ranking.append(d)
    for m in members:
        d = dict(m)
        d["display_name"] = d.get("member_display") or d["member_email"].split("@")[0]
        d["poem_title"] = d["poem_text"][:60] + "..." if len(d["poem_text"]) > 60 else d["poem_text"]
        ranking.append(d)

    ranking.sort(key=lambda x: (x["total"] or 0), reverse=True)

    # aggiungi posizione
    for i, item in enumerate(ranking):
        item["rank"] = i + 1

    return {"ranking": ranking, "total": len(ranking)}


@router.get("/hall")
def hall_of_fame():
    """Solo 25/25."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT h.*, p.name as ancestor_name
        FROM verse_hall h
        LEFT JOIN poet_archive p ON p.slug = h.ancestor_poet_slug
        ORDER BY h.inducted_at DESC
    """).fetchall()
    conn.close()

    # Aggiungi poeti storici 25/25
    static = [
        {"display_name": "e.e. cummings", "poem_title": '"l(a"', "score_total": 25, "type": "storico"},
        {"display_name": "Ungaretti", "poem_title": '"M\'illumino d\'immenso"', "score_total": 25, "type": "storico"},
    ]
    members = [dict(r) for r in rows]
    return {"hall": static + members}
