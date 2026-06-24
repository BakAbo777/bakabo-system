from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, field_validator
import sqlite3
from verse_engine.submission import process_submission
from verse_engine.artwork import full_artwork_pipeline, publish_product
from verse_engine.notifications import notify_discord, notify_telegram
from verse_engine.config import settings

router = APIRouter()


class SubmitRequest(BaseModel):
    member_email: str
    poem_text: str
    collection_slug: str | None = None
    lang: str = "it"
    member_id: str | None = None
    member_display: str | None = None

    @field_validator("poem_text")
    @classmethod
    def validate_length(cls, v):
        v = v.strip()
        if len(v) < settings.verse_min_chars:
            raise ValueError(f"Min {settings.verse_min_chars} caratteri")
        if len(v) > settings.verse_max_chars:
            raise ValueError(f"Max {settings.verse_max_chars} caratteri")
        return v


def _db():
    conn = sqlite3.connect(settings.verse_db_path)
    conn.row_factory = sqlite3.Row
    return conn


@router.post("/submit")
async def submit_verse(req: SubmitRequest):
    result = await process_submission(
        member_email=req.member_email,
        poem_text=req.poem_text,
        collection_slug=req.collection_slug,
        lang=req.lang,
        member_id=req.member_id,
        member_display=req.member_display,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result


@router.get("/status/{submission_id}")
def get_status(submission_id: int):
    conn = _db()
    row = conn.execute(
        """SELECT id, status, score_total, giudice_verdict, submitted_at,
                  score_image, score_voice, score_tension, score_bks, score_body,
                  product_id, product_created
           FROM verse_submissions WHERE id = ?""",
        (submission_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Submission non trovata")
    return dict(row)


@router.post("/approve/{submission_id}")
async def approve_and_generate(
    submission_id: int,
    x_admin_key: str = Header(default=""),
):
    """
    Roberto approva una submission approvata → genera artwork + crea draft Shopify.
    Richiede header X-Admin-Key = VERSE_SECRET_KEY.
    """
    if x_admin_key != settings.verse_secret_key:
        raise HTTPException(403, "Non autorizzato")

    conn = _db()
    row = conn.execute(
        """SELECT s.*, p.name as ancestor_name
           FROM verse_submissions s
           LEFT JOIN poet_archive p ON p.id = s.ancestor_poet_id
           WHERE s.id = ? AND s.status IN ('approved','hall')""",
        (submission_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, "Submission non trovata o non approvata")

    row = dict(row)
    import json
    notes = json.loads(row.get("giudice_notes") or "{}")

    result = await full_artwork_pipeline(
        submission_id=submission_id,
        poem_text=row["poem_text"],
        score=row["score_total"],
        collection_slug=row.get("collection_slug") or "bks-verse",
        ancestor_poet=row.get("ancestor_name") or "tradizione poetica",
        giudice_notes=notes,
    )

    conn = _db()
    conn.execute(
        "UPDATE verse_submissions SET product_id = ?, product_created = 1 WHERE id = ?",
        (result["product_id"], submission_id)
    )
    conn.commit()
    conn.close()

    await notify_telegram(
        f"Artwork generato #{submission_id}\n"
        f"Product: {result['product_url']}\n"
        f"Score: {row['score_total']}/25"
    )

    return result


@router.post("/publish/{submission_id}")
async def publish_verse_product(
    submission_id: int,
    x_admin_key: str = Header(default=""),
):
    """
    Roberto pubblica il prodotto draft → live su Shopify.
    Richiede header X-Admin-Key = VERSE_SECRET_KEY.
    """
    if x_admin_key != settings.verse_secret_key:
        raise HTTPException(403, "Non autorizzato")

    conn = _db()
    row = conn.execute(
        "SELECT product_id, poem_text, score_total, member_email FROM verse_submissions WHERE id = ?",
        (submission_id,)
    ).fetchone()
    conn.close()

    if not row or not row["product_id"]:
        raise HTTPException(404, "Prodotto non trovato — usa /approve prima")

    ok = await publish_product(row["product_id"])
    if not ok:
        raise HTTPException(500, "Errore pubblicazione Shopify")

    conn = _db()
    conn.execute(
        "UPDATE verse_submissions SET status = 'published' WHERE id = ?",
        (submission_id,)
    )
    conn.commit()
    conn.close()

    product_url = f"https://{settings.shopify_store}/products/bks-verse-{submission_id}"

    await notify_discord(
        settings.discord_webhook_verse,
        f"**Nuovo prodotto Verse live!**\n{row['poem_text'][:80]}...\n[Vedi prodotto]({product_url})",
        title=f"BKS Verse #{submission_id} — {row['score_total']}/25",
        color=0xFFD700,
    )
    await notify_telegram(f"LIVE #{submission_id} — {product_url}")

    return {"published": True, "product_url": product_url, "submission_id": submission_id}


@router.get("/pending")
def list_pending(x_admin_key: str = Header(default="")):
    """Lista submission approvate in attesa di artwork/pubblicazione."""
    if x_admin_key != settings.verse_secret_key:
        raise HTTPException(403, "Non autorizzato")

    conn = _db()
    rows = conn.execute(
        """SELECT id, member_email, score_total, poem_text, submitted_at,
                  product_created, product_id, status
           FROM verse_submissions
           WHERE status IN ('approved','hall')
           ORDER BY score_total DESC, submitted_at ASC"""
    ).fetchall()
    conn.close()
    return {"pending": [dict(r) for r in rows], "total": len(rows)}
