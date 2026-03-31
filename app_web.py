import streamlit as st
import pandas as pd
import datetime

# --- 1. IMPORT MODULI PERSONALIZZATI ---
from auth import check_password
from engine import (
    get_shot_type, save_shots, load_shots, 
    load_roster, save_player_to_roster, delete_last_shot
)
from court_graphics import create_basketball_court
from reports import generate_player_report

# --- 2. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Scout Basket PRO 2026", layout="wide", page_icon="🏀")

# Controllo Accesso
if not check_password():
    st.stop()

user_id = st.session_state.get("username")

# --- 3. INIZIALIZZAZIONE DATI E VARIABILI CORE ---
# Inizializziamo all_teams subito per evitare NameError nella sidebar
all_teams = []
df_roster = pd.DataFrame()

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots(user_id)

# Caricamento Roster dal Cloud
df_roster = load_roster(user_id)
if not df_roster.empty and 'squadra' in df_roster.columns:
    all_teams = sorted(df_roster['squadra'].unique().tolist())

# Coordinate mirino (X, Y)
if 'px' not in st.session_state: st.session_state.px = 0.0
if 'py' not in st.session_state: st.session_state.py = 100.0

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"🏀 Coach: {user_id}")
    tipo_sessione = st.radio("MODALITÀ:", ["Partita 🏟️", "Allenamento 🏃‍♂️"])
    st.divider()

    # --- GESTIONE ROSTER & SQUADRE ---
    with st.expander("📂 Gestione Roster e Squadre", expanded=False):
        # A) Import CSV
        st.subheader("📥 Importa CSV")
        up_file = st.file_uploader("Carica file .csv", type=["csv"])
        if up_file:
            df_up = pd.read_csv(up_file)
            df_up.columns = [c.lower().strip() for c in df_up.columns]
            if st.button("Conferma Importazione Massiva"):
                for _, r in df_up.iterrows():
                    save_player_to_roster(user_id, r.get('numero','0'), r.get('nome','?'), r.get('ruolo','G'), r.get('squadra','MIA SQ'))
                st.success("Roster Caricato!")
                st.rerun()
        
        st.divider()
        # B) Aggiunta Manuale Squadra
        st.subheader("Nuova Squadra")
        n_sq_man = st.text_input("Nome Team").upper()
        if st.button("Crea Team"):
            if n_sq_man:
                save_player_to_roster(user_id, "0", "COACH", "STAFF", n_sq_man)
                st.rerun()

        st.divider()
        # C) Aggiunta Manuale Giocatore
        st.subheader("Nuovo Giocatore")
        if all_teams:
            target_q = st.selectbox("Aggiungi a:", all_teams)
            c1, c2 = st.columns([1, 3])
            m_num = c1.text_input("N°")
            m_nome = c2.text_input("Nome").upper()
            if st.button("Salva Giocatore"):
                if m_nome and m_num:
                    save_player_to_roster(user_id, m_num, m_nome, "G", target_q)
                    st.rerun()
        else:
            st.info("Crea una squadra per aggiungere giocatori.")

    st.divider()

    # --- REPORT PDF ---
    if st.session_state.shots:
        st.subheader("📊 Esporta Report")
        try:
            df_rep = pd.DataFrame(st.session_state.shots)
            t_name = df_rep[df_rep['team'] != 'AVVERSARI']['team'].unique()[0] if not df_rep.empty else "TEAM"
            pdf_data = generate_player_report(df_rep, t_name)
            st.download_button("📥 Scarica PDF", data=pdf_data, file_name=f"Report_{t_name}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"Errore PDF: {e}")

    # --- RESET & LOGOUT ---
    st.divider()
    if st.button("🚨 RESET TOTALE TIRI", use_container_width=True, help="Cancella tutti i tiri dal database"):
        from engine import get_conn
        get_conn().table("shots").delete().eq("user_id", user_id).execute()
        st.session_state.shots = []
        st.rerun()

    if st.button("🚪 Logout", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- 5. CORPO CENTRALE ---
st.title(f"🏀 {tipo_sessione}")

# Selezione Squadre e Scoreboard
if tipo_sessione == "Partita 🏟️":
    cs1, cs2, cs3 = st.columns([2, 1, 2])
    t_home = cs1.selectbox("Tua Squadra:", all_teams) if all_teams else cs1.text_input("Tua Squadra:", "HOME").upper()
    t_away = cs3.text_input("Avversari:", "AVVERSARI").upper()
    
    df_live = pd.DataFrame(st.session_state.shots) if st.session_state.shots else pd.DataFrame()
    p_h = df_live[df_live['team'] == t_home]['punti'].sum() if not df_live.empty else 0
    p_a = df_live[df_live['team'] == "AVVERSARI"]['punti'].sum() if not df_live.empty else 0
    cs2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{p_h}-{p_a}</h1>", unsafe_allow_html=True)
else:
    t_home = st.selectbox("Squadra:", all_teams) if all_teams else st.text_input("Squadra:", "TEAM").upper()
    t_away = "N/A"

# Selezione Giocatori e Quintetto
df_t_players = df_roster[df_roster['squadra'] == t_home].copy() if not df_roster.empty else pd.DataFrame()
nomi_giocatori = sorted(df_t_players['nome'].tolist()) if not df_t_players.empty else []

st.divider()
cq, cp = st.columns([2, 1])
quintetto = cq.multiselect("5 in Campo (per +/-):", nomi_giocatori, help="Seleziona chi è in campo ora")
p_name = cp.selectbox("Giocatore al Tiro:", nomi_giocatori)

# --- TABS AZIONI ---
tab_tiri, tab_extra, tab_opp = st.tabs(["🎯 Tiri", "📊 Stats Extra", "🚩 Avversari"])

with tab_tiri:
    esito = st.radio("Esito:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)
    is_tl = "TL" in esito
    
    # Slider per mirino Stella Gialla
    st
