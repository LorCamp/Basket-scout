import streamlit as st
import pandas as pd
import datetime

# --- IMPORTAZIONE MODULI PERSONALIZZATI ---
from auth import check_password
from engine import (
    load_shots, save_shots, delete_last_shot, 
    load_roster, save_player_to_roster
)
from court_graphics import create_basketball_court
from reports import generate_player_report

# 1. Configurazione Pagina
st.set_page_config(page_title="Scout Basket Cloud", layout="wide", page_icon="🏀")

# 2. Controllo Accesso (auth.py)
if not check_password():
    st.stop()

# 3. Inizializzazione Variabili
user_id = st.session_state.username

if "shots" not in st.session_state:
    st.session_state.shots = load_shots(user_id)

if "px" not in st.session_state: st.session_state.px = 0.0
if "py" not in st.session_state: st.session_state.py = 0.0

# Carichiamo il roster dal database
df_roster = load_roster(user_id)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🏀 Coach: {user_id}")
    modalita = st.radio("MODALITÀ:", ["Partita 🏟️", "Allenamento 🏃‍♂️"])
    
    st.divider()

    # ESPANDER: GESTIONE ROSTER
    with st.expander("📂 Gestione Roster"):
        st.subheader("Carica CSV")
        up_file = st.file_uploader("Trascina file qui", type=["csv"])
        if up_file:
            df_up = pd.read_csv(up_file)
            df_up.columns = [c.lower().strip() for c in df_up.columns]
            if st.button("Conferma Importazione"):
                for _, r in df_up.iterrows():
                    save_player_to_roster(user_id, r.get('numero','0'), r.get('nome','?'), r.get('ruolo','-'), r.get('squadra','MIA'))
                st.success("Roster aggiornato!")
                st.rerun()
        
        st.divider()
        st.subheader("Aggiunta Rapida")
        n_num = st.text_input("N°", key="manual_num")
        n_nome = st.text_input("Nome", key="manual_name").upper()
        if st.button("Salva Giocatore"):
            if n_nome and n_num:
                save_player_to_roster(user_id, n_num, n_nome, "G", "MIA SQUADRA")
                st.rerun()

    st.divider()
    
    # --- TASTO RESET DATI ---
    with st.expander("⚠️ Zona Pericolo"):
        st.warning("Il reset cancellerà TUTTI i tiri salvati su Supabase per questo account.")
        if st.button("🚨 RESET TOTALE PARTITA", use_container_width=True):
            try:
                from engine import get_conn
                conn = get_conn()
                # Cancella tutti i tiri dell'utente corrente dal database
                conn.table("shots").delete().eq("user_id", user_id).execute()
                
                # Svuota anche la memoria temporanea dell'app
                st.session_state.shots = []
                st.success("Dati resettati con successo!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore durante il reset: {e}")

    st.divider()
    
    # TASTO LOGOUT
    if st.button("🚪 Logout", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- CORPO CENTRALE ---
st.title("🏀 Tabellone Scouting")

col_sx, col_dx = st.columns([1.5, 1])

with col_sx:
    st.subheader("📍 Registra Tiro")
    
    # Visualizzazione Campo (court_graphics.py)
    fig = create_basketball_court(st.session_state.px, st.session_state.py, st.session_state.shots)
    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': False})

    # Controlli Mirino
    cx, cy = st.columns(2)
    st.session_state.px = cx.slider("Sposta Orizzontale (X)", -250.0, 250.0, st.session_state.px)
    st.session_state.py = cy.slider("Sposta Verticale (Y)", -40.0, 420.0, st.session_state.py)

    st.divider()

    # Selezione Giocatore e Azione
    if not df_roster.empty:
        lista_nomi = sorted(df_roster['nome'].tolist())
        giocatore = st.selectbox("Seleziona Giocatore:", lista_nomi)
        
        # Logica tipo tiro automatica
        t_type = "3PT" if st.session_state.py > 237 else "2PT"
        
        b1, b2, b3 = st.columns(3)
        
        if b1.button("✅ SEGNATO", use_container_width=True, type="primary"):
            nuovo = {
                "user_id": user_id, "player": giocatore, "x": float(st.session_state.px), 
                "y": float(st.session_state.py), "made": True, "type": t_type, 
                "punti": 3 if t_type=="3PT" else 2, "team": "MIA SQUADRA"
            }
            st.session_state.shots.append(nuovo)
            save_shots(user_id, st.session_state.shots)
            st.toast(f"Canestro di {giocatore}!")
            st.rerun()

        if b2.button("❌ SBAGLIATO", use_container_width=True):
            nuovo = {
                "user_id": user_id, "player": giocatore, "x": float(st.session_state.px), 
                "y": float(st.session_state.py), "made": False, "type": t_type, 
                "punti": 0, "team": "MIA SQUADRA"
            }
            st.session_state.shots.append(nuovo)
            save_shots(user_id, st.session_state.shots)
            st.rerun()
            
        if b3.button("🗑️ ANNULLA (UNDO)", use_container_width=True):
            delete_last_shot(user_id)
            st.session_state.shots = load_shots(user_id)
            st.rerun()
    else:
        st.warning("⚠️ Roster vuoto! Aggiungi giocatori dalla sidebar per iniziare.")

with col_dx:
    st.subheader("📊 Box Score Live")
    if st.session_state.shots:
        df_sh = pd.DataFrame(st.session_state.shots)
        # Tabella punti veloci
        box_score = df_sh.groupby('player')['punti'].sum().reset_index().sort_values('punti', ascending=False)
        st.dataframe(box_score, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("📥 Report PDF")
        
        # Generazione PDF (reports.py)
        try:
            pdf_bytes = generate_player_report(df_sh, "MIA SQUADRA")
            st.download_button(
                label="SCARICA MATCH REPORT",
                data=pdf_bytes,
                file_name=f"report_{user_id}_{datetime.datetime.now().strftime('%d%m')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore PDF: {e}")
    else:
        st.info("Nessun tiro registrato in questa sessione.")
