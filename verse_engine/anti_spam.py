"""Anti-spam: GPTZero detection + behavioral gate."""
import httpx
from .config import settings


async def check_ai_probability(poem_text: str) -> dict:
    """Chiama GPTZero API. Ritorna score umano (0-1) e flag."""
    if not settings.gptzero_api_key:
        return {"human_score": 1.0, "flagged": False, "source": "skipped"}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.gptzero.me/v2/predict/text",
            headers={
                "x-api-key": settings.gptzero_api_key,
                "Content-Type": "application/json",
            },
            json={"document": poem_text},
        )
        resp.raise_for_status()
        data = resp.json()

    human_score = data.get("documents", [{}])[0].get("average_generated_prob", 0.0)
    human_score = 1.0 - human_score  # GPTZero ritorna prob di essere AI, noi vogliamo human

    return {
        "human_score": round(human_score, 3),
        "flagged": human_score < settings.gptzero_min_human_score,
        "source": "gptzero",
        "raw": data,
    }


def validate_poem_text(text: str) -> dict:
    """Validazione locale prima del Giudice."""
    errors = []
    warnings = []

    text = text.strip()
    char_count = len(text)

    if char_count < settings.verse_min_chars:
        errors.append(f"Testo troppo breve ({char_count} caratteri, minimo {settings.verse_min_chars})")
    if char_count > settings.verse_max_chars:
        errors.append(f"Testo troppo lungo ({char_count} caratteri, massimo {settings.verse_max_chars})")

    # check contenuto minimo
    words = text.split()
    if len(words) < 5:
        errors.append("Troppo poche parole")
    if text == text.upper() and len(words) > 3:
        warnings.append("Testo tutto maiuscolo — potrebbe penalizzare Voice")

    # ripetizioni banali
    unique_words = set(w.lower().strip(".,!?;:") for w in words)
    if len(unique_words) < len(words) * 0.4:
        warnings.append("Alta ripetizione di parole — Giudice potrebbe penalizzare Voice")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "char_count": char_count,
        "word_count": len(words),
    }


async def full_gate(poem_text: str, member_email: str, poet_score: float = 0.0) -> dict:
    """Gate completo: validazione + GPTZero + Poet Score boost."""
    validation = validate_poem_text(poem_text)
    if not validation["valid"]:
        return {"passed": False, "reason": "validation", "detail": validation}

    spam = await check_ai_probability(poem_text)
    if spam["flagged"]:
        # Poet Score alto può abbassare la soglia di sospetto
        adjusted = spam["human_score"] + (poet_score / 200)  # max +0.5 boost
        if adjusted < settings.gptzero_min_human_score:
            return {
                "passed": False,
                "reason": "ai_detected",
                "detail": spam,
                "poet_score_applied": poet_score,
            }

    return {
        "passed": True,
        "validation": validation,
        "spam_check": spam,
        "poet_score_applied": poet_score,
    }
