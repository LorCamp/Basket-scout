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

# --- FIX CSS PER TOUCH MOBILE ---
st.markdown("""
    <style>
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

# --- SIDEBAR COMPLETA ---
st.sidebar.title("⚙️ Controllo")

if st.sidebar.button("🚨 NUOVA PARTITA", key="reset_game"):
    st.session_state.shots = []
    save_shots([])
    st.session_state.last_touch = {"x": 0, "y": 100}
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("👥 Gestione Roster")

# Selezione/Creazione Squadra
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

# --- SEZIONE RIPRISTINATA: CARICAMENTO ROSTER ---
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
        else:
            st.sidebar.error("CSV non valido (colonne: nome, squadra)")
    except Exception as e:
        st.sidebar.error("Errore nel file")

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

# Selezione Azione
c1, c2, c3 = st.columns([1, 2, 1])
p_team = c1.radio("Team:", [t_home, t_away] if t_away else [t_home])
giocatori = df_roster[df_roster['squadra'] == p_team]['nome'].tolist() if not df_roster.empty else []
p_name = c2.selectbox("Giocatore:", giocatori) if giocatori else c2.text_input("Nome:")
p_time = c3.text_input("Tempo:", "00:00")

esito = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Gestione Coordinate
is_tl = "TL" in esito
cx = 0 if is_tl else st.session_state.last_touch["x"]
cy = 142 if is_tl else st.session_state.last_touch["y"]

# --- CAMPO INTERATTIVO ---
st.write("📍 **Tocca il punto del tiro:**")
fig = create_basketball_court(cx, cy, st.session_state.shots)

event = st.plotly_chart(fig, on_select="rerun", key="court_v155", config={'displayModeBar': False})

if event and "selection" in event and event["selection"].get("points"):
    new_x = event["selection"]["points"][0]["x"]
    new_y = event["selection"]["points"][0]["y"]
    if not is_tl:
        st.session_state.last_touch = {"x": new_x, "y": new_y}
        st.rerun()

if st.button("✅ REGISTRA AZIONE", type="primary", key="save_btn"):
    final_x = 0 if is_tl else st.session_state.last_touch["x"]
    final_y = 142 if is_tl else st.session_state.last_touch["y"]
    
    s_type = "TL" if is_tl else get_shot_type(final_x, final_y)
    made = "Canestro" in esito or "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "sessione": tipo_s, "team": p_team, "player": p_name, "tempo": p_time,
        "x": final_x, "y": final_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    df_t = df[df['team'] == p_team]
    if not df_t.empty:
        st.subheader(f"📊 {p_team}")
        met = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_t[df_t['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            met[i].metric(t, f"{m}/{tot}", f"{(m/tot*100) if tot>0 else 0:.1f}%")

    st.divider()
    b1, b2, b3 = st.columns(3)
    if b1.button("⬅️ Elimina Ultimo"):
        if st.session_state.shots:
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
    b2.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "scout.csv")
    try:
        pdf = generate_player_report(df, t_home)
        b3.download_button("📄 PDF", pdf, f"Report_{t_home}.pdf", "application/pdf")
    except:
        st.error("Errore PDF")
