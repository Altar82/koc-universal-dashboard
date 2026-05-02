🎮 KOC Universal Server Dashboard
A powerful, lightweight, and universal web-based management dashboard for Knockout City private servers. Built with Python and Streamlit, it provides real-time insights into your server's database and session data.

✨ Features
- **[LIVE STATUS]**: Real-time CPU/RAM and Player Uptime monitoring.
- **[GAME MONITOR]**: Visual group detection and session tracking (Hideout, Street Play, etc.).
- **[BRAWLER DOSSIER]**: Deep-search player stats, wins, MVPs, and join dates.
- **[RANKINGS]**: Live Top 20 MMR Leaderboard.
- **[FRIENDSHIP]**: Send in-game friend requests via web interface

🚀 One-Command Installation
To install the dashboard on your server, simply run the following command in your terminal:

```curl -sSL https://raw.githubusercontent.com/Altar82/koc-universal-dashboard/main/install.sh | sudo bash```

🛠 Manual Integration
If you prefer to add it manually to your compose.yaml, add the following service:

```  
  dashboard:
    image: ghcr.io/Altar82/koc-dashboard:latest
    container_name: koc-dashboard-${SERVER_NAME}
    environment:
      - SERVER_NAME=${SERVER_NAME}
      - KOC_BACKEND_DB=${KOC_BACKEND_DB}
      - KOC_BACKEND_REDIS_DB_HOST=${KOC_BACKEND_REDIS_DB_HOST}
      - DATABASE_URL=${DATABASE_URL}
    ports:
      - "8501:8501"
    restart: always
```

📋 Prerequisites
A running Knockout City Private Server environment (Docker).
Existing postgres and redis services within the same Docker network.
🔒 Security
This dashboard is intended for internal management. It is highly recommended to:
Use a firewall to restrict access to port 8501.
Or use a reverse proxy (like Nginx or Traefik) with Basic Auth to protect the dashboard.
