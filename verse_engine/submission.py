"""Pipeline completa di submission: gate → Giudice → lineage → notifiche → DB."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from .config import settings
from .giudice import score_poem
from .lineage import find_ancestor, build_lineage_card
from .anti_spam import full_gate
from .notifications import dispatch_verdict


def get_db():
    db_path = Path(settings.verse_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_poets_archive() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM poet_archive").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_member_poet_score(member_email: str) -> float:
    conn = get_db()
    row = conn.execute(
        "SELECT poet_score FROM member_poet_score WHERE member_email = ?",
        (member_email,)
    ).fetchone()
    conn.close()
    return row["poet_score"] if row else 0.0


async def verify_brass_tier(member_email: str, member_id: str = None) -> bool:
    """Verifica tier Brass+ via Shopify (placeholder — implementare con API reale)."""
    # TODO: chiamata Shopify Admin API per leggere metafield member_tier
    # Per ora, accetta sempre in sviluppo
    return True


async def process_submission(
    member_email: str,
    poem_text: str,
    collection_slug: str = None,
    lang: str = "it",
    member_id: str = None,
    member_display: str = None,
) -> dict:
    """
    Pipeline completa per una submission.
    Ritorna dict con: submission_id, verdict, score, lineage_card (se approved)
    """

    # 1. Gate Brass+
    if not await verify_brass_tier(member_email, member_id):
        return {"error": "tier_required", "message": "BKS Verse richiede tier Brass o superiore."}

    # 2. Anti-spam + validazione
    poet_score = get_member_poet_score(member_email)
    gate = await full_gate(poem_text, member_email, poet_score)
    if not gate["passed"]:
        return {"error": gate["reason"], "detail": gate}

    # 3. Gran Giudice scoring
    result = await score_poem(poem_text, collection_slug, lang)
    score_total = result["total"]
    verdict = result["verdict"]

    # 4. Salva in DB
    conn = get_db()
    scores = result.get("scores", {})
    notes = result.get("notes", {})
    cursor = conn.execute("""
        INSERT INTO verse_submissions
        (member_email, member_id, collection_slug, poem_text, poem_lang, char_count,
         score_image, score_voice, score_tension, score_bks, score_body, score_total,
         giudice_notes, giudice_verdict, scored_at, gptzero_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        member_email, member_id, collection_slug, poem_text, lang, len(poem_text),
        scores.get("image"), scores.get("voice"), scores.get("tension"),
        scores.get("bks_resonance"), scores.get("body"), score_total,
        json.dumps(notes, ensure_ascii=False),
        verdict, datetime.utcnow().isoformat(),
        gate.get("spam_check", {}).get("human_score"),
        verdict,
    ))
    submission_id = cursor.lastrowid
    conn.commit()

    # 5. Lineage (solo se approvato)
    lineage_card = None
    ancestor_name = ""
    if verdict in ("approved", "hall"):
        poets_archive = get_poets_archive()
        if poets_archive:
            lineage = await find_ancestor(poem_text, notes, poets_archive)
            ancestor_slug = lineage.get("ancestor_slug", "")

            poet = next((p for p in poets_archive if p["slug"] == ancestor_slug), None)
            if poet:
                ancestor_name = poet["name"]
                lineage_card = build_lineage_card(poet, poem_text, lineage,
                                                   member_display or member_email.split("@")[0])
                conn.execute(
                    "UPDATE verse_submissions SET ancestor_poet_id = ?, lineage_note = ? WHERE id = ?",
                    (poet["id"], lineage.get("lineage_note", ""), submission_id)
                )
                conn.commit()

    # 6. Hall of Fame
    if verdict == "hall":
        hall_num = conn.execute("SELECT COUNT(*)+1 FROM verse_hall").fetchone()[0]
        conn.execute("""
            INSERT INTO verse_hall (submission_id, member_email, member_display, poem_text,
              score_total, ancestor_poet_slug, limited_edition_num)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (submission_id, member_email, member_display, poem_text, score_total,
              lineage_card["poet"]["slug"] if lineage_card else None, hall_num))
        conn.commit()

    conn.close()

    # 7. Notifiche
    await dispatch_verdict(
        submission_id, member_email, verdict, score_total,
        poem_text[:120],
        ancestor_name=ancestor_name,
        rejection_reason=result.get("rejection_reason", ""),
    )

    return {
        "submission_id": submission_id,
        "verdict": verdict,
        "score_total": score_total,
        "scores": scores,
        "notes": notes,
        "approval_message": result.get("approval_message", ""),
        "lineage_card": lineage_card,
    }
