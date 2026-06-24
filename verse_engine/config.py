from pydantic_settings import BaseSettings
from pathlib import Path

ROOT = Path(__file__).parent.parent

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o"

    # Shopify
    shopify_store: str = "bakabo.club"                         # dominio pubblico
    shopify_myshopify_domain: str = "11628e-2.myshopify.com"  # usato per Admin API
    shopify_admin_token: str = ""
    shopify_api_version: str = "2025-01"
    shopify_brass_metafield_key: str = "member_tier"

    # Printify (Shop ID fisso — NON modificare)
    printify_api_token: str = ""
    printify_shop_id: str = "12030061"

    # Cloudflare (proxy pubblico → server privato)
    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    cloudflare_worker_name: str = "bks-verse-worker"

    # Discord
    discord_webhook_verse: str = ""
    discord_webhook_giudice: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""

    # HeyGen (Il Filo video — opzionale)
    heygen_api_key: str = ""
    heygen_avatar_giudice_id: str = ""

    # GPTZero
    gptzero_api_key: str = ""
    gptzero_min_human_score: float = 0.65

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = "crew@bakabo.club"
    smtp_password: str = ""

    # Database
    verse_db_path: str = "./data/verse.db"

    # App
    verse_api_port: int = 8001
    verse_api_host: str = "0.0.0.0"
    verse_secret_key: str = "change-this-in-production"
    verse_min_chars: int = 80
    verse_max_chars: int = 280
    verse_gate_score: int = 20
    verse_hall_of_fame_score: int = 25

    # Hosting server (Hetzner CX22 — cambio IP dopo deploy)
    verse_public_url: str = "https://verse.bakabo.club"

    # Bridge BAK ABO
    bakabo_engine_url: str = "http://localhost:8000"

    class Config:
        env_file = ROOT / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
