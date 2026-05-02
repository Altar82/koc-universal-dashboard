import streamlit as st
import pandas as pd
import psycopg2
import redis
import os
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Aggiorna la pagina ogni 10 secondi (10000 millisecondi)
# 'count' è una variabile interna che aumenta a ogni refresh
count = st_autorefresh(interval=10000, limit=None, key="fizzbuzzcounter")

# --- CONFIGURAZIONE UNIVERSALE ---
SERVER_NAME = os.getenv("SERVER_NAME", "KOC Private Server")
DB_URL = os.getenv("DATABASE_URL") or os.getenv("KOC_BACKEND_DB")
REDIS_H = os.getenv("REDIS_HOST") or os.getenv("KOC_BACKEND_REDIS_DB_HOST") or "redis"
REDIS_P = os.getenv("REDIS_PORT") or os.getenv("KOC_BACKEND_REDIS_DB_PORT") or "6379"

st.set_page_config(page_title=SERVER_NAME, page_icon="🎮", layout="wide")

# Helpers per la formattazione (Source 2)
def time_ago(ts):
    if not ts: return "Never"
    try:
        dt = datetime.fromtimestamp(int(ts)/1000) if len(str(ts)) > 10 else datetime.fromtimestamp(int(ts))
        diff = datetime.now() - dt
        if diff.days > 0: return f"{diff.days} days ago"
        if diff.seconds > 3600: return f"{diff.seconds // 3600}h ago"
        return f"{diff.seconds // 60}m ago"
    except: return "Unknown"

@st.cache_resource
def init_conns():
    pg = psycopg2.connect(DB_URL)
    r = redis.Redis(host=REDIS_H, port=int(REDIS_P), decode_responses=True)
    return pg, r

try:
    pg, r = init_conns()

    # --- HEADER & STATUS (Source 3) ---
    st.title(f"🌐 {SERVER_NAME} Network")
    
    # BOX: Stato Server
    with st.container():
        st.markdown("### 🔌 System Health")
        c1, c2, c3 = st.columns(3)
        c1.metric("Status", "🟢 ONLINE")
        # Player count da Redis (Source 4)
        online_uids = set()
        for key in r.keys('backend:users:*'):
            online_uids.update(r.smembers(key))
        c2.metric("Active Connections", len(online_uids))
        c3.info("Uptime: Managed by Docker")

    # --- TABS PRINCIPALI ---
    tab_live, tab_search, tab_leaderboard = st.tabs(["🔴 LIVE ACTIVITY", "🔍 BRAWLER DOSSIER", "🏆 RANKINGS"])

    # 1. LIVE ACTIVITY (Logica Gruppi Source 4)
    with tab_live:
        st.subheader("Current Sessions & Groups")
        group_keys = r.keys('group_members:*')
        processed = set()

        if not online_uids:
            st.info("No brawlers online at the moment.")
        else:
            for g_key in group_keys:
                leader_id = g_key.split(':')[-1]
                members = r.smembers(g_key)
                if leader_id in online_uids:
                    with st.expander(f"👥 Group Leader: {r.hget(f'user:session:{leader_id}', 'username') or leader_id}", expanded=True):
                        cols = st.columns(len(members) if len(members) > 0 else 1)
                        for i, mid in enumerate(members):
                            name = r.hget(f"user:session:{mid}", "username") or mid
                            cols[i % len(cols)].write(f"👤 {name}")
                            processed.add(mid)
            
            # Solo Players
            solos = online_uids - processed
            if solos:
                st.markdown("---")
                st.markdown("**Solo Players:**")
                for sid in solos:
                    name = r.hget(f"user:session:{sid}", "username") or sid
                    st.write(f"🏃 {name}")

    # 2. SEARCH & FRIENDSHIP (Source 2)
    with tab_search:
        st.subheader("Search Brawler Stats")
        search_col, friend_col = st.columns(2)

        with search_col:
            st.markdown("#### 🕵️ Statistics Lookup")
            user_input = st.text_input("Enter Username", key="search_box")
            if user_input:
                query = """
                    SELECT u.id, u.username, u.inserted_at, u.last_authenticated_at, 
                           s.current_mmr, s.wins, s.total_games_played, s.mvps
                    FROM users u
                    JOIN skill s ON u.id = s.user_id
                    WHERE u.username ILIKE %s LIMIT 1;
                """
                df = pd.read_sql(query, pg, params=(user_input,))
                if not df.empty:
                    d = df.iloc[0]
                    st.success(f"Dossier found for {d['username']}")
                    st.json({
                        "MMR": d['current_mmr'],
                        "Wins": d['wins'],
                        "Matches": d['total_games_played'],
                        "Joined": time_ago(d['inserted_at'])
                    })
                else:
                    st.error("Brawler not found.")

        with friend_col:
            st.markdown("#### 🤝 Send Friend Request")
            sender = st.text_input("Your Username")
            target = st.text_input("Recipient Username")
            if st.button("🚀 Send Request"):
                # Logica del bot Friendship
                st.info(f"Simulating request from {sender} to {target}...")
                # Qui andrebbe la INSERT INTO friend_requests del Source 2

    # 3. LEADERBOARD (Source 4)
    with tab_leaderboard:
        st.subheader("Top 20 Street MMR")
        query_mmr = """
            SELECT u.username, s.current_mmr 
            FROM skill s 
            JOIN users u ON u.id = s.user_id 
            ORDER BY s.current_mmr DESC LIMIT 20
        """
        df_mmr = pd.read_sql(query_mmr, pg)
        st.table(df_mmr)

except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")
