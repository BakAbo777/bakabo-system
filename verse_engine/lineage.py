"""Il Filo — identifica l'antenato poetico storico e genera il momento di incontro."""
import json
from openai import AsyncOpenAI
from .config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

LINEAGE_PROMPT = """Sei un critico letterario che identifica affinità tra un verso contemporaneo
e la tradizione poetica mondiale. Opera con precisione filologica.

Hai a disposizione l'archivio poetico BKS (fornito come contesto).
Identifica UN SOLO poeta dall'archivio che rappresenta l'antenato più significativo
del verso analizzato. Non scegliere quello ovvio — scegli quello vero.

Rispondi SOLO in JSON:
{
  "ancestor_slug": "slug del poeta",
  "connection_type": "image|voice|tension|structure|theme",
  "lineage_note": "spiegazione in 2-3 frasi (tono critico, non didattico)",
  "il_filo_message": "il poeta storico ringrazia il member in prima persona, voce del poeta, max 3 righe",
  "time_place": "luogo e anno del poeta storico (es: Parigi, 1873)",
  "reel_opening": "prima didascalia del reel (max 120 caratteri)"
}"""


async def find_ancestor(poem_text: str, giudice_notes: dict, poets_archive: list) -> dict:
    """
    Trova l'antenato poetico per un verso approvato.
    poets_archive: lista semplificata dei poeti dal DB.
    """
    archive_summary = "\n".join(
        f"- {p['slug']}: {p['name']} ({p['country_code']}, {p['era']}) — {p['rep_poem_title']}"
        for p in poets_archive
    )

    user_msg = f"""VERSO CONTEMPORANEO:
{poem_text}

NOTE DEL GIUDICE:
{json.dumps(giudice_notes, ensure_ascii=False, indent=2)}

ARCHIVIO POETICO BKS:
{archive_summary}"""

    response = await client.chat.completions.create(
        model=settings.openai_default_model,
        messages=[
            {"role": "system", "content": LINEAGE_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.5,
        response_format={"type": "json_object"},
        max_tokens=600,
    )

    return json.loads(response.choices[0].message.content)


def build_lineage_card(poet: dict, poem_text: str, lineage: dict, member_display: str = "Member BKS") -> dict:
    """Costruisce la Lineage Card completa per dashboard e reel."""
    return {
        "type": "lineage_card",
        "poet": {
            "name": poet["name"],
            "era": poet["era"],
            "city": poet.get("city", ""),
            "rep_poem_title": poet["rep_poem_title"],
            "rep_poem_excerpt": poet["rep_poem_excerpt"],
            "score_total": sum([
                poet.get("score_image", 0),
                poet.get("score_voice", 0),
                poet.get("score_tension", 0),
                poet.get("score_bks", 0),
                poet.get("score_body", 0),
            ]),
        },
        "member": {
            "display": member_display,
            "poem_text": poem_text,
            "year": 2026,
        },
        "lineage": lineage,
        "reel": {
            "opening": lineage.get("reel_opening", ""),
            "time_place": lineage.get("time_place", ""),
            "poet_voice": lineage.get("il_filo_message", ""),
            "cta": "Puoi battere questo punteggio? bakabo.club/verse",
        }
    }
