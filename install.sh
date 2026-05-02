#!/bin/bash
# KOC Universal Dashboard - Installer by Altar82

echo "------------------------------------------"
echo "  KOC UNIVERSAL DASHBOARD INSTALLER      "
echo "------------------------------------------"

# 0. Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "❌ Error: Please run the installer with sudo:"
  echo "curl -sSL https://raw.githubusercontent.com/Altar82/koc-universal-dashboard/main/install.sh | sudo bash"
  exit 1
fi

# 1. Network Discovery Logic
echo "🔍 Detecting Docker network..."
# Cerca il container del database (postgres o db)
CONTAINER_ID=$(docker ps --filter "name=postgres" --filter "name=db" --format "{{.ID}}" | head -n 1)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Error: Database container (postgres/db) not found."
    echo "Make sure your KOC server is running before installing the dashboard."
    exit 1
fi

# Ottiene il nome della rete reale a cui è collegato il DB[cite: 3]
NETWORK_NAME=$(docker inspect $CONTAINER_ID -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')
echo "✅ Network detected: $NETWORK_NAME"

# 2. Setup Directory
echo "📁 Preparing local files..."
REPO_DIR="koc-universal-dashboard"

if [ -d "$REPO_DIR" ]; then
    echo "🔄 Updating existing repository..."
    cd $REPO_DIR
    git pull
else
    echo "📥 Cloning repository from Altar82..."
    git clone https://github.com/Altar82/koc-universal-dashboard.git
    cd $REPO_DIR
fi

# 3. Create Dynamic Override
# Questo collega la dashboard alla rete esistente del tuo server
echo "⚙️ Configuring network bridge..."
cat <<EOF > docker-compose.override.yml
services:
  dashboard:
    networks:
      - kocinfrastructure

networks:
  kocinfrastructure:
    external: true
    name: $NETWORK_NAME
EOF

# 4. Build and Start
echo "🏗 Building Docker image (this may take a minute)..."
docker compose up -d --build

# 5. Output Results
IP_ADDR=$(curl -s https://ifconfig.me)
echo "------------------------------------------"
echo "✅ SUCCESS! Dashboard is now running."
echo "🌐 Web UI: http://$IP_ADDR:8501"
echo "📊 Database: Linked to $NETWORK_NAME"
echo "------------------------------------------"
