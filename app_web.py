import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# 1. CONTROLLO ACCESSO (L'app si ferma qui se non sei loggato)
if not check_password():
    st.stop()

# 2. SE SIAMO QUI, L'UTENTE È SICURAMENTE LOGGATO
user_id = st.session_state.username

# Inizializzazione Session State per i tiri
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

# Caricamento Roster
df_roster = load_roster()

# --- SIDEBAR ---
st.sidebar.title(f"👤 Coach: {user_id}")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.shots = []
    st.rerun()

st.sidebar.divider()

# AGGIUNTA MANUALE GIOCATORE
with st.sidebar.expander("➕ Aggiungi Giocatore"):
    teams_in_db = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
    sq_input = st.selectbox("Squadra:", teams_in_db + ["+ NUOVA..."])
    final_sq = st.text_input("Nome Nuova Squadra:").upper() if sq_input == "+ NUOVA..." else sq_input
    new_n = st.text_input("Nome Giocatore:").upper()
    if st.button("Salva nel Roster"):
        if new_n and final_sq:
            save_player_to_roster(new_n, final_sq)
            st.rerun()

st.sidebar.divider()

# CARICAMENTO FILE ESTERNO
up_file = st.sidebar.file_uploader("📂 Carica CSV Roster", type=["csv"])
if up_file:
    df_up = pd.read_csv(up_file)
    os.makedirs(f"data_users/{user_id}", exist_ok=True)
    df_up.to_csv(f"data_users/{user_id}/roster.csv", index=False)
    st.sidebar.success("Roster caricato!")
    st.rerun()

# --- INTERFACCIA PRINCIPALE ---
st.title("🏀 Scout Basket PRO")
tipo_sessione = st.selectbox("Sessione:", ["Allenamento", "Partita"])

col_t1, col_t2 = st.columns(2)
teams_list = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []

t_home = col_t1.selectbox("Casa:", teams_list) if teams_list else col_t1.text_input("Casa:", "CASA").upper()
t_away = col_t2.text_input("Ospite:", "OSPITE").upper() if tipo_sessione == "Partita" else None

st.divider()

# Input Azione
c_team, c_player, c_time = st.columns([1, 1.5, 1])
target_team = c_team.radio("Tira:", [t_home, t_away] if t_away else [t_home], horizontal=True)

giocatori = df_roster[df_roster['squadra'] == target_team]['nome'].tolist() if not df_roster.empty else []
p_name = c_player.selectbox("Giocatore:", sorted(giocatori)) if giocatori else c_player.text_input("Nome:", "TEAM")
p_time = c_time.text_input("Minuto:", "00:00") if tipo_sessione == "Partita" else "N/A"

esito = st.radio("Esito:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Grafico
is_tl = "TL" in esito
cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))

fig = create_basketball_court(cur_x, cur_y, st.session_state.shots)
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})

if st.button("✅ REGISTRA", type="primary", use_container_width=True):
    s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
    made = "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    st.session_state.shots.append({
        "team": target_team, "player": p_name, "tempo": p_time,
        "x": cur_x, "y": cur_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE LIVE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    sc1, sc2 = st.columns(2)
    sc1.metric(t_home, f"{df[df['team']==t_home]['punti'].sum()} pts")
    if t_away: sc2.metric(t_away, f"{df[df['team']==t_away]['punti'].sum()} pts")
    
    df_t = df[df['team'] == target_team]
    if not df_t.empty:
        st.write(f"📊 Stats {target_team}:")
        stats = df_t.groupby('player').agg(PTS=('punti', 'sum'), Seg=('made', 'sum'), Tot=('made', 'count'))
        stats['%'] = (stats['Seg']/stats['Tot']*100).round(1).astype(str)+'%'
        st.table(stats.sort_values(by='PTS', ascending=False))
        
        # Download
        exp_c1, exp_c2 = st.columns(2)
        exp_c1.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "partita.csv")
        try:
            pdf_data = generate_player_report(df, t_home)
            exp_c2.download_button("📄 PDF", pdf_data, "Report.pdf", "application/pdf")
        except: pass
