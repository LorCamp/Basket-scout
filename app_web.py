import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# 1. PROTEZIONE ACCESSO (Password)
if not check_password():
    st.stop()

# 2. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Basket Scout PRO", layout="centered", page_icon="🏀")

# --- FIX CSS PER TOUCH MOBILE v1.55+ ---
st.markdown("""
    <style>
    /* Impedisce al browser di interpretare lo scroll quando si tocca il grafico */
    .stPlotlyChart {
        touch-action: none;
        border: 1px solid #444;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Inizializzazione sessione
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()
if 'last_touch' not in st.session_state:
    st.session_state.last_touch = {"x": 0, "y": 100}

df_roster = load_roster()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Controllo")

if st.sidebar.button("🚨 NUOVA PARTITA (Reset Tiri)", key="reset_game"):
    st.session_state.shots = []
    save_shots([])
    st.session_state.last_touch = {"x": 0, "y": 100}
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("👥 Gestione Roster")

teams = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
s_squadra = st.sidebar.selectbox("Squadra:", teams + ["+ NUOVA..."], key="sb_sq")
r_team = st.sidebar.text_input("Nome Nuova Squadra:").upper() if s_squadra == "+ NUOVA..." else s_squadra
r_name = st.sidebar.text_input("Nome Giocatore:").upper()

if st.sidebar.button("➕ Salva Giocatore", type="primary", key="save_pl"):
    if r_name and r_team:
        save_player_to_roster(r_name, r_team)
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💾 Backup & Caricamento")

if not df_roster.empty:
    st.sidebar.download_button(
        label="📥 Scarica Roster Attuale",
        data=df_roster.to_csv(index=False).encode('utf-8'),
        file_name="mio_roster_basket.csv",
        mime="text/csv"
    )

uploaded_file = st.sidebar.file_uploader("📂 Carica Roster da CSV", type=["csv"], key="roster_upload")
if uploaded_file is not None:
    try:
        new_df = pd.read_csv(uploaded_file)
        new_df.columns = [c.strip().lower() for c in new_df.columns]
        if 'nome' in new_df.columns and 'squadra' in new_df.columns:
            new_df[['nome', 'squadra']].to_csv("roster.csv", index=False)
            st.sidebar.success("✅ Roster caricato!")
            st.rerun()
    except:
        st.sidebar.error("Errore nel file")

with st.sidebar.expander("⚠️ Zona Pericolo"):
    conf_delete = st.checkbox("Confermo cancellazione roster", key="confirm_delete_cb")
    if st.sidebar.button("🗑️ CANCELLA TUTTO IL ROSTER", disabled=not conf_delete, type="secondary", key="del_roster_btn"):
        empty_df = pd.DataFrame(columns=['nome', 'squadra'])
        empty_df.to_csv("roster.csv", index=False)
        st.rerun()

# --- MAIN APP ---
st.title("🏀 Basket Scout PRO")

col_s, col_h, col_a = st.columns([1, 1.5, 1.5])
tipo_s = col_s.selectbox("Sessione:", ["Allenamento", "Partita"])
with col_h:
    h_sel = st.selectbox("Casa:", teams + ["+ AGGIUNGI..."], key="h_s")
    t_home = st.text_input("Nome Casa:", "CASA").upper() if h_sel == "+ AGGIUNGI..." else h_sel
with col_a:
    t_away = None
    if tipo_s == "Partita":
        a_sel = st.selectbox("Ospite:", teams + ["+ AGGIUNGI..."], key="a_s")
        t_away = st.text_input("Nome Ospite:", "OSPITE").upper() if a_sel == "+ AGGIUNGI..." else a_sel

st.divider()

# Input Azione
c1, c2, c3 = st.columns([1, 2, 1])
p_team = c1.radio("Team tira:", [t_home, t_away] if t_away else [t_home], key="team_shoots_radio")
giocatori = df_roster[df_roster['squadra'] == p_team]['nome'].tolist() if not df_roster.empty else []
p_name = c2.selectbox("Giocatore:", giocatori, key="player_select") if giocatori else c2.text_input("Nome Giocatore:", key="player_manual")
p_time = c3.text_input("Tempo:", "00:00", key="time_input")

esito = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True, key="outcome_radio")

# Gestione Coordinate
is_tl = "TL" in esito
if is_tl:
    # Lunetta dei Tiri Liberi (fissa)
    cx, cy = 0, 142
else:
    # Ultimo tocco o default
    cx, cy = st.session_state.last_touch["x"], st.session_state.last_touch["y"]

# --- CAMPO INTERATTIVO (TOUCH Fix Rettangolo) ---
st.write("📍 **Tocca il punto del tiro sul campo:**")
fig = create_basketball_court(cx, cy, st.session_state.shots)

# Widget Plotly con on_select
event = st.plotly_chart(fig, on_select="rerun", key="court_mobile", config={'displayModeBar': False})

# Logica di cattura avanzata per v1.55+ (solo punti singoli)
if event and "selection" in event:
    pts = event["selection"].get("points", [])
    if pts:
        # Se c'è un punto, prendiamo le coordinate X e Y
        st.session_state.last_touch = {"x": pts[0]["x"], "y": pts[0]["y"]}
        st.rerun()

if st.button("✅ REGISTRA AZIONE", type="primary", key="save_btn"):
    final_x = 0 if is_tl else st.session_state.last_touch["x"]
    final_y = 142 if is_tl else st.session_state.last_touch["y"]
    
    s_type = "TL" if is_tl else get_shot_type(final_x, final_y)
    made = "Canestro" in esito or "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    # Salvataggio
    st.session_state.shots.append({
        "sessione": tipo_s, "team": p_team, "player": p_name, "tempo": p_time,
        "x": final_x, "y": final_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    # Reset stella per la prossima azione
    st.session_state.last_touch = {"x": 0, "y": 100}
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    df_t = df[df['team'] == p_team]
    if not df_t.empty:
        st.subheader(f"📊 Statistiche {p_team}")
        met = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_t[df_t['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            met[i].metric(t, f"{m}/{tot}", f"{(m/tot*100) if tot>0 else 0:.1f}%")

    st.divider()
    b1, b2, b3 = st.columns(3)
    if b1.button("⬅️ Elimina Ultimo", key="del_last"):
        if st.session_state.shots:
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
    b2.download_button("📥 Scarica CSV", df.to_csv(index=False).encode('utf-8'), "partita.csv", key="download_csv_btn")
    try:
        pdf_bytes = generate_player_report(df, t_home)
        b3.download_button("📄 PDF Report", pdf_bytes, f"Report_{t_home}.pdf", "application/pdf", key="download_pdf_btn")
    except:
        st.error("Errore generazione PDF")
