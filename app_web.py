import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

st.set_page_config(page_title="Scout Basket PRO", layout="centered")

# 1. ACCESSO
if not check_password():
    st.stop()

# Recuperiamo l'username dalla sessione (settato in auth.py)
user_id = st.session_state.username

# 2. CARICAMENTO DATI (Passiamo user_id come richiesto da engine.py)
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots(user_id)

df_roster = load_roster(user_id)

# --- SIDEBAR ---
st.sidebar.title(f"👤 Coach: {user_id}")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

st.sidebar.divider()
with st.sidebar.expander("➕ Aggiungi Giocatore"):
    teams_db = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
    sq_in = st.selectbox("Squadra:", teams_db + ["+ NUOVA..."])
    final_sq = st.text_input("Nome Squadra:").upper() if sq_in == "+ NUOVA..." else sq_in
    new_n = st.text_input("Nome Giocatore:").upper()
    if st.button("Salva"):
        if new_n and final_sq:
            save_player_to_roster(user_id, new_n, final_sq)
            st.rerun()

# --- MAIN APP ---
st.title("🏀 Scout Basket PRO")
tipo = st.selectbox("Sessione:", ["Allenamento", "Partita"])

# Selezione squadre
c1, c2 = st.columns(2)
teams_list = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
t_home = c1.selectbox("Casa:", teams_list) if teams_list else c1.text_input("Casa:", "CASA").upper()
t_away = c2.text_input("Ospite:", "OSPITE").upper() if tipo == "Partita" else None

st.divider()

# Input Azione
col_t, col_p, col_m = st.columns([1, 1.5, 1])
target_team = col_t.radio("Tira:", [t_home, t_away] if t_away else [t_home])
giocatori = df_roster[df_roster['squadra'] == target_team]['nome'].tolist() if not df_roster.empty else []
p_name = col_p.selectbox("Giocatore:", sorted(giocatori)) if giocatori else col_p.text_input("Nome:", "TEAM")
p_time = col_m.text_input("Min:", "00:00") if tipo == "Partita" else "N/A"

esito = st.radio("Esito:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Grafico
is_tl = "TL" in esito
cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))
fig = create_basketball_court(cur_x, cur_y, st.session_state.shots)
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})

if st.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
    s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
    made = "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "team": target_team, "player": p_name, "tempo": p_time, 
        "x": cur_x, "y": cur_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(user_id, st.session_state.shots)
    st.rerun()

# --- STATS ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    m1, m2 = st.columns(2)
    m1.metric(t_home, f"{df[df['team']==t_home]['punti'].sum()} pts")
    if t_away: m2.metric(t_away, f"{df[df['team']==t_away]['punti'].sum()} pts")
    
    df_t = df[df['team'] == target_team]
    if not df_t.empty:
        stats = df_t.groupby('player').agg(PTS=('punti', 'sum'), Seg=('made', 'sum'), Tot=('made', 'count'))
        stats['%'] = (stats['Seg']/stats['Tot']*100).round(1).astype(str)+'%'
        st.table(stats.sort_values(by='PTS', ascending=False))
