#!/bin/bash
echo "🚀 Installing KOC Universal Dashboard..."
if [ ! -d "koc-dashboard" ]; then
  git clone https://github.com/Altar82/koc-universal-dashboard.git koc-dashboard
  cd koc-dashboard
else
  cd koc-dashboard
  git pull
fi
docker compose up -d --build
echo "✅ Done! Dashboard: http://$(curl -s https://ifconfig.me):8501"
