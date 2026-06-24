"""Gran Giudice — motore di scoring poetico BKS (5 assi, 1-5pt ciascuno)"""
import json
import asyncio
from openai import AsyncOpenAI
from .config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

AXES = ["image", "voice", "tension", "bks_resonance", "body"]

SYSTEM_PROMPT = """Sei il Gran Giudice BKS Verse. Valuti poesie secondo una rubrica precisa.
Opera con giudizio preciso e rispetto per chi scrive: valuta senza indulgenza per il generico,
ma riconosci sempre lo sforzo autentico.

RUBRICA — 5 assi, da 1 a 5 punti ciascuno (max totale: 25):

IMAGE (1-5): Forza dell'immagine centrale. 5 = un'immagine che non si dimentica mai.
VOICE (1-5): Unicità e riconoscibilità della voce. 5 = inconfondibile anche senza firma.
TENSION (1-5): Tensione tra elementi opposti. 5 = il verso è sul punto di spezzarsi.
BKS_RESONANCE (1-5): Affinità con l'estetica BKS (#080604, materia, oscurità controllata,
  geometria del capo). 5 = potrebbe essere il manifesto di una collezione.
BODY (1-5): Potenziale di diventare un oggetto tessile (pattern, stampa, frase su capo).
  5 = il verso è già un disegno.

GATE COMMERCIALE: 20/25 = il verso diventa prodotto BKS.
HALL OF FAME: 25/25 = evento raro. Nella storia umana, meno di 20 poeti ci sono arrivati.

Rispondi SOLO in JSON valido:
{
  "scores": {"image": N, "voice": N, "tension": N, "bks_resonance": N, "body": N},
  "total": N,
  "verdict": "approved|rejected|hall",
  "notes": {
    "image": "commento breve",
    "voice": "commento breve",
    "tension": "commento breve",
    "bks_resonance": "commento breve",
    "body": "commento breve"
  },
  "ancestor_hint": "nome-slug del poeta storico più affine (opzionale)",
  "rejection_reason": "solo se rejected: motivo specifico",
  "approval_message": "solo se approved/hall: messaggio al member (max 2 frasi, caldo e diretto)"
}"""


async def score_poem(poem_text: str, collection_slug: str = None, lang: str = "it") -> dict:
    """Invia poesia al Gran Giudice e ritorna il punteggio completo."""
    user_prompt = f"Poesia da valutare:\n\n{poem_text}"
    if collection_slug:
        user_prompt += f"\n\nCollezione BKS di riferimento: {collection_slug}"
    if lang != "it":
        user_prompt += f"\n\nLingua: {lang}"

    response = await client.chat.completions.create(
        model=settings.openai_default_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
        max_tokens=800,
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)

    # normalizza
    scores = result.get("scores", {})
    total  = sum(scores.get(a, 0) for a in AXES)
    result["total"] = total

    if total >= settings.verse_hall_of_fame_score:
        result["verdict"] = "hall"
    elif total >= settings.verse_gate_score:
        result["verdict"] = "approved"
    else:
        result["verdict"] = "rejected"

    return result


async def score_batch(poems: list[dict]) -> list[dict]:
    """Scoring parallelo per lista di poesie. Ogni elemento: {id, text, collection}."""
    tasks = [
        score_poem(p["text"], p.get("collection"), p.get("lang", "it"))
        for p in poems
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [
        {"id": p["id"], "result": r} if not isinstance(r, Exception)
        else {"id": p["id"], "error": str(r)}
        for p, r in zip(poems, results)
    ]
