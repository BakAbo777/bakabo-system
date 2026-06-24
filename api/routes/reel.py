from fastapi import APIRouter, HTTPException
import sqlite3, json
from verse_engine.config import settings

router = APIRouter()


@router.get("/storyboard/{submission_id}")
def get_storyboard(submission_id: int):
    """Ritorna lo storyboard testuale per il reel 'Il Filo'."""
    conn = sqlite3.connect(settings.verse_db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("""
        SELECT s.poem_text, s.score_total, s.lineage_note,
               p.name as poet_name, p.city, p.era, p.rep_poem_excerpt,
               p.year_birth, p.year_death
        FROM verse_submissions s
        LEFT JOIN poet_archive p ON p.id = s.ancestor_poet_id
        WHERE s.id = ? AND s.status IN ('approved','hall')
    """, (submission_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, "Submission non trovata")

    d = dict(row)
    poem_year  = 2026
    poet_year  = d["year_birth"] or "?"
    gap_years  = (poem_year - int(poet_year)) if d["year_birth"] else "?"

    storyboard = {
        "duration_seconds": 60,
        "scenes": [
            {
                "id": 1,
                "start": 0,
                "end": 8,
                "type": "title_card",
                "text": f"{d['city']}, {d['era'].split('-')[0] if d['era'] else '?'}",
                "style": "archive_bw",
                "audio": "silence_ambient",
            },
            {
                "id": 2,
                "start": 8,
                "end": 22,
                "type": "poet_verse",
                "text": d["rep_poem_excerpt"] or "",
                "poet": d["poet_name"],
                "style": "typewriter_gold",
                "audio": "giudice_voice_read",
            },
            {
                "id": 3,
                "start": 22,
                "end": 24,
                "type": "time_jump",
                "text": f"↓  {gap_years} anni dopo",
                "style": "dissolve_to_bks",
            },
            {
                "id": 4,
                "start": 24,
                "end": 40,
                "type": "member_verse",
                "text": d["poem_text"],
                "style": "bks_font_white",
                "audio": "silence",
            },
            {
                "id": 5,
                "start": 40,
                "end": 52,
                "type": "score_reveal",
                "score": d["score_total"],
                "lineage_note": d["lineage_note"] or "",
                "style": "axes_appear_one_by_one",
            },
            {
                "id": 6,
                "start": 52,
                "end": 60,
                "type": "cta",
                "text": f"{d['poet_name']} non ha più bisogno di scrivere.\nQualcuno ha continuato per lui.",
                "cta_url": "bakabo.club/verse",
                "style": "gold_on_black",
            },
        ],
        "poet": d["poet_name"],
        "poem_text": d["poem_text"],
        "lineage_note": d["lineage_note"],
    }
    return storyboard


@router.get("/episodes")
def get_episode_series():
    """Serie 'Il Giudice Esamina' — poesie storiche per reel episodici."""
    episodes = [
        {
            "ep": 1,
            "poet": "Ungaretti",
            "poem": "M'illumino d'immenso",
            "hook": "2 parole. Il Giudice le mette sotto esame.",
            "score": "25/25",
            "why_first": "Impatto massimo in 4 sillabe — ideale per primo episodio TikTok",
        },
        {
            "ep": 2,
            "poet": "Saffo",
            "poem": "Frammento 31",
            "hook": "2.600 anni fa. Sopravvissuto su papiro bruciato.",
            "score": "23/25",
            "why": "Il filo più lungo — massima distanza temporale",
        },
        {
            "ep": 3,
            "poet": "Celan",
            "poem": "Todesfuge",
            "hook": "Scritto in tedesco da un sopravvissuto all'Olocausto.",
            "score": "24/25",
            "why": "Oscurità BKS al massimo — controverso, fa engagement",
        },
        {
            "ep": 4,
            "poet": "Rimbaud",
            "poem": "Le Bateau ivre",
            "hook": "A 19 anni scrisse questo. Poi smise per sempre.",
            "score": "24/25",
            "why": "Abbandono della poesia per il commercio = BKS in reverse",
        },
        {
            "ep": 5,
            "poet": "e.e. cummings",
            "poem": "l(a",
            "hook": "Una foglia che cade. Costruita con le lettere.",
            "score": "25/25",
            "why": "Visivamente è già un pattern tessile",
        },
    ]
    return {"episodes": episodes, "series_title": "Il Giudice Esamina", "platform": "TikTok + Instagram Reels"}
