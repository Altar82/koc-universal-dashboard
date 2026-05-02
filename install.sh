#!/bin/bash
# KOC Universal Dashboard - Installer

echo "------------------------------------------"
echo "  KOC UNIVERSAL DASHBOARD INSTALLER      "
echo "------------------------------------------"
# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "❌ Please run the installer with sudo or as root:"
  echo "curl -sSL ... | sudo bash"
  exit 1
fi

# 1. Network Discovery Logic
echo "🔍 Detecting Docker network..."
# Cerca il primo container che ha "postgres" o "db" nel nome
CONTAINER_ID=$(docker ps --filter "name=postgres" --filter "name=db" --format "{{.ID}}" | head -n 1)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Error: Database container not found."
    exit 1
fi

# Ottiene la rete usando l'ID trovato
NETWORK_NAME=$(docker inspect $CONTAINER_ID -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')

echo "✅ Network detected: $NETWORK_NAME"

# 2. Setup Directory
echo "📁 Preparing local files..."
# (Logic to clone or pull goes here)

# 3. Create Dynamic Override
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
echo "🏗 Building Docker image..."
docker compose up -d --build

echo "------------------------------------------"
echo "✅ SUCCESS!"
echo "🌐 Web UI: http://$(curl -s https://ifconfig.me):8501"
echo "------------------------------------------"
