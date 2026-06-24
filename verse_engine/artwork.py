"""
Artwork Generator — sostituisce Make.com Scenario 2.
Pipeline: poem → prompt DALL-E 3 → immagine → Printify upload → Shopify draft.
Tutto in Python diretto, nessun intermediario.
"""
import httpx
import base64
import json
from openai import AsyncOpenAI
from .config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

PROMPT_SYSTEM = """Sei un art director BKS. Trasformi una poesia in un prompt per DALL-E 3.
Il risultato deve essere un'immagine adatta a diventare un pattern tessile o stampa su capo.

Regole assolute:
- Nessun testo nell'immagine (zero parole, zero lettere)
- Palette: dominanza di nero (#080604), accenti oro o bianco
- Stile: grafico, geometrico, astrazione controllata — NON fotorealismo
- Formato: composizione che si ripete bene su tessuto (pattern-friendly)
- Mood: coerente con l'estetica BKS — oscurità elegante, tensione visiva

Rispondi con UN SOLO prompt in inglese, max 200 parole, pronto per DALL-E 3.
Solo il prompt, nessun altro testo."""


async def poem_to_prompt(poem_text: str, collection_slug: str = None, giudice_notes: dict = None) -> str:
    """Genera il prompt DALL-E 3 dalla poesia tramite GPT-4o."""
    context = f"Poesia:\n{poem_text}"
    if collection_slug:
        context += f"\n\nCollezione BKS: {collection_slug}"
    if giudice_notes:
        # Usa le note del Giudice per arricchire il prompt visivo
        image_note = giudice_notes.get("image", "")
        bks_note   = giudice_notes.get("bks_resonance", "")
        if image_note:
            context += f"\n\nForza visiva identificata dal Giudice: {image_note}"
        if bks_note:
            context += f"\nRisonanza BKS: {bks_note}"

    resp = await client.chat.completions.create(
        model=settings.openai_default_model,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": context},
        ],
        temperature=0.7,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


async def generate_artwork(poem_text: str, collection_slug: str = None,
                            giudice_notes: dict = None) -> dict:
    """Genera l'immagine con DALL-E 3. Ritorna URL + b64."""
    dalle_prompt = await poem_to_prompt(poem_text, collection_slug, giudice_notes)

    resp = await client.images.generate(
        model="dall-e-3",
        prompt=dalle_prompt,
        size="1024x1024",
        quality="hd",
        style="vivid",
        response_format="b64_json",
        n=1,
    )

    image_data = resp.data[0]
    return {
        "b64": image_data.b64_json,
        "revised_prompt": image_data.revised_prompt,
        "original_prompt": dalle_prompt,
    }


async def upload_to_printify(b64_image: str, title: str) -> str:
    """Carica immagine su Printify. Ritorna image_id."""
    if not settings.printify_api_token:
        raise ValueError("PRINTIFY_API_TOKEN non configurata")

    image_bytes = base64.b64decode(b64_image)
    filename = f"bks-verse-{title[:30].replace(' ', '-').lower()}.png"

    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            "https://api.printify.com/v1/uploads/images.json",
            headers={
                "Authorization": f"Bearer {settings.printify_api_token}",
                "Content-Type": "application/json",
            },
            json={
                "file_name": filename,
                "contents": b64_image,
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def create_shopify_draft(
    title: str,
    poem_text: str,
    score: int,
    ancestor_poet: str,
    collection_slug: str,
    image_url: str = None,
) -> dict:
    """Crea prodotto draft su Shopify (non pubblicato — Roberto approva prima)."""
    if not settings.shopify_admin_token:
        raise ValueError("SHOPIFY_ADMIN_TOKEN non configurata")

    body_html = f"""<div class="bks-verse-product">
  <blockquote class="bks-verse-poem">{poem_text}</blockquote>
  <p class="bks-verse-meta">
    Punteggio Giudice: {score}/25 · Filo: {ancestor_poet} · Collezione: {collection_slug}
  </p>
</div>"""

    product_payload = {
        "product": {
            "title": title,
            "body_html": body_html,
            "vendor": "BKS Studio",
            "product_type": "Verse",
            "tags": [
                "bks-verse", collection_slug or "bks-verse",
                f"score-{score}", "limited-edition"
            ],
            "status": "draft",
            "variants": [{"price": "89.00", "requires_shipping": True}],
        }
    }

    if image_url:
        product_payload["product"]["images"] = [{"src": image_url}]

    async with httpx.AsyncClient(timeout=20) as http:
        resp = await http.post(
            f"https://{settings.shopify_myshopify_domain}/admin/api/{settings.shopify_api_version}/products.json",
            headers={
                "X-Shopify-Access-Token": settings.shopify_admin_token,
                "Content-Type": "application/json",
            },
            json=product_payload,
        )
        resp.raise_for_status()
        return resp.json()["product"]


async def publish_product(product_id: str) -> bool:
    """Roberto approva → pubblica il prodotto (endpoint /verse/publish)."""
    async with httpx.AsyncClient(timeout=20) as http:
        resp = await http.put(
            f"https://{settings.shopify_myshopify_domain}/admin/api/{settings.shopify_api_version}/products/{product_id}.json",
            headers={
                "X-Shopify-Access-Token": settings.shopify_admin_token,
                "Content-Type": "application/json",
            },
            json={"product": {"id": product_id, "status": "active"}},
        )
        return resp.status_code == 200


async def full_artwork_pipeline(
    submission_id: int,
    poem_text: str,
    score: int,
    collection_slug: str,
    ancestor_poet: str,
    giudice_notes: dict = None,
) -> dict:
    """
    Pipeline completa (sostituisce Make.com Scenario 2 + 3):
    1. poem → DALL-E 3 prompt → immagine
    2. immagine → Printify upload
    3. → Shopify draft product
    Ritorna: product_id, image_url, prompt usato
    """
    # 1. Genera artwork
    artwork = await generate_artwork(poem_text, collection_slug, giudice_notes)

    # 2. Upload Printify (opzionale — se chiave disponibile)
    printify_image_id = None
    if settings.printify_api_token:
        printify_image_id = await upload_to_printify(artwork["b64"], f"verse-{submission_id}")

    # 3. Draft Shopify
    title = f"BKS Verse #{submission_id} — {score}/25"
    product = await create_shopify_draft(
        title=title,
        poem_text=poem_text,
        score=score,
        ancestor_poet=ancestor_poet,
        collection_slug=collection_slug or "bks-verse",
    )

    return {
        "submission_id": submission_id,
        "product_id": str(product["id"]),
        "product_url": f"https://{settings.shopify_store}/admin/products/{product['id']}",
        "artwork_prompt": artwork["original_prompt"],
        "revised_prompt": artwork.get("revised_prompt"),
        "printify_image_id": printify_image_id,
        "status": "draft_created",
    }
