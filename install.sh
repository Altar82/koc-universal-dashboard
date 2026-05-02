#!/bin/bash
echo "🚀 Setting up KOC Universal Dashboard..."

# 1. Clone repository
REPO_NAME="koc-universal-dashboard"
if [ ! -d "$REPO_NAME" ]; then
    git clone https://github.com/Altar82/$REPO_NAME.git
    cd $REPO_NAME
else
    cd $REPO_NAME && git pull
fi

# 2. Start with Docker
# Nota: prenderà le variabili d'ambiente dal sistema o dal .env esistente
docker compose up -d --build

echo "✅ Installation complete!"
echo "🌐 Access your dashboard at: http://$(curl -s https://ifconfig.me):8501"
