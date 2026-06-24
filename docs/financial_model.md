# BKS VERSE — Modello Finanziario v2
*Aggiornato: senza Make.com · con server Hetzner sempre attivo*

---

## Costi fissi di sistema / anno

| Voce                                   | Dettaglio                              | €/mese | €/anno |
|----------------------------------------|----------------------------------------|--------|--------|
| **Server Hetzner CX22**                | 2 vCPU · 4GB RAM · 40GB SSD · Ubuntu  | €4.51  | **€54**    |
| **Cloudflare** (proxy + DNS + tunnel)  | Free tier o Pro €20/m per sicurezza    | €0–20  | **€0–240** |
| **OpenAI API**                         | Giudice ~500 call/m + DALL-E ~20 img/m | €15    | **€180**   |
| **GPTZero API**                        | 1.000 check/mese (piano Developer)     | €10    | **€120**   |
| **Discord**                            | Gratuito                               | €0     | **€0**     |
| **Telegram Bot**                       | Gratuito                               | €0     | **€0**     |
| **Dominio verse.bakabo.club**          | già incluso in bakabo.club             | €0     | **€0**     |
| **Make.com**                           | ELIMINATO — sostituito con Python      | ~~€23~~ | ~~**€276**~~ |
| **TOTALE FISSI (scenario base)**       |                                        | **€29.51** | **€354** |
| **TOTALE FISSI (con Cloudflare Pro)**  |                                        | **€49.51** | **€594** |

**Risparmio vs sistema con Make.com: €402/anno** (eliminato Make, aggiunto server).

---

## Confronto architettura: Make.com vs Python diretto

| Funzione               | Make.com (prima)      | Python diretto (ora)    | Vantaggio                |
|------------------------|-----------------------|-------------------------|--------------------------|
| Poem Judge trigger     | Scenario 1 (webhook)  | `giudice.py` (diretto)  | Velocità ×3              |
| Artwork generation     | Scenario 2 (DALL-E)   | `artwork.py` (diretto)  | Nessun intermediario     |
| Printify upload        | Scenario 2            | `artwork.py` (diretto)  | Nessun intermediario     |
| Shopify draft creation | Scenario 2            | `artwork.py` (diretto)  | Nessun intermediario     |
| Drop launch notify     | Scenario 3            | `notifications.py`      | Discord+TG già integrati |
| Google Sheets tracking | Scenario 3            | SQLite verse.db         | Più affidabile, offline  |
| **Costo**              | **€276/anno**         | **€0**                  | -€276                    |
| **Dipendenza**         | Alta (black box)      | Nessuna (Python proprio)| Controllo totale         |
| **Debug**              | Difficile             | Codice leggibile        | Trasparenza              |

---

## Costi variabili per prodotto Verse

| Voce                              | Standard (20-22) | Premium (23-24) | Hall (25/25) |
|-----------------------------------|-----------------|-----------------|--------------|
| Tempo Roberto (review/approv.)    | €10             | €15             | €20          |
| OpenAI DALL-E 3 (artwork)         | €0.08           | €0.08           | €0.08        |
| Printify produzione capo          | €18–28          | €22–32          | €22–32       |
| Shopify transaction fee (Basic)   | €1.40–2.00      | €2.00–2.50      | €3.50        |
| Spedizione (a carico cliente)     | €0              | €0              | €0           |
| **Totale costo per prodotto**     | **€30–42**      | **€39–51**      | **€46–57**   |

### Pricing consigliato

| Tier         | Score     | Prezzo vendita | Margine netto medio |
|--------------|-----------|----------------|----------------------|
| Standard     | 20–22/25  | €79            | €37–49               |
| Premium      | 23–24/25  | €119           | €68–80               |
| Hall (ed.num)| 25/25     | €199           | €142–153             |

---

## Proiezioni Year 1

### Ipotesi conservative

| Parametro                            | Minimo | Realistico | Ottimista |
|--------------------------------------|--------|------------|-----------|
| Members Brass+ attivi                | 50     | 150        | 400       |
| % che sottomettono almeno 1 poesia   | 15%    | 25%        | 40%       |
| Submission totali/anno               | 8      | 38         | 160       |
| Approval rate (≥20/25)               | 15%    | 20%        | 25%       |
| Prodotti draft creati                | 1      | 8          | 40        |
| Prodotti venduti (conv. 50%)         | 1      | 4          | 20        |
| Prezzo medio                         | €79    | €94        | €99       |

### P&L Year 1

| Voce                          | Minimo    | Realistico | Ottimista  |
|-------------------------------|-----------|------------|------------|
| Ricavi prodotti Verse          | €79       | €376       | €1.980     |
| Costi variabili prodotti       | €36       | €160       | €840       |
| **Margine lordo prodotti**    | **€43**   | **€216**   | **€1.140** |
| Costi fissi sistema/anno       | €354      | €354       | €594       |
| **Utile / Perdita Verse**     | **-€311** | **-€138**  | **+€546**  |

### Break-even

Con pricing medio €94: **servono ~10 prodotti venduti/anno per il break-even** (meno di 1 al mese).

---

## Il valore non è nel P&L di Verse

Il costo netto nel scenario realistico è **€138/anno** (€11.50/mese).

In cambio:

- **Content engine infinito**: ogni poesia approvata = 1 reel "Il Filo" = contenuto organico
- **Member retention**: i member che partecipano acquistano il 3× in più
- **Differenziazione**: nessun brand fashion al mondo ha questo
- **SEO + PR**: la classifica mondiale con poeti storici genera link spontanei
- **TikTok acquisition**: "Il Giudice Esamina Leopardi" = reach potenziale 100K+

**€138/anno è il costo di un'ora di consulenza di marketing**, e Verse produce contenuti per 365 giorni.

---

## Roadmap costi

| Fase        | Quando         | Costo aggiuntivo | Note                              |
|-------------|----------------|------------------|-----------------------------------|
| **Lancio**  | Subito         | €354/anno        | Server + API                      |
| **Crescita**| +100 member    | +€120/anno       | GPTZero piano Pro                 |
| **Scale**   | +500 member    | +€300/anno       | Server upgrade CX32 (€12/m)       |
| **Poet Sub**| Year 2         | €0               | Ricavi abbonamento coprono tutto  |

---

## Setup server (istruzioni operative)

```bash
# 1. Crea server su hetzner.com (CX22, Ubuntu 24.04, Frankfurt)
# 2. SSH e installa Python 3.12 + pip
# 3. Clone o trasferisci I:\BAKABO SYSTEM\ sul server
# 4. Crea .env dal template
# 5. python scripts/init_db.py
# 6. uvicorn api.main:app --host 0.0.0.0 --port 8001

# Configurazione dominio:
# verse.bakabo.club → CNAME → IP Hetzner (via Cloudflare)
# Cloudflare: SSL/TLS Full, cache bypass per /verse/*
```

**Costo setup unico: 30 minuti**. Zero vendor lock-in.
