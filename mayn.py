import streamlit as st
import pandas as pd
import psycopg2
import redis
import os
from urllib.parse import urlparse

server_name = os.getenv("SERVER_NAME", "KOC Private Server")

st.set_page_config(page_title=f"{server_name} Dashboard", page_icon="🎮", layout="wide")
st.title(f"🚀 {server_name} - Management Panel")

@st.cache_resource
def init_connections():
    db_url = os.getenv("KOC_BACKEND_DB") or os.getenv("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URL or KOC_BACKEND_DB not found.")
        st.stop()
    conn_pg = psycopg2.connect(db_url)
    r_host = os.getenv("KOC_BACKEND_REDIS_DB_HOST") or os.getenv("REDIS_HOST") or "redis"
    r_port = os.getenv("KOC_BACKEND_REDIS_DB_PORT") or os.getenv("REDIS_PORT") or "6379"
    r_pass = os.getenv("REDIS_PASSWORD", None)
    conn_red = redis.Redis(host=r_host, port=int(r_port), password=r_pass, decode_responses=True)
    return conn_pg, conn_red, db_url, f"{r_host}:{r_port}"

try:
    pg, red, active_db, active_redis = init_connections()
    st.sidebar.header("Connection Info")
    st.sidebar.success(f"Connected to: {server_name}")
    st.sidebar.text(f"DB Host: {urlparse(active_db).hostname}")
    st.sidebar.text(f"Redis: {active_redis}")
    
    st.subheader("Real-time Metrics")
    col1, col2, col3 = st.columns(3)
    try:
        online_count = len(red.keys("player_session:*"))
        col1.metric("Online Players", online_count)
    except:
        col1.metric("Online Players", "N/A")
    total_players = pd.read_sql("SELECT COUNT(*) FROM players", pg).iloc[0,0]
    col2.metric("Registered Users", total_players)
    max_p = os.getenv("MAX_PLAYERS") or os.getenv("KOC_BACKEND_MAX_PLAYER_CONNECTIONS") or "N/A"
    col3.metric("Capacity", max_p)

    tab_p, tab_e = st.tabs(["Players List", "Economy Status"])
    with tab_p:
        df_players = pd.read_sql("SELECT id, name, created_at FROM players", pg)
        st.dataframe(df_players, use_container_width=True)
    with tab_e:
        df_econ = pd.read_sql("SELECT player_id, currency_balance FROM player_economies", pg)
        st.bar_chart(df_econ.set_index("player_id"))
except Exception as e:
    st.error(f"System Error: {e}")
