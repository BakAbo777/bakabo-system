"""Test rapido del Giudice con una poesia campione."""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from verse_engine.giudice import score_poem

TEST_POEMS = [
    {
        "title": "Test 1 — minimal BKS",
        "text": "il nero respira\nprima che la luce\ncapisce di non poter entrare",
        "collection": "bks-hours",
    },
    {
        "title": "Test 2 — troppo generico (atteso rejected)",
        "text": "il cielo è blu\nle stelle brillano la notte\npenso a te sempre\nsei la mia vita",
        "collection": None,
    },
    {
        "title": "Test 3 — alta tensione",
        "text": "cucio il silenzio con filo d'osso\nnon è un tessuto — è una cicatrice\nla indossi comunque",
        "collection": "bks-glyph",
    },
]


async def main():
    print("\n" + "="*60)
    print("BKS VERSE — Test Gran Giudice")
    print("="*60)
    for poem in TEST_POEMS:
        print(f"\n[{poem['title']}]")
        print(f"Testo: {poem['text'][:80]}...")
        result = await score_poem(poem["text"], poem.get("collection"))
        sc = result.get("scores", {})
        print(f"  Image={sc.get('image')} Voice={sc.get('voice')} Tension={sc.get('tension')}")
        print(f"  BKS={sc.get('bks_resonance')} Body={sc.get('body')}")
        print(f"  TOTALE: {result.get('total')}/25 → {result.get('verdict').upper()}")
        if result.get("approval_message"):
            print(f"  Messaggio: {result['approval_message'][:120]}")
        if result.get("rejection_reason"):
            print(f"  Rifiuto: {result['rejection_reason'][:120]}")
        if result.get("ancestor_hint"):
            print(f"  Antenato suggerito: {result['ancestor_hint']}")

asyncio.run(main())
