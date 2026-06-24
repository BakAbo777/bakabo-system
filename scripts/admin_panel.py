"""
BKS Verse Admin — pannello locale Roberto.
Avvia con: python scripts/admin_panel.py
Apre http://localhost:8099 con lista pending + pulsanti approvazione.
"""
import sqlite3
import httpx
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import os

DB   = Path(__file__).parent.parent / "data" / "verse.db"
PORT = 8099

# Legge secret dal .env locale
SECRET = ""
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith("VERSE_SECRET_KEY="):
            SECRET = line.split("=", 1)[1].strip()

VERSE_API = "http://localhost:8001"

HTML_BASE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>BKS Verse Admin</title>
<style>
body{background:#080604;color:#faf8f5;font-family:Georgia,serif;padding:32px;margin:0}
h1{color:#ffd700;letter-spacing:3px;font-size:22px;font-weight:400;margin-bottom:28px}
table{width:100%;border-collapse:collapse;margin-top:24px}
th{color:#c9b79c;font-size:11px;letter-spacing:2px;text-align:left;padding:8px 12px;
   border-bottom:1px solid #c9b79c33}
td{padding:10px 12px;border-bottom:1px solid #1a1510;vertical-align:top;font-size:13px}
.score{color:#ffd700;font-size:18px;font-weight:bold}
.poem{color:#faf8f5;max-width:260px;line-height:1.6;font-style:italic}
.btn{display:inline-block;padding:6px 14px;border:1px solid;cursor:pointer;
     font-size:11px;letter-spacing:1px;text-decoration:none;margin:2px}
.btn-approve{color:#ffd700;border-color:#ffd700}
.btn-publish{color:#4caf50;border-color:#4caf50}
.badge-hall{background:#ffd700;color:#080604;padding:2px 6px;font-size:10px}
.badge-approved{background:#c8942a;color:#fff;padding:2px 6px;font-size:10px}
.stats{display:flex;gap:0;border-top:1px solid #c9b79c22;border-bottom:1px solid #c9b79c22;
       padding:18px 0;margin-bottom:28px;flex-wrap:wrap}
.stat{flex:1 1 120px;padding:0 24px;border-right:1px solid #c9b79c18}
.stat:first-child{padding-left:0}
.stat:last-child{border-right:none}
.stat-num{display:block;font-size:28px;font-style:italic;color:#c9b79c;line-height:1.1;margin-bottom:4px}
.stat-lbl{display:block;font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:#faf8f555}
.stat-num.gold{color:#ffd700}
.stat-num.green{color:#4caf50}
.stat-num.red{color:#ff6b6b}
.queue-title{color:#c9b79c;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px}
</style>
</head>
<body>
<h1>BKS VERSE — Admin</h1>
{body}
</body>
</html>"""


class AdminHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silenzia log HTTP

    def do_GET(self):
        if self.path == "/":
            self.render_dashboard()
        else:
            self.send_error(404)

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)
        params  = dict(p.split("=") for p in body.decode().split("&") if "=" in p)
        action  = params.get("action")
        sub_id  = params.get("id")

        if action in ("approve", "publish") and sub_id:
            endpoint = f"{VERSE_API}/verse/{action}/{sub_id}"
            try:
                r = httpx.post(endpoint, headers={"X-Admin-Key": SECRET}, timeout=60)
                msg = f"OK: {action} #{sub_id}" if r.status_code == 200 else f"ERR: {r.text[:80]}"
            except Exception as e:
                msg = f"ERR: {e}"
        else:
            msg = "Azione non valida"

        self.send_response(303)
        self.send_header("Location", f"/?msg={msg}")
        self.end_headers()

    def render_dashboard(self):
        from urllib.parse import urlparse, parse_qs
        qs  = parse_qs(urlparse(self.path).query)
        msg = qs.get("msg", [""])[0]

        try:
            conn = sqlite3.connect(str(DB))
            conn.row_factory = sqlite3.Row

            # ── Stats ──────────────────────────────────────────────────────────
            status_counts = {r["status"]: r["cnt"] for r in conn.execute(
                "SELECT status, COUNT(*) as cnt FROM verse_submissions GROUP BY status"
            ).fetchall()}
            total_sub   = sum(status_counts.values())
            n_approved  = status_counts.get("approved", 0)
            n_hall      = status_counts.get("hall", 0)
            n_rejected  = status_counts.get("rejected", 0)
            n_pending   = status_counts.get("pending", 0)
            n_poets     = conn.execute("SELECT COUNT(*) FROM poet_archive").fetchone()[0]
            last_row    = conn.execute(
                "SELECT submitted_at FROM verse_submissions ORDER BY submitted_at DESC LIMIT 1"
            ).fetchone()
            last_sub    = last_row["submitted_at"][:10] if last_row else "—"

            avg_row = conn.execute(
                "SELECT AVG(score_total) FROM verse_submissions WHERE verdict != 'rejected'"
            ).fetchone()
            avg_score = f"{avg_row[0]:.1f}" if avg_row[0] else "—"

            stats_html = f"""
            <div class="stats">
              <div class="stat">
                <span class="stat-num">{total_sub}</span>
                <span class="stat-lbl">submission totali</span>
              </div>
              <div class="stat">
                <span class="stat-num green">{n_approved + n_hall}</span>
                <span class="stat-lbl">approvate</span>
              </div>
              <div class="stat">
                <span class="stat-num gold">{n_hall}</span>
                <span class="stat-lbl">hall of fame</span>
              </div>
              <div class="stat">
                <span class="stat-num red">{n_rejected}</span>
                <span class="stat-lbl">rifiutate</span>
              </div>
              <div class="stat">
                <span class="stat-num">{n_pending}</span>
                <span class="stat-lbl">in attesa</span>
              </div>
              <div class="stat">
                <span class="stat-num">{n_poets}</span>
                <span class="stat-lbl">poeti archivio</span>
              </div>
              <div class="stat">
                <span class="stat-num">{avg_score}</span>
                <span class="stat-lbl">score medio</span>
              </div>
              <div class="stat">
                <span class="stat-num" style="font-size:14px;padding-top:6px">{last_sub}</span>
                <span class="stat-lbl">ultima submission</span>
              </div>
            </div>"""

            # ── Queue ──────────────────────────────────────────────────────────
            rows = conn.execute("""
                SELECT s.id, s.member_email, s.score_total, s.poem_text,
                       s.status, s.giudice_verdict, s.submitted_at,
                       s.product_created, s.product_id,
                       p.name as ancestor
                FROM verse_submissions s
                LEFT JOIN poet_archive p ON p.id = s.ancestor_poet_id
                WHERE s.status IN ('approved','hall')
                ORDER BY s.score_total DESC, s.submitted_at ASC
            """).fetchall()
            conn.close()

            if not rows:
                queue_html = "<p style='color:#c9b79c;font-size:13px;'>Nessuna submission approvata in attesa.</p>"
            else:
                trs = ""
                for r in rows:
                    badge = '<span class="badge-hall">25/25 HALL</span>' if r["score_total"] == 25 \
                            else '<span class="badge-approved">APPROVED</span>'
                    btn_approve = "" if r["product_created"] else \
                        f'<form method="post"><input type="hidden" name="action" value="approve">' \
                        f'<input type="hidden" name="id" value="{r["id"]}">' \
                        f'<button class="btn btn-approve">Genera artwork</button></form>'
                    btn_publish = f'<form method="post"><input type="hidden" name="action" value="publish">' \
                        f'<input type="hidden" name="id" value="{r["id"]}">' \
                        f'<button class="btn btn-publish">Pubblica</button></form>' \
                        if r["product_created"] else ""
                    trs += f"""<tr>
                        <td>#{r['id']}<br><small>{r['submitted_at'][:10]}</small></td>
                        <td class="score">{r['score_total']}/25<br>{badge}</td>
                        <td class="poem">{r['poem_text'][:120]}...</td>
                        <td>{r['ancestor'] or '—'}</td>
                        <td>{r['member_email']}</td>
                        <td>{btn_approve}{btn_publish}</td>
                    </tr>"""
                queue_html = f"""
                <table>
                  <tr>
                    <th>#</th><th>Score</th><th>Poesia</th>
                    <th>Antenato</th><th>Member</th><th>Azioni</th>
                  </tr>
                  {trs}
                </table>"""

            body = f"""
            {f'<p style="color:#ffd700;margin-bottom:16px;">{msg}</p>' if msg else ''}
            {stats_html}
            <p class="queue-title">Coda approvazione</p>
            {queue_html}"""

        except Exception as e:
            body = f"<p style='color:#ff6b6b;'>Errore DB: {e}</p>"

        html = HTML_BASE.replace('{body}', body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(html))
        self.end_headers()
        self.wfile.write(html)


if __name__ == "__main__":
    print(f"\nBKS Verse Admin → http://localhost:{PORT}")
    print("Ctrl+C per uscire\n")
    httpx.get(f"{VERSE_API}/health", timeout=3)  # verifica API attiva
    srv = HTTPServer(("127.0.0.1", PORT), AdminHandler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nAdmin panel chiuso.")
