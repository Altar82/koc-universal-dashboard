import streamlit as st
import os
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="KOC Universal Dashboard",
    page_icon="🤜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styling CSS per richiamare il look "Knockout City"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; border-radius: 10px; padding: 15px; border: 1px solid #ff00ff; }
    .stButton>button { background-color: #ff00ff; color: white; border-radius: 20px; border: none; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #00ffff; color: black; }
    .stTextInput>div>div>input { background-color: #1f2937; color: white; border: 1px solid #00ffff; }
    h1, h2, h3 { color: #00ffff !important; text-transform: uppercase; font-family: 'Arial Black'; }
    .player-card { background: #1f2937; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 5px solid #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAZIONE AMBIENTE ---
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
SERVER_NAME = os.getenv("SERVER_NAME", "Nova")
MAX_PLAYERS = os.getenv("MAX_PLAYERS", "30")

# Auto-refresh ogni 10 secondi
st_autorefresh(interval=10000, key="global_refresh")

# --- HELPER FUNCTIONS ---
def time_ago(ts):
    if not ts: return "Never"
    if isinstance(ts, (int, float, str)) and str(ts).isdigit():
        dt = datetime.fromtimestamp(int(ts) / 1000)
    elif isinstance(ts, datetime):
        dt = ts
    else:
        return "Unknown"
    
    diff = (datetime.now() - dt).total_seconds()
    if diff < 60: return "Just now"
    if diff < 3600: return f"{int(diff//60)}m ago"
    if diff < 86400: return f"{int(diff//3600)}h ago"
    return dt.strftime("%Y-%m-%d")

PRESENCE_NAMES = {
    '0': '🏠 Hideout',
    '2': '🏢 Street Play',
    '6': '🔒 Private Match',
    '7': '👥 Lobby',
    '8': '🎯 Training',
}

PLATFORM_MAP = {
    'win64': '💻 PC',
    'switch': '🎮 Switch',
    'ps4': '🎮 PlayStation',
    'xbox': '🎮 Xbox'
}

# --- DATABASE LOGIC ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def get_redis_connection():
    return redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

# --- UI LAYOUT ---
st.title(f"🤜 {SERVER_NAME.upper()} // COMMAND CENTER")

tab_monitor, tab_stats, tab_friends = st.tabs(["📡 LIVE MONITOR", "📊 BRAWLER DOSSIER", "🤝 FRIENDSHIP"])

# --- TAB 1: MONITOR ONLINE ---
with tab_monitor:
    try:
        r = get_redis_connection()
        instance_keys = r.keys('backend:users:*')
        all_uids = set()
        for key in instance_keys:
            all_uids.update(r.smembers(key))
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("BRAWLERS ONLINE", f"{len(all_uids)} / {MAX_PLAYERS}")
            
            st.subheader("🏆 TOP 10 MMR")
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT u.username, s.current_mmr FROM skill s JOIN users u ON u.id = s.user_id ORDER BY s.current_mmr DESC LIMIT 10")
                    for i, row in enumerate(cur.fetchall()):
                        st.markdown(f"**#{i+1}** {row['username']} `{row['current_mmr']}`")

        with col2:
            st.subheader("🎮 CURRENT SESSIONS")
            if not all_uids:
                st.info("No brawlers in the streets right now...")
            else:
                processed_uids = set()
                group_keys = r.keys('group_members:*')
                
                # Render Gruppi
                for g_key in group_keys:
                    leader_id = g_key.split(':')[1]
                    members = r.smembers(g_key)
                    if leader_id in all_uids:
                        session = r.hgetall(f"user:session:{leader_id}")
                        if session:
                            st.markdown(f"""<div class='player-card'>
                                👑 <b>{session.get('username')}</b>'s Group ({len(members)} members)<br>
                                <small>📍 {PRESENCE_NAMES.get(session.get('rich_presence'), 'Online')}</small>
                            </div>""", unsafe_allow_html=True)
                            processed_uids.add(leader_id)
                            processed_uids.update(members)

                # Render Solo
                solo_uids = [uid for uid in all_uids if uid not in processed_uids]
                for uid in solo_uids:
                    session = r.hgetall(f"user:session:{uid}")
                    if session:
                        st.markdown(f"""<div class='player-card' style='border-left-color: #00ffff;'>
                            👤 <b>{session.get('username')}</b><br>
                            <small>📍 {PRESENCE_NAMES.get(session.get('rich_presence'), 'Online')}</small>
                        </div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Redis Connection Error: {e}")

# --- TAB 2: DOSSIER (STAT) ---
with tab_stats:
    st.subheader("🔍 ANALYZE BRAWLER")
    search_user = st.text_input("Enter Username", key="search_input")
    if search_user:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.*, s.*, sr.raw_xp_s6 as xp 
                    FROM users u 
                    JOIN skill s ON u.id = s.user_id 
                    LEFT JOIN street_rank sr ON u.id = sr.user_id 
                    WHERE u.username ILIKE %s LIMIT 1
                """, (search_user,))
                d = cur.fetchone()
                
                if d:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("MMR", d['current_mmr'])
                    c2.metric("WINS", d['wins'])
                    c3.metric("WIN STREAK", f"🔥 {d['win_streak']}")
                    
                    st.write(f"**Platform:** {PLATFORM_MAP.get(d['last_authenticated_platform'], d['last_authenticated_platform'])}")
                    st.write(f"**Last Seen:** {time_ago(d['last_authenticated_at'])}")
                    st.progress(min((d['xp'] or 0) % 10000 / 10000, 1.0), text=f"XP: {d['xp'] or 0}")
                else:
                    st.warning("Brawler not found in archives.")

# --- TAB 3: FRIENDSHIP ---
with tab_friends:
    st.subheader("🤝 DISPATCH FRIEND REQUEST")
    c_s, c_r = st.columns(2)
    sender = c_s.text_input("Your Username")
    target = c_r.text_input("Target Username")
    
    if st.button("SEND REQUEST"):
        if sender and target:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id, username FROM users WHERE username ILIKE %s OR username ILIKE %s", (sender, target))
                        found = cur.fetchall()
                        if len(found) >= 2:
                            s_id = next(f['id'] for f in found if f['username'].lower() == sender.lower())
                            t_id = next(f['id'] for f in found if f['username'].lower() == target.lower())
                            cur.execute("INSERT INTO friend_requests (sender_user_id, recipient_user_id, sender_persona_kind) VALUES (%s, %s, 0) ON CONFLICT DO NOTHING", (s_id, t_id))
                            conn.commit()
                            st.success(f"Friend request sent to {target}!")
                        else:
                            st.error("Could not find one or both brawlers.")
            except Exception as e:
                st.error(f"DB Error: {e}")
