import streamlit as st
import pandas as pd
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# 1. Accesso
if not check_password():
    st.stop()

st.set_page_config(page_title="Scout Basket PRO", layout="centered", page_icon="🏀")

# Inizializzazione dati
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

df_roster = load_roster()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Impostazioni")
if st.sidebar.button("🚨 Reset Sessione"):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

st.sidebar.divider()
teams = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
sq_sel = st.sidebar.selectbox("Squadra:", teams + ["+ NUOVA..."])
r_team = st.sidebar.text_input("Nome Squadra:").upper() if sq_sel == "+ NUOVA..." else sq_sel
r_name = st.sidebar.text_input("Nome Giocatore:").upper()

if st.sidebar.button("➕ Aggiungi Giocatore"):
    if r_name and r_team:
        save_player_to_roster(r_name, r_team)
        st.rerun()

st.sidebar.divider()
up_file = st.sidebar.file_uploader("📂 Carica Roster CSV", type=["csv"])
if up_file:
    pd.read_csv(up_file).to_csv("roster.csv", index=False)
    st.rerun()

if st.sidebar.button("🗑️ Svuota Roster"):
    pd.DataFrame(columns=['nome', 'squadra']).to_csv("roster.csv", index=False)
    st.rerun()

# --- MAIN APP ---
st.title("🏀 Scout Basket PRO")

col_t1, col_t2 = st.columns(2)
t_home = col_t1.text_input("Casa:", "CASA").upper()
t_away = col_t2.text_input("Ospite:", "OSPITE").upper()

st.divider()

# Selezione Squadra e Esito
c_team, c_res = st.columns(2)
p_team = c_team.radio("Chi ha tirato:", [t_home, t_away], horizontal=True)
esito = c_res.radio("Risultato:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"])

st.write("### 📍 Posiziona il tiro")
is_tl = "TL" in esito

if is_tl:
    cur_x, cur_y = 0, 142
    st.success("Tiro Libero: Posizione bloccata.")
else:
    # Gli slider controllano la stella senza far apparire rettangoli sul grafico
    cur_x = st.slider("Sposta (X)", -250, 250, 0, step=10)
    cur_y = st.slider("Distanza (Y)", -40, 420, 100, step=10)

# GRAFICO BLINDATO
fig = create_basketball_court(cur_x, cur_y, st.session_state.shots)
st.plotly_chart(fig, use_container_width=True, config={
    'staticPlot': True,         # <--- QUESTO ELIMINA IL RETTANGOLO PER SEMPRE
    'displayModeBar': False     # Rimuove icone inutili
})

if st.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
    s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
    made = "Segnato" in esito
    
    st.session_state.shots.append({
        "team": p_team, "x": cur_x, "y": cur_y, 
        "made": made, "type": s_type, "player": "TEAM"
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- EXPORT E PDF ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    st.write("📂 **Esporta Risultati:**")
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    # CSV
    exp_col1.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "partita.csv", use_container_width=True)
    
    # PDF
    try:
        pdf_data = generate_player_report(df, t_home)
        exp_col2.download_button("📄 PDF", pdf_data, f"Scout_{t_home}.pdf", "application/pdf", use_container_width=True)
    except:
        exp_col2.error("Errore PDF")

    # Elimina Ultimo
    if exp_col3.button("⬅️ Cancella", use_container_width=True):
        st.session_state.shots.pop()
        save_shots(st.session_state.shots)
        st.rerun()
