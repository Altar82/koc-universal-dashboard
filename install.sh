#!/bin/bash
# KOC Universal Dashboard - Pro Installer (Fixed Build Context)

echo "------------------------------------------"
echo "  KOC UNIVERSAL DASHBOARD INSTALLER      "
echo "------------------------------------------"

# 1. Rilevamento automatico (Zero-Config)
echo "🔍 Analisi dell'infrastruttura KOC..."

# Trova i container reali di Postgres, Redis e Proxy
DB_CONTAINER=$(docker ps --filter "name=postgres" --filter "name=db" --format "{{.Names}}" | head -n 1)
REDIS_CONTAINER=$(docker ps --filter "name=redis" --format "{{.Names}}" | head -n 1)
PROXY_CONTAINER=$(docker ps --filter "name=koc-proxy" --format "{{.Names}}" | head -n 1)

if [ -z "$DB_CONTAINER" ] || [ -z "$REDIS_CONTAINER" ]; then
    echo "❌ Errore: Container Postgres o Redis non trovati."
    exit 1
fi

# Estrae variabili dal Proxy (se disponibile)
if [ -n "$PROXY_CONTAINER" ]; then
    FINAL_SERVER_NAME=$(docker exec $PROXY_CONTAINER printenv SERVER_NAME)
    FINAL_MAX_PLAYERS=$(docker exec $PROXY_CONTAINER printenv MAX_PLAYERS)
fi

# Fallback se le variabili proxy sono vuote
FINAL_SERVER_NAME=${FINAL_SERVER_NAME:-"KOC Server"}
FINAL_MAX_PLAYERS=${FINAL_MAX_PLAYERS:-"100"}

# Estrae rete e credenziali dal container attivo
NETWORK_NAME=$(docker inspect $DB_CONTAINER -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')
DB_USER=$(docker exec $DB_CONTAINER printenv POSTGRES_USER || echo "postgres")
DB_PASS=$(docker exec $DB_CONTAINER printenv POSTGRES_PASSWORD || echo "postgres")
DB_NAME=$(docker exec $DB_CONTAINER printenv POSTGRES_DB || echo "koc")

echo "✅ Rete: $NETWORK_NAME | DB: $DB_CONTAINER"
echo "✅ Proxy: $PROXY_CONTAINER (Server: $FINAL_SERVER_NAME)"

# 2. Setup Directory
REPO_DIR="koc-universal-dashboard"
if [ ! -d "$REPO_DIR" ]; then
    git clone https://github.com/Altar82/koc-universal-dashboard.git
fi
cd "$REPO_DIR" || exit
git pull

# 3. Generazione Docker Compose (Uniformato su 'dashboard')
echo "⚙️ Generazione file di configurazione..."
cat <<EOF > docker-compose.yml
services:
  dashboard:
    build: .
    container_name: koc-dashboard
    ports:
      - "8501:8501"
    environment:
      - DATABASE_URL=postgres://$DB_USER:$DB_PASS@$DB_CONTAINER:5432/$DB_NAME
      - REDIS_HOST=$REDIS_CONTAINER
      - SERVER_NAME=$FINAL_SERVER_NAME
      - MAX_PLAYERS=$FINAL_MAX_PLAYERS
    networks:
      - kocinfrastructure
    restart: always

networks:
  kocinfrastructure:
    external: true
    name: $NETWORK_NAME
EOF

# Rimuoviamo l'override se esiste per evitare conflitti di nomi vecchi
rm -f docker-compose.override.yml

# 4. Build e Avvio forzato
echo "🏗 Avvio build della dashboard..."
docker compose up -d --build

# 5. Output
IP_ADDR=$(curl -4 -s https://ifconfig.me)
echo "------------------------------------------"
echo "✅ INSTALLAZIONE COMPLETATA!"
echo "🌐 URL: http://$IP_ADDR:8501"
echo "📊 Config: $FINAL_SERVER_NAME ($FINAL_MAX_PLAYERS players)"
echo "------------------------------------------"
