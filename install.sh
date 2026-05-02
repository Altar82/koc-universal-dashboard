#!/bin/bash
# KOC Universal Dashboard - Smart Installer by Altar82

echo "------------------------------------------"
echo "  KOC UNIVERSAL DASHBOARD INSTALLER      "
echo "------------------------------------------"

# 0. Permessi di Root
if [ "$EUID" -ne 0 ]; then 
  echo "❌ Error: Please run with sudo: curl -sSL ... | sudo bash"
  exit 1
fi

# 1. Trova il container del Database per rubare la rete
echo "🔍 Detecting existing KOC network..."
CONTAINER_ID=$(docker ps --filter "name=postgres" --filter "name=db" --format "{{.ID}}" | head -n 1)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Error: Database container not found. Is your server running?"
    exit 1
fi

NETWORK_NAME=$(docker inspect $CONTAINER_ID -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')
echo "✅ Network found: $NETWORK_NAME"

#!/bin/bash
# KOC Universal Dashboard - Pro Installer (Zero-Config)

echo "------------------------------------------"
echo "  KOC UNIVERSAL DASHBOARD INSTALLER      "
echo "------------------------------------------"

# 1. Rilevamento automatico dai container in esecuzione
echo "🔍 Analisi dell'infrastruttura KOC in corso..."

# Trova i nomi esatti dei container DB e Redis
DB_CONTAINER=$(docker ps --filter "name=postgres" --filter "name=db" --format "{{.Names}}" | head -n 1)
REDIS_CONTAINER=$(docker ps --filter "name=redis" --format "{{.Names}}" | head -n 1)

if [ -z "$DB_CONTAINER" ] || [ -z "$REDIS_CONTAINER" ]; then
    echo "❌ Errore: Non trovo i container di Postgres o Redis."
    echo "Assicurati che il tuo server KOC sia avviato."
    exit 1
fi

# Estrae la rete esistente
NETWORK_NAME=$(docker inspect $DB_CONTAINER -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')

# Estrae le credenziali reali dal container DB (senza indovinare)
DB_USER=$(docker exec $DB_CONTAINER printenv POSTGRES_USER)
DB_PASS=$(docker exec $DB_CONTAINER printenv POSTGRES_PASSWORD)
DB_NAME=$(docker exec $DB_CONTAINER printenv POSTGRES_DB)

# Fallback di sicurezza se non settate esplicitamente
DB_USER=${DB_USER:-postgres}
DB_PASS=${DB_PASS:-postgres}
DB_NAME=${DB_NAME:-koc}

echo "✅ Rete rilevata: $NETWORK_NAME"
echo "✅ Database: $DB_CONTAINER (User: $DB_USER)"
echo "✅ Redis: $REDIS_CONTAINER"

# 2. Setup Directory
REPO_DIR="koc-universal-dashboard"
if [ ! -d "$REPO_DIR" ]; then
    git clone https://github.com/Altar82/koc-universal-dashboard.git
fi
cd "$REPO_DIR" || exit
git pull

# 3. Creazione del Compose pulito per la dashboard
# Usiamo i nomi dei container come Host per sfruttare il DNS interno di Docker
echo "⚙️ Generazione docker-compose.yml personalizzato..."
cat <<EOF > docker-compose.yml
services:
  koc-dashboard:
    build: .
    container_name: koc-dashboard
    ports:
      - "8501:8501"
    environment:
      - DATABASE_URL=postgres://$DB_USER:$DB_PASS@$DB_CONTAINER:5432/$DB_NAME
      - REDIS_HOST=$REDIS_CONTAINER
    networks:
      - kocinfrastructure
    restart: always

networks:
  kocinfrastructure:
    external: true
    name: $NETWORK_NAME
EOF

# 4. Build e Avvio
echo "🏗 Avvio della dashboard..."
docker compose up -d --build

# 5. Fine
IP_ADDR=$(curl -4 -s https://ifconfig.me)
echo "------------------------------------------"
echo "✅ INSTALLAZIONE COMPLETATA CON SUCCESSO"
echo "🌐 Accedi qui: http://$IP_ADDR:8501"
echo "------------------------------------------"
