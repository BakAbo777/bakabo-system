from fastapi import APIRouter, HTTPException
import sqlite3, json
from verse_engine.config import settings

router = APIRouter()


@router.get("/submission/{submission_id}")
def get_lineage(submission_id: int):
    conn = sqlite3.connect(settings.verse_db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("""
        SELECT s.*, p.name as poet_name, p.era, p.city, p.rep_poem_title,
               p.rep_poem_excerpt, p.score_total as poet_score_total
        FROM verse_submissions s
        LEFT JOIN poet_archive p ON p.id = s.ancestor_poet_id
        WHERE s.id = ? AND s.status IN ('approved','hall')
    """, (submission_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Submission non trovata o non approvata")
    return dict(row)


@router.get("/map")
def lineage_map():
    """Costellazione: per ogni poeta storico, quanti members ha ispirato."""
    conn = sqlite3.connect(settings.verse_db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT p.slug, p.name, p.country_code, p.era,
               COUNT(s.id) as inspired_count,
               MAX(s.score_total) as top_score
        FROM poet_archive p
        LEFT JOIN verse_submissions s ON s.ancestor_poet_id = p.id
            AND s.status IN ('approved','hall')
        GROUP BY p.id
        ORDER BY inspired_count DESC, p.score_total DESC
    """).fetchall()
    conn.close()
    return {"map": [dict(r) for r in rows]}
