#!/bin/bash
# BKS Verse — Setup server Hetzner CX22 (Ubuntu 24.04)
# Esegui come root dopo la creazione del server.
# Costo: €4.51/mese. IP assegnato da Hetzner.

set -e

echo "=== BKS Verse — Server Setup ==="

# 1. Sistema base
apt-get update -qq && apt-get upgrade -y -qq
apt-get install -y python3.12 python3.12-venv python3-pip git curl ufw -qq

# 2. Firewall: apri solo 22 (SSH) e 8001 (Verse API)
ufw allow 22/tcp
ufw allow 8001/tcp
ufw --force enable

# 3. Utente non-root per il servizio
useradd -m -s /bin/bash bksverse 2>/dev/null || true

# 4. Crea directory app
mkdir -p /opt/bks-verse
chown bksverse:bksverse /opt/bks-verse

echo ""
echo "=== Trasferisci i file ==="
echo "Da Windows, esegui:"
echo "  scp -r 'I:/BAKABO SYSTEM/*' root@<IP_SERVER>:/opt/bks-verse/"
echo ""
read -p "Premi ENTER dopo aver trasferito i file..."

# 5. Setup Python venv
cd /opt/bks-verse
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "=== Configura .env ==="
if [ ! -f .env ]; then
    cp .env.template .env
    echo "Compila /opt/bks-verse/.env con le chiavi API."
    nano .env
fi

# 6. Init DB
.venv/bin/python scripts/init_db.py

# 7. Systemd service (avvio automatico)
cat > /etc/systemd/system/bks-verse.service << 'EOF'
[Unit]
Description=BKS Verse API
After=network.target

[Service]
User=bksverse
WorkingDirectory=/opt/bks-verse
ExecStart=/opt/bks-verse/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/bks-verse

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bks-verse
systemctl start bks-verse

sleep 2
systemctl status bks-verse --no-pager

echo ""
echo "=== Setup completato ==="
echo "Server API: http://$(curl -s ifconfig.me):8001/health"
echo ""
echo "Prossimi passi:"
echo "1. Punta verse.bakabo.club → $(curl -s ifconfig.me) via Cloudflare"
echo "2. Compila cloudflare/wrangler.toml con IP e zone_id"
echo "3. cd cloudflare && npx wrangler deploy"
