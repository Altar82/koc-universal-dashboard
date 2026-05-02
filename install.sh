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
NETWORK_NAME=$(docker inspect postgres -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')

if [ -z "$NETWORK_NAME" ]; then
    echo "❌ Error: 'postgres' container not found. Please ensure your KOC server is running."
    exit 1
fi
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
