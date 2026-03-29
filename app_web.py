import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# 1. PROTEZIONE ACCESSO
if not check_password():
    st.stop()

# 2. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Basket Scout PRO", layout="centered", page_icon="🏀")

# Inizializzazione dati in sessione
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

if 'last_touch' not in st.session_state:
    st.session_state.last_touch = {"x": 0, "y": 100}

df_roster = load_roster()

# --- SIDEBAR: GESTIONE ROSTER E FILE ---
st.sidebar.title("⚙️ Pannello Controllo")

if st.sidebar.button("🚨 NUOVA PARTITA (Reset)", key="reset_btn"):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("👥 Gestione Roster")

# Selezione squadra (esistente o nuova)
teams_in_roster = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
scelta_t_roster = st.sidebar.selectbox("Squadra:", teams_in_roster + ["+ NUOVA SQUADRA..."], key="sidebar_squadra")

if scelta_t_roster == "+ NUOVA SQUADRA...":
    r_team = st.sidebar.text_input("Nome Nuova Squadra:").upper().strip()
else:
    r_team = scelta_t_roster

r_name = st.sidebar.text_input("Nome Giocatore:").upper().strip()

if st.sidebar.button("➕ Salva nel Roster", type="primary", key="save_roster"):
    if r_name and r_team:
        save_player_to_roster(r_name, r_team)
        st.sidebar.success(f"Aggiunto: {r_name}")
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💾 Backup CSV")

if not df_roster.empty:
    st.sidebar.download_button(
        label="📥 Scarica Roster",
        data=df_roster.to_csv(index=False).encode('utf-8'),
        file_name="mio_roster_basket.csv",
        mime="text/csv"
    )

uploaded_file = st.sidebar.file_uploader("📂 Carica Roster", type=["csv"])
if uploaded_file is not None:
    try:
        new_df = pd.read_csv(uploaded_file)
        new_df.columns = [c.strip().lower() for c in new_df.columns]
        if 'nome' in new_df.columns and 'squadra' in new_df.columns:
            new_df[['nome', 'squadra']].to_csv("roster.csv", index=False)
            st.rerun()
    except:
        st.sidebar.error("File non valido")

# --- MAIN APP: SETUP MATCH ---
st.title("🏀 Basket Scout PRO")

col_sess, col_t1, col_t2 = st.columns([1, 1.5, 1.5])
tipo_sessione = col_sess.selectbox("Sessione:", ["Allenamento", "Partita"])

with col_t1:
    s_h = st.selectbox("Casa:", teams_in_roster + ["+ AGGIUNGI..."], key="h_sel")
    team_home = st.text_input("Nome Casa:", "CASA").upper().strip() if s_h == "+ AGGIUNGI..." else s_h

with col_t2:
    team_away = None
    if tipo_sessione == "Partita":
        s_a = st.selectbox("Ospite:", teams_in_roster + ["+ AGGIUNGI..."], key="a_sel")
        team_away = st.text_input("Nome Ospite:", "OSPITE").upper().strip() if s_a == "+ AGGIUNGI..." else s_a

st.divider()

# --- INPUT AZIONE ---
col_act, col_name, col_time = st.columns([1.2, 1.8, 1])

with col_act:
    p_team = st.radio("Chi tira:", [team_home, team_away] if team_away else [team_home])

with col_name:
    giocatori_filtrati = df_roster[df_roster['squadra'] == p_team]['nome'].tolist() if not df_roster.empty else []
    p_name = st.selectbox("Tiratore:", giocatori_filtrati) if giocatori_filtrati else st.text_input("Giocatore:").upper().strip()

p_time = col_time.text_input("Tempo:", "00:00")

esito = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Logica coordinate (Touch vs TL)
is_tl = "TL" in esito
if is_tl:
    current_x, current_y = 0, 142
else:
    current_x, current_y = st.session_state.last_touch["x"], st.session_state.last_touch["y"]

# --- CAMPO INTERATTIVO (TOUCH) ---
st.write("📍 **Tocca il punto del tiro sul campo:**")
fig_court = create_basketball_court(current_x, current_y, st.session_state.shots)

# IMPORTANTE: use_container_width=True è necessario per mappare le coordinate X/Y 
# correttamente su schermi diversi (smartphone vs pc). 
# Se vuoi evitare il warning futuro, la versione 1.35+ di Streamlit usa ancora questo.
event = st.plotly_chart(
    fig_court, 
    use_container_width=True, 
    on_select="rerun", 
    config={'displayModeBar': False, 'staticPlot': False}
)

# Se l'utente tocca il campo, aggiorniamo la stella gialla
if event and "selection" in event and "points" in event["selection"] and len(event["selection"]["points"]) > 0:
    # Recuperiamo le coordinate dal punto toccato
    point = event["selection"]["points"][0]
    st.session_state.last_touch = {
        "x": point["x"],
        "y": point["y"]
    }
    st.rerun()


# --- BOTTONE REGISTRAZIONE ---
if st.button("✅ REGISTRA AZIONE", type="primary", key="reg_azione"):
    final_x = 0 if is_tl else st.session_state.last_touch["x"]
    final_y = 142 if is_tl else st.session_state.last_touch["y"]
    
    s_type = "TL" if is_tl else get_shot_type(final_x, final_y)
    made = "Canestro" in esito or "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "sessione": tipo_sessione, "team": p_team, "player": p_name, "tempo": p_time,
        "x": final_x, "y": final_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    
    # Report veloce squadra attiva
    df_t = df[df['team'] == p_team]
    if not df_t.empty:
        st.subheader(f"📊 Statistiche {p_team}")
        cols = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_t[df_t['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            cols[i].metric(t, f"{m}/{tot}", f"{(m/tot*100) if tot>0 else 0:.1f}%")

    st.divider()
    c_del, c_csv, c_pdf = st.columns(3)
    
    if c_del.button("⬅️ Elimina Ultimo", key="del_last"):
        if st.session_state.shots:
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
            
    c_csv.download_button("📥 Scarica CSV", df.to_csv(index=False).encode('utf-8'), "partita.csv")
    
    try:
        pdf_bytes = generate_player_report(df, team_home)
        c_pdf.download_button("📄 Genera PDF", pdf_bytes, f"Report_{team_home}.pdf", "application/pdf")
    except:
        st.error("Errore generazione PDF")