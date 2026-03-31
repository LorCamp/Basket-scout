import streamlit as st
import pandas as pd
# Assicurati che i nomi qui corrispondano esattamente a quelli nel tuo engine.py
from engine import (
    load_shots, save_shots, delete_last_shot, 
    load_roster, save_player_to_roster, get_shot_type,
    generate_player_report # La tua funzione PDF
)
from auth import check_password

# 1. Configurazione
st.set_page_config(page_title="Scout Basket Cloud", layout="wide")

if not check_password():
    st.stop()

user_id = st.session_state.username

# 2. Caricamento Dati
if "shots" not in st.session_state:
    st.session_state.shots = load_shots(user_id)

df_roster = load_roster(user_id)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🏀 Coach: {user_id}")
    modalita = st.radio("MODALITÀ:", ["Partita 🏟️", "Allenamento 🏃‍♂️"])
    
    with st.expander("📂 Gestione Roster"):
        up_file = st.file_uploader("Carica CSV", type=["csv"])
        if up_file:
            # Qui andrebbe la logica di import che abbiamo scritto prima
            pass
        
        st.divider()
        st.subheader("Aggiunta Manuale")
        n_num = st.text_input("N°", key="n_num")
        n_nome = st.text_input("Cognome Nome").upper()
        if st.button("Salva Giocatore"):
            save_player_to_roster(user_id, n_num, n_nome, "PG", "MIA SQUADRA")
            st.rerun()

    if st.button("🚪 Logout", type="primary"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- CORPO CENTRALE ---
st.title("🏀 Tabellone Scouting")

col_sx, col_dx = st.columns([2, 1])

with col_sx:
    # --- IL CAMPO DA BASKET ---
    # Qui devi richiamare la tua funzione che disegna il campo (es. draw_court)
    # Se hai il codice in court_graphics.py, importalo e usalo qui.
    st.subheader("Campo di Gioco")
    
    # ESEMPIO INTERFACCIA DI INSERIMENTO RAPIDO
    if not df_roster.empty:
        giocatore_attivo = st.selectbox("Chi ha tirato?", df_roster['nome'].tolist())
        
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ 2PT SEGNATO", use_container_width=True):
            nuovo = {"user_id": user_id, "player": giocatore_attivo, "type": "2PT", "made": True, "punti": 2, "team": "MIA SQUADRA"}
            st.session_state.shots.append(nuovo)
            save_shots(user_id, st.session_state.shots)
            st.rerun()
            
        if c2.button("❌ 2PT SBAGLIATO", use_container_width=True):
            nuovo = {"user_id": user_id, "player": giocatore_attivo, "type": "2PT", "made": False, "punti": 0, "team": "MIA SQUADRA"}
            st.session_state.shots.append(nuovo)
            save_shots(user_id, st.session_state.shots)
            st.rerun()

        if c3.button("🗑️ UNDO (Annulla)", use_container_width=True):
            delete_last_shot(user_id)
            st.session_state.shots = load_shots(user_id)
            st.rerun()
    else:
        st.warning("⚠️ Carica prima i giocatori nel Roster dalla sidebar!")

with col_dx:
    st.subheader("Box Score Live")
    if st.session_state.shots:
        df_display = pd.DataFrame(st.session_state.shots)
        # Mostriamo le statistiche veloci
        stats = df_display.groupby('player')['punti'].sum().reset_index()
        st.dataframe(stats, hide_index=True, use_container_width=True)
    
    st.divider()
    st.subheader("📊 Analisi & Export")
    if st.session_state.shots:
        pdf_bytes = generate_player_report(pd.DataFrame(st.session_state.shots), "MIA SQUADRA")
        st.download_button("📥 SCARICA PDF", data=pdf_bytes, file_name="report.pdf", use_container_width=True)
