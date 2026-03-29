import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# 1. CONTROLLO ACCESSO (Password)
if not check_password():
    st.stop()

# 2. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Basket Scout PRO", layout="centered", page_icon="🏀")

# Inizializzazione dati
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

df_roster = load_roster()

# --- SIDEBAR: GESTIONE ROSTER E BACKUP ---
st.sidebar.title("⚙️ Pannello Controllo")

if st.sidebar.button("🚨 NUOVA PARTITA (Reset)", use_container_width=True):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("👥 Gestione Roster")

# Selezione squadra esistente o creazione nuova
teams_in_roster = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
scelta_t_roster = st.sidebar.selectbox("Squadra:", teams_in_roster + ["+ NUOVA SQUADRA..."], key="sidebar_squadra")

if scelta_t_roster == "+ NUOVA SQUADRA...":
    r_team = st.sidebar.text_input("Nome Nuova Squadra:").upper().strip()
else:
    r_team = scelta_t_roster

r_name = st.sidebar.text_input("Nome Giocatore:").upper().strip()

if st.sidebar.button("➕ Salva nel Roster", use_container_width=True, type="primary"):
    if r_name and r_team:
        save_player_to_roster(r_name, r_team)
        st.sidebar.success(f"Aggiunto: {r_name}")
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💾 Backup & Ripristino")

# Download Roster
if not df_roster.empty:
    st.sidebar.download_button(
        label="📥 Scarica Roster (CSV)",
        data=df_roster.to_csv(index=False).encode('utf-8'),
        file_name="mio_roster_basket.csv",
        mime="text/csv",
        use_container_width=True
    )

# Caricamento Roster
uploaded_file = st.sidebar.file_uploader("📂 Carica Roster da File", type=["csv"])
if uploaded_file is not None:
    try:
        new_df = pd.read_csv(uploaded_file)
        new_df.columns = [c.strip().lower() for c in new_df.columns]
        if 'nome' in new_df.columns and 'squadra' in new_df.columns:
            new_df[['nome', 'squadra']].to_csv("roster.csv", index=False)
            st.sidebar.success("✅ Caricato!")
            st.rerun()
    except:
        st.sidebar.error("File non valido")

if st.sidebar.button("🗑️ SVUOTA ROSTER", use_container_width=True):
    if os.path.exists("roster.csv"):
        os.remove("roster.csv")
        st.rerun()

# --- MAIN APP: SETUP MATCH ---
st.title("🏀 Basket Scout PRO")

col_sess, col_t1, col_t2 = st.columns([1, 1.5, 1.5])
tipo_sessione = col_sess.selectbox("Sessione:", ["Allenamento", "Partita"])

with col_t1:
    s_h = st.selectbox("Casa:", teams_in_roster + ["+ AGGIUNGI..."], key="h_sel")
    team_home = st.text_input("Nome Casa:", "CASA").upper().strip() if s_h == "+ AGGIUNGI..." else s_h

with col_t2:
    if tipo_sessione == "Partita":
        s_a = st.selectbox("Ospite:", teams_in_roster + ["+ AGGIUNGI..."], key="a_sel")
        team_away = st.text_input("Nome Ospite:", "OSPITE").upper().strip() if s_a == "+ AGGIUNGI..." else s_a
    else:
        team_away = None

st.divider()

# --- INPUT TIRO ---
col_act, col_name, col_time = st.columns([1.2, 1.8, 1])

with col_act:
    # Seleziona quale squadra sta tirando ora
    p_team = st.radio("Squadra al tiro:", [team_home, team_away] if team_away else [team_home])

with col_name:
    # Filtra i giocatori in base alla squadra selezionata nel radio button
    giocatori_filtrati = df_roster[df_roster['squadra'] == p_team]['nome'].tolist() if not df_roster.empty else []
    if giocatori_filtrati:
        p_name = st.selectbox("Tiratore:", giocatori_filtrati)
    else:
        p_name = st.text_input("Giocatore:").upper().strip()

p_time = col_time.text_input("Tempo:", "00:00")

esito = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Gestione Coordinate
is_tl = "TL" in esito
pos_x, pos_y = (0, 142) if is_tl else (st.slider("X (Largo)", -250, 250, 0, step=5), st.slider("Y (Lungo)", -50, 420, 100, step=5))

# --- DISEGNO CAMPO ---
fig = create_basketball_court(pos_x, pos_y, st.session_state.shots)
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

if st.button("✅ REGISTRA AZIONE", use_container_width=True, type="primary"):
    s_type = "TL" if is_tl else get_shot_type(pos_x, pos_y)
    made = "Canestro" in esito or "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "sessione": tipo_sessione, "team": p_team, "player": p_name, "tempo": p_time,
        "x": pos_x, "y": pos_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE E EXPORT ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    
    # Statistiche Individuali
    df_ind = df[(df['team'] == p_team) & (df['player'] == p_name)]
    if not df_ind.empty:
        st.subheader(f"👤 Individuale: {p_name}")
        c = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_ind[df_ind['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            c[i].metric(t, f"{m}/{tot}", f"{(m/tot*100) if tot>0 else 0:.1f}%")

    # Statistiche Squadra
    df_team_stats = df[df['team'] == p_team]
    if not df_team_stats.empty:
        st.subheader(f"📊 Team: {p_team}")
        ct = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_team_stats[df_team_stats['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            ct[i].metric(t, f"{m}/{tot}", f"{(m/tot*100) if tot>0 else 0:.1f}%")

    st.divider()
    
    # Pulsanti Azione
    c_del, c_csv, c_pdf = st.columns(3)
    
    if c_del.button("⬅️ Elimina Ultimo", use_container_width=True):
        if st.session_state.shots:
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
            
    c_csv.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "scout.csv", use_container_width=True)
    
    try:
        # Genera il report PDF (usiamo team_home come riferimento principale)
        pdf_bytes = generate_player_report(df, team_home)
        c_pdf.download_button("📄 PDF Report", pdf_bytes, f"Report_{team_home}.pdf", "application/pdf", use_container_width=True)
    except:
        c_pdf.error("Errore PDF")
