import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster, delete_last_shot
from reports import generate_player_report
from court_graphics import create_basketball_court

st.set_page_config(page_title="Scout Basket PRO", layout="wide") # Layout wide per tabelle larghe

if not check_password():
    st.stop()

user_id = st.session_state.get("username")
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots(user_id)
df_roster = load_roster(user_id)

# --- SIDEBAR ---
st.sidebar.title(f"👤 Coach: {user_id}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

with st.sidebar.expander("➕ Aggiungi Giocatore"):
    teams_db = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
    sq_in = st.selectbox("Squadra:", teams_db + ["+ NUOVA..."])
    final_sq = st.text_input("Nome Squadra:").upper() if sq_in == "+ NUOVA..." else sq_in
    new_n = st.text_input("Nome Giocatore:").upper()
    if st.button("Salva nel Roster"):
        if new_n and final_sq:
            save_player_to_roster(user_id, new_n, final_sq)
            st.rerun()

st.sidebar.subheader("📂 Importa Roster")
up_file = st.sidebar.file_uploader("Carica .csv", type=["csv"])
if up_file:
    pd.read_csv(up_file).to_csv(f"data_users/{user_id}/roster.csv", index=False)
    st.sidebar.success("Roster caricato!")
    st.rerun()

if st.sidebar.button("🚨 Reset Tiri"):
    st.session_state.shots = []
    save_shots(user_id, [])
    st.rerun()

# --- MAIN APP ---
st.title("🏀 Scout Basket PRO")
c_top1, c_top2 = st.columns(2)
tipo = c_top1.selectbox("Sessione:", ["Allenamento", "Partita"])
teams_list = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
t_home = c_top2.selectbox("Squadra:", teams_list) if teams_list else c_top2.text_input("Squadra:", "TEAM").upper()

st.divider()

# Input Azione
col_p, col_m, col_e = st.columns([1.5, 1, 2])
giocatori = df_roster[df_roster['squadra'] == t_home]['nome'].tolist() if not df_roster.empty else []
p_name = col_p.selectbox("Giocatore:", sorted(giocatori)) if giocatori else col_p.text_input("Nome:", "PLAYER")
p_time = col_m.text_input("Min:", "00:00")
esito = col_e.radio("Risultato:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Grafico
is_tl = "TL" in esito
cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))
st.plotly_chart(create_basketball_court(cur_x, cur_y, st.session_state.shots), use_container_width=True)

# Pulsanti
b1, b2 = st.columns([4, 1])
if b1.button("✅ REGISTRA AZIONE", type="primary", use_container_width=True):
    s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
    made = "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    st.session_state.shots.append({"team": t_home, "player": p_name, "tempo": p_time, "x": cur_x, "y": cur_y, "made": made, "type": s_type, "punti": pts})
    save_shots(user_id, st.session_state.shots)
    st.rerun()
if b2.button("↩️", use_container_width=True):
    if st.session_state.shots:
        st.session_state.shots.pop()
        delete_last_shot(user_id)
        st.rerun()

# --- STATISTICHE DETTAGLIATE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    df_t = df[df['team'] == t_home]
    
    if not df_t.empty:
        st.divider()
        st.subheader(f"📊 Box Score: {t_home} ({df_t['punti'].sum()} PTS)")

        # Logica Tabella Avanzata
        def get_stat(player_df, shot_type):
            sub = player_df[player_df['type'] == shot_type]
            made = sub['made'].sum()
            total = len(sub)
            return f"{made}/{total}"

        rows = []
        for player in df_t['player'].unique():
            p_df = df_t[df_t['player'] == player]
            rows.append({
                "Giocatore": player,
                "PTS": p_df['punti'].sum(),
                "2PT": get_stat(p_df, "2PT"),
                "3PT": get_stat(p_df, "3PT"),
                "TL": get_stat(p_df, "TL"),
                "% Tot": f"{(p_df['made'].sum()/len(p_df)*100):.1f}%"
            })
        
        st.table(pd.DataFrame(rows).sort_values(by="PTS", ascending=False))

        # Download
        d1, d2 = st.columns(2)
        d1.download_button("Scarica CSV", df.to_csv(index=False).encode('utf-8'), "scout.csv", use_container_width=True)
        try:
            pdf_data = generate_player_report(df, t_home)
            d2.download_button("Scarica PDF", pdf_data, "Report.pdf", "application/pdf", use_container_width=True)
        except: st.write("")
