"""Notifiche: Discord, Telegram, Email per ogni evento BKS Verse."""
import httpx
import aiosmtplib
from email.message import EmailMessage
from .config import settings


async def notify_discord(webhook_url: str, message: str, title: str = "", color: int = 0xFFD700) -> bool:
    if not webhook_url:
        return False
    payload = {
        "embeds": [{
            "title": title or "BKS Verse",
            "description": message,
            "color": color,
            "footer": {"text": "bakabo.club/verse"},
        }]
    }
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.post(webhook_url, json=payload)
        return r.status_code == 204


async def notify_telegram(message: str) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_admin_chat_id:
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.post(url, json={
            "chat_id": settings.telegram_admin_chat_id,
            "text": message,
            "parse_mode": "Markdown",
        })
        return r.status_code == 200


async def send_email(to: str, subject: str, body_html: str) -> bool:
    if not settings.smtp_password:
        return False
    msg = EmailMessage()
    msg["From"] = settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("Apri in un client che supporta HTML.")
    msg.add_alternative(body_html, subtype="html")
    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        return True
    except Exception:
        return False


# ── Template email ───────────────────────────────────────────────────────────

def email_approved(member_email: str, score: int, poem_excerpt: str, ancestor_name: str = "") -> str:
    ancestor_line = f"<p>Il Giudice ha trovato un'affinità con <strong>{ancestor_name}</strong>.</p>" if ancestor_name else ""
    return f"""
<div style="background:#080604;color:#faf8f5;font-family:Georgia,serif;padding:40px;max-width:600px;">
  <h1 style="color:#ffd700;font-size:22px;letter-spacing:2px;">IL GIUDICE HA PARLATO</h1>
  <p style="color:#c9b79c;font-size:13px;">Punteggio: <strong style="color:#ffd700;font-size:20px;">{score}/25</strong></p>
  <blockquote style="border-left:2px solid #ffd700;margin:20px 0;padding:10px 20px;
    color:#faf8f5;font-style:italic;">{poem_excerpt}</blockquote>
  {ancestor_line}
  <p>Il tuo verso è stato approvato per la collezione BKS Verse.<br>
  Sarà trasformato in un oggetto nei prossimi giorni.</p>
  <a href="https://bakabo.club/verse" style="color:#ffd700;">→ bakabo.club/verse</a>
</div>"""


def email_rejected(member_email: str, score: int, reason: str) -> str:
    return f"""
<div style="background:#080604;color:#faf8f5;font-family:Georgia,serif;padding:40px;max-width:600px;">
  <h1 style="color:#c9b79c;font-size:22px;letter-spacing:2px;">IL GIUDICE HA PARLATO</h1>
  <p style="color:#c9b79c;font-size:13px;">Punteggio: <strong>{score}/25</strong>
    (soglia: {settings.verse_gate_score}/25)</p>
  <p style="color:#c9b79c;">{reason}</p>
  <p>Puoi ripresentare tra 7 giorni.<br>Studia il profilo degli assi e riprova.</p>
  <a href="https://bakabo.club/verse" style="color:#ffd700;">→ bakabo.club/verse</a>
</div>"""


def email_hall_of_fame(member_email: str, poem_excerpt: str, ancestor_name: str) -> str:
    return f"""
<div style="background:#080604;color:#faf8f5;font-family:Georgia,serif;padding:40px;max-width:600px;">
  <h1 style="color:#ffd700;font-size:26px;letter-spacing:3px;">25 / 25</h1>
  <p style="color:#ffd700;">Nella storia umana, meno di venti poeti ci sono arrivati.</p>
  <blockquote style="border-left:3px solid #ffd700;margin:20px 0;padding:10px 20px;
    color:#faf8f5;font-style:italic;font-size:18px;">{poem_excerpt}</blockquote>
  <p>Il tuo verso entra nella <strong>BKS Verse Hall</strong>.<br>
  {ancestor_name} avrebbe riconosciuto questo lavoro.</p>
  <a href="https://bakabo.club/verse/hall" style="color:#ffd700;">→ Hall of Fame</a>
</div>"""


async def dispatch_verdict(submission_id: int, member_email: str, verdict: str,
                           score: int, poem_excerpt: str,
                           ancestor_name: str = "", rejection_reason: str = "") -> None:
    """Dispatch completo: Discord + Telegram + Email."""
    if verdict == "hall":
        subject = "25/25 — BKS Verse Hall of Fame"
        html = email_hall_of_fame(member_email, poem_excerpt, ancestor_name)
        discord_msg = f"**25/25 — HALL OF FAME**\n{poem_excerpt[:100]}..."
        discord_color = 0xFFD700
    elif verdict == "approved":
        subject = f"Poesia approvata {score}/25 — BKS Verse"
        html = email_approved(member_email, score, poem_excerpt, ancestor_name)
        discord_msg = f"**Nuovo verso approvato** — {score}/25\n{poem_excerpt[:80]}..."
        discord_color = 0xC8942A
    else:
        subject = f"Esito valutazione {score}/25 — BKS Verse"
        html = email_rejected(member_email, score, rejection_reason)
        discord_msg = f"Verso non approvato — {score}/25 (#{submission_id})"
        discord_color = 0x3D2018

    await send_email(member_email, subject, html)

    if verdict != "rejected":
        await notify_discord(settings.discord_webhook_verse, discord_msg,
                             title="BKS Verse", color=discord_color)
        await notify_telegram(f"BKS Verse #{submission_id} — {verdict.upper()} {score}/25")
