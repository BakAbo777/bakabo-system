# BKS VERSE — Architettura di Sistema v2
*Senza Make.com · Server Hetzner CX22 · Python puro*

---

## Diagramma generale

```text
                         ROBERTO (Windows locale)
                         I:\BAK ABO       I:\BAKABO SYSTEM
                         ┌────────────┐   ┌──────────────────────────┐
                         │ Motore BKS │   │  verse_engine/ (Python)  │
                         │ Printify   │   │  api/ (FastAPI)          │
                         │ Shopify    │   │  data/verse.db (SQLite)  │
                         │ Streamlit  │   │  scripts/admin_panel.py  │
                         └────────────┘   └──────────────────────────┘
                                                   │ deploy
                                                   ▼
              ┌────────────────────────────────────────────────────────┐
              │           HETZNER CX22  (€4.51/mese, sempre attivo)   │
              │  /opt/bks-verse/  →  uvicorn :8001                    │
              │                                                        │
              │  verse.bakabo.club ──► Cloudflare Worker ──► :8001    │
              └────────────────────────────────────────────────────────┘
                              │                     │
              ┌───────────────▼───┐    ┌────────────▼──────────────────┐
              │   SHOPIFY TM04    │    │  SERVIZI ESTERNI               │
              │  bakabo.club/verse│    │  OpenAI GPT-4o  (Giudice)     │
              │  bks-verse.js     │    │  OpenAI DALL-E 3 (artwork)    │
              │  bks-verse.css    │◄───│  GPTZero  (anti-spam)         │
              │  leaderboard page │    │  Printify (upload immagine)   │
              │  hall page        │    │  Discord  (notifiche)         │
              └───────────────────┘    │  Telegram (alert admin)       │
                                       │  Email    (member)            │
                                       │  HeyGen   (reel — opzionale) │
                                       └───────────────────────────────┘
```

---

## Flusso submission — step by step

```text
[Member su bakabo.club/verse]
    │  POST form (poem, collection, member_email)
    ▼
[bks-verse.js]
    │  fetch → verse.bakabo.club/verse/submit
    ▼
[Cloudflare Worker]          ← CORS, rate-limit 30 req/min/IP
    │  proxy → Hetzner :8001/verse/submit
    ▼
[FastAPI /verse/submit]
    │
    ├─[1] anti_spam.py
    │     ├─ validate_poem_text()    char 80-280, parole min 5
    │     └─ GPTZero API            human_score < 0.65 → soft-flag
    │
    ├─[2] giudice.py
    │     └─ OpenAI GPT-4o          5 assi × 5pt → score 1-25
    │        sistema prompt: spirito Pasolini
    │
    ├─[3] SQLite insert              verse_submissions
    │
    ├─[4] lineage.py  (se score≥20)
    │     └─ OpenAI GPT-4o          trova antenato poetico tra 21 storici
    │
    ├─[5] verse_hall insert          (se score=25)
    │
    └─[6] notifications.py
          ├─ Email member            approvato/rifiutato
          ├─ Discord #verse          (solo se approved/hall)
          └─ Telegram admin          (solo se approved/hall)

[Roberto riceve Telegram]
    │
    ▼
[01_ADMIN_PANEL.bat → localhost:8099]
    │
    ├─ "Genera artwork" → POST /verse/approve/{id}
    │     ├─ artwork.py → OpenAI DALL-E 3   genera immagine
    │     ├─ artwork.py → Printify API       upload PNG
    │     └─ artwork.py → Shopify Admin API  crea prodotto DRAFT
    │
    └─ "Pubblica" → POST /verse/publish/{id}
          └─ artwork.py → Shopify Admin API  status = active
             notifications.py → Discord + Telegram "LIVE!"
```

---

## Stack completo

| Layer           | Tecnologia           | Costo       |
|-----------------|----------------------|-------------|
| Server          | Hetzner CX22 Ubuntu  | €54/anno    |
| API framework   | FastAPI + uvicorn    | €0          |
| AI Judge        | OpenAI GPT-4o        | incluso API |
| AI Artwork      | OpenAI DALL-E 3      | incluso API |
| OpenAI totale   | ~500 call/m          | €180/anno   |
| Anti-spam       | GPTZero API          | €120/anno   |
| DB              | SQLite               | €0          |
| Edge proxy      | Cloudflare Worker    | €0          |
| Notifiche       | Discord + Telegram   | €0          |
| Email           | SMTP crew@bakabo     | €0          |
| Video reel      | HeyGen (opzionale)   | TBD         |
| Automazioni     | ~~Make.com~~  Python | -€276/anno  |
| **TOTALE**      |                      | **€354/anno**|

---

## Porte

| Servizio           | Porta | Dove          |
|--------------------|-------|---------------|
| BAK ABO Engine     | 8000  | locale Roberto|
| BKS Verse API      | 8001  | Hetzner       |
| Admin Panel        | 8099  | locale Roberto|
| Shopify            | 443   | cloud         |
| verse.bakabo.club  | 443   | Cloudflare    |

---

## Sicurezza

- Nessuna chiave API nel codice — tutte in `.env`
- Admin endpoints richiedono `X-Admin-Key` header
- Cloudflare Worker: CORS whitelist + rate-limit IP
- Server Hetzner: firewall UFW, solo porte 22 + 8001
- SQLite in `/opt/bks-verse/data/` — non esposto
- Shopify Admin API key mai nel frontend

---

## Struttura file

```
I:\BAKABO SYSTEM\
├── 00_START_VERSE.bat       avvia API locale (dev)
├── 01_ADMIN_PANEL.bat       pannello approvazione Roberto
├── .env.template            chiavi API (senza Make.com)
├── .markdownlint.json
├── requirements.txt
│
├── verse_engine/
│   ├── config.py            Pydantic settings
│   ├── giudice.py           Gran Giudice (OpenAI)
│   ├── lineage.py           Il Filo — antenato poetico
│   ├── submission.py        pipeline completa
│   ├── anti_spam.py         GPTZero + validazione
│   ├── artwork.py           DALL-E → Printify → Shopify draft
│   └── notifications.py     Discord + Telegram + Email
│
├── api/
│   ├── main.py              FastAPI app
│   └── routes/
│       ├── verse.py         submit / approve / publish / pending
│       ├── leaderboard.py   classifica globale
│       ├── lineage.py       mappa Il Filo
│       └── reel.py          storyboard + episodi TikTok
│
├── data/
│   ├── schema.sql           5 tabelle SQLite
│   └── poets.json           21 poeti storici scorati
│
├── shopify/
│   ├── sections/            3 sezioni liquid
│   ├── assets/              bks-verse.css + bks-verse.js
│   └── templates/           2 template JSON
│
├── cloudflare/
│   ├── worker.js            proxy CORS + rate-limit
│   └── wrangler.toml        config deploy
│
├── docs/
│   ├── architecture.md      questo file
│   ├── financial_model.md   P&L + costi
│   └── reel_format.md       guida produzione video
│
└── scripts/
    ├── init_db.py           crea DB + carica poeti
    ├── deploy_shopify.py    push assets → TM04
    ├── server_setup.sh      setup Hetzner (bash)
    ├── admin_panel.py       UI approvazione locale
    └── test_giudice.py      test scoring
```
