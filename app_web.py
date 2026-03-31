import streamlit as st
import pandas as pd
from engine import (
    load_shots, save_shots, delete_last_shot, 
    load_roster, save_player_to_roster, get_shot_type, generate_pdf_report
)
# Assicurati di avere anche il tuo file auth.py per la funzione check_password
from auth import check_password

# 1. Configurazione Pagina
st.set_page_config(page_title="Scout Basket PRO", layout="wide", page_icon="🏀")

# 2. Controllo Accesso
if not check_password():
    st.stop()

# 3. Inizializzazione Variabili di Sessione
user_id = st.session_state.username

if "shots" not in st.session_state:
    # Carichiamo i tiri dal Cloud Supabase all'avvio
    st.session_state.shots = load_shots(user_id)

# Carichiamo il roster dal Cloud
df_roster = load_roster(user_id)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🏀 Coach: {user_id}")
    
    modalita = st.radio("MODALITÀ:", ["Partita 🏟️", "Allenamento 🏃‍♂️"])
    
    st.divider()

    # EXPANDER: GESTIONE ROSTER
    with st.expander("📂 Gestione Roster"):
        
        # --- SEZIONE 1: CARICAMENTO MASSIVO DA CSV ---
        st.subheader("Carica da File")
        up_file = st.file_uploader("Trascina qui il CSV della squadra", type=["csv"])
        
        if up_file:
            try:
                # Leggiamo il file caricato
                df_import = pd.read_csv(up_file)
                # Rendiamo i nomi delle colonne minuscoli per evitare errori (es. Nome -> nome)
                df_import.columns = [c.lower().strip() for c in df_import.columns]
                
                if st.button("Conferma Importazione Cloud"):
                    count = 0
                    with st.spinner("Salvataggio in corso..."):
                        for _, row in df_import.iterrows():
                            # Mappiamo i campi del CSV con le colonne del tuo DB
                            success = save_player_to_roster(
                                user_id, 
                                str(row.get('numero', '0')), 
                                str(row.get('nome', 'Sconosciuto')).upper(), 
                                str(row.get('ruolo', '-')).upper(), 
                                str(row.get('squadra', 'MIA SQUADRA')).upper()
                            )
                            if success: count += 1
                    
                    st.success(f"Caricati {count} giocatori su Supabase!")
                    st.rerun()
            except Exception as e:
                st.error(f"Errore nel file CSV: {e}")

        st.divider()

        # --- SEZIONE 2: AGGIUNTA MANUALE ---
        st.subheader("Aggiunta Singola")
        c1, c2 = st.columns([1, 2])
        n_num = c1.text_input("N°", key="manual_num")
        n_ruolo = c2.selectbox("Ruolo", ["PG", "SG", "SF", "PF", "C"], key="manual_role")
        n_nome = st.text_input("Cognome Nome", key="manual_name").upper()
        n_sq = st.text_input("Squadra", key="manual_sq").upper()

        if st.button("Salva Singolo", use_container_width=True):
            if n_nome and n_num:
                if save_player_to_roster(user_id, n_num, n_nome, n_ruolo, n_sq):
                    st.toast(f"Giocatore {n_nome} salvato!")
                    st.rerun()

    st.divider()

    # TASTO LOGOUT
    if st.button("🚪 Logout", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- CORPO CENTRALE ---
st.title("Tabellone Scouting")

# Esempio di interfaccia rapida per inserire tiri
col_sx, col_dx = st.columns([2, 1])

with col_sx:
    st.subheader("Campo di Gioco")
    # Qui andrebbe la tua logica Plotly per il campo
    st.info("Clicca sul campo per registrare un tiro (Logica in court_graphics.py)")
    
    # Esempio tasto rapido per testare il salvataggio
    if st.button("Simula Tiro Segnato (2PT)"):
        nuovo_tiro = {
            "user_id": user_id,
            "player": "TEST PLAYER",
            "x": 100.0,
            "y": 150.0,
            "made": True,
            "type": "2PT",
            "punti": 2
        }
        st.session_state.shots.append(nuovo_tiro)
        save_shots(user_id, st.session_state.shots)
        st.toast("Tiro salvato su Supabase!")

with col_dx:
    st.subheader("Box Score Live")
    if st.session_state.shots:
        df_display = pd.DataFrame(st.session_state.shots)
        st.dataframe(df_display[['player', 'type', 'punti', 'made']], use_container_width=True)
        
        if st.button("⬅️ Annulla Ultimo (Undo)"):
            delete_last_shot(user_id)
            st.session_state.shots = load_shots(user_id)
            st.rerun()
    else:
        st.write("Nessun tiro registrato.")

# --- SEZIONE REPORT ---
st.divider()
st.subheader("📊 Analisi & Export")

if st.session_state.shots:
    # Preparazione dati per il PDF
    # Trasformiamo la lista di tiri (da Supabase) in un DataFrame per la funzione PDF
    df_report = pd.DataFrame(st.session_state.shots)
    
    # Chiamata alla funzione che avevamo creato (assicurati che sia in engine.py)
    try:
        pdf_bytes = generate_pdf_report(user_id, st.session_state.shots)
        
        st.download_button(
            label="📥 SCARICA REPORT PDF",
            data=pdf_bytes,
            file_name=f"scout_{user_id}_partita.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="secondary"
        )
    except Exception as e:
        st.error(f"Errore generazione PDF: {e}")
else:
    st.info("Nessun dato disponibile per il PDF. Registra un tiro!")
