import streamlit as st
import pandas as pd
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report # <--- Assicurati che questo file esista
from court_graphics import create_basketball_court

if not check_password():
    st.stop()

st.set_page_config(page_title="Basket Scout PRO", layout="centered", page_icon="🏀")

# Inizializzazione sessione
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

df_roster = load_roster()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Gestione")
if st.sidebar.button("🚨 Reset Partita"):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

st.sidebar.divider()
teams = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
sq_sel = st.sidebar.selectbox("Squadra:", teams + ["+ NUOVA..."])
r_team = st.sidebar.text_input("Nome Squadra:").upper() if sq_sel == "+ NUOVA..." else sq_sel
r_name = st.sidebar.text_input("Nome Giocatore:").upper()

if st.sidebar.button("➕ Aggiungi al Roster"):
    if r_name and r_team:
        save_player_to_roster(r_name, r_team)
        st.rerun()

st.sidebar.divider()
up_file = st.sidebar.file_uploader("📂 Carica CSV Roster", type=["csv"])
if up_file:
    pd.read_csv(up_file).to_csv("roster.csv", index=False)
    st.rerun()

# --- MAIN ---
st.title("🏀 Basket Scout PRO")

col_info = st.columns(2)
t_home = col_info[0].text_input("Casa:", "CASA").upper()
t_away = col_info[1].text_input("Ospite:", "OSPITE").upper()

st.divider()

# Input tiri
c1, c2 = st.columns(2)
p_team = c1.radio("Team tira:", [t_home, t_away], horizontal=True)
esito = c2.radio("Esito:", ["Canestro", "Errore", "TL Segnato", "TL Sbagliato"])

st.write("### 📍 Posiziona il tiro")
is_tl = "TL" in esito

if is_tl:
    cur_x, cur_y = 0, 142
    st.info("Posizione Tiri Liberi automatica (Stella in lunetta).")
else:
    cur_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=5)
    cur_y = st.slider("Distanza dal fondo", -40, 400, 100, step=5)

# Visualizzazione Campo
fig = create_basketball_court(cur_x, cur_y, st.session_state.shots)
st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=True)

if st.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
    s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
    made = "Canestro" in esito or "Segnato" in esito
    
    st.session_state.shots.append({
        "team": p_team, "x": cur_x, "y": cur_y, 
        "made": made, "type": s_type, "player": "TEAM"
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE E EXPORT ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    # Visualizziamo gli ultimi 3 tiri per controllo
    st.write("📝 **Ultimi tiri:**")
    st.dataframe(df.tail(3), use_container_width=True)
    
    st.write("📂 **Esporta Risultati:**")
    col_d1, col_d2, col_d3 = st.columns(3)
    
    # 1. Bottone CSV
    col_d1.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "partita.csv", use_container_width=True)
    
    # 2. Bottone PDF (Richiama reports.py)
    try:
        pdf_data = generate_player_report(df, t_home)
        col_d2.download_button("📄 PDF", pdf_data, f"Scout_{t_home}.pdf", "application/pdf", use_container_width=True)
    except Exception as e:
        col_d2.error("Errore PDF")

    # 3. Elimina Ultimo
    if col_d3.button("⬅️ Cancella", use_container_width=True):
        st.session_state.shots.pop()
        save_shots(st.session_state.shots)
        st.rerun()
