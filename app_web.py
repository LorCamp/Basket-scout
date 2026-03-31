import streamlit as st
import pandas as pd
import datetime

# --- 1. IMPORT MODULI ---
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

# --- 3. CARICAMENTO DATI (Prima della Sidebar) ---
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots(user_id)

# Inizializzazione variabili per evitare NameError
all_teams = []
df_roster = load_roster(user_id)

if not df_roster.empty and 'squadra' in df_roster.columns:
    all_teams = sorted(df_roster['squadra'].unique().tolist())

# Coordinate mirino stella
if 'px' not in st.session_state: st.session_state.px = 0.0
if 'py' not in st.session_state: st.session_state.py = 100.0

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"🏀 Coach: {user_id}")
    tipo_sessione = st.radio("MODALITÀ:", ["Partita 🏟️", "Allenamento 🏃‍♂️"])
    st.divider()

    # --- GESTIONE ROSTER & SQUADRE ---
    with st.expander("📂 Gestione Roster e Squadre", expanded=False):
        # A) Importazione CSV
        st.subheader("📥 Importa da CSV")
        up_file = st.file_uploader("Carica file .csv", type=["csv"], key="uploader")
        if up_file:
            df_up = pd.read_csv(up_file)
            df_up.columns = [c.lower().strip() for c in df_up.columns]
            if st.button("Conferma Importazione"):
                for _, r in df_up.iterrows():
                    save_player_to_roster(user_id, r.get('numero','0'), r.get('nome','?'), r.get('ruolo','G'), r.get('squadra','MIA SQ'))
                st.success("Roster Caricato!")
                st.rerun()
        
        st.divider()
        # B) Aggiunta Squadra Manuale
        st.subheader("Crea Squadra")
        nuova_sq_nome = st.text_input("Nome Team (es. U17)").upper()
        if st.button("Registra Team"):
            if nuova_sq_nome:
                # Crea un coach fittizio per inizializzare la squadra
                save_player_to_roster(user_id, "0", "COACH", "STAFF", nuova_sq_nome)
                st.rerun()

        st.divider()
        # C) Aggiunta Giocatore Manuale
        st.subheader("Aggiungi Giocatore")
        if all_teams:
            sq_sel = st.selectbox("A quale squadra?", all_teams)
            c1, c2 = st.columns([1, 3])
            m_num = c1.text_input("N°")
            m_nome = c2.text_input("Nome").upper()
            if st.button("Salva nel Database"):
                if m_nome and m_num:
                    save_player_to_roster(user_id, m_num, m_nome, "G", sq_sel)
                    st.toast(f"{m_nome} aggiunto!")
                    st.rerun()
        else:
            st.info("Crea prima una squadra.")

    st.divider()

    # --- REPORT PDF ---
    if st.session_state.shots:
        st.subheader("📊 Esportazione")
        try:
            df_rep = pd.DataFrame(st.session_state.shots)
            t_name = df_rep[df_rep['team'] != 'AVVERSARI']['team'].unique()[0] if not df_rep.empty else "TEAM"
            pdf_bytes = generate_player_report(df_rep, t_name)
            st.download_button("📥 Scarica Report PDF", data=pdf_bytes, file_name=f"Report_{t_name}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"Errore PDF: {e}")

    # --- RESET & LOGOUT ---
    st.divider()
    if st.button("🚨 RESET TOTALE", use_container_width=True):
        from engine import get_conn
        get_conn().table("shots").delete().eq("user_id", user_id).execute()
        st.session_state.shots = []
        st.rerun()

    if st.button("🚪 Logout", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- 5. CORPO CENTRALE ---
st.title(f"🏀 {tipo_sessione}")

# Selezione Squadre
if tipo_sessione == "Partita 🏟️":
    cs1, cs2, cs3 = st.columns([2, 1, 2])
    t_home = cs1.selectbox("Tua Squadra:", all_teams) if all_teams else cs1.text_input("Tua Squadra:", "HOME").upper()
    t_away = cs3.text_input("Avversari:", "AVVERSARI").upper()
    
    # Scoreboard Live
    df_live = pd.DataFrame(st.session_state.shots) if st.session_state.shots else pd.DataFrame()
    p_h = df_live[df_live['team'] == t_home]['punti'].sum() if not df_live.empty else 0
    p_a = df_live[df_live['team'] == "AVVERSARI"]['punti'].sum() if not df_live.empty else 0
    cs2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{p_h}-{p_a}</h1>", unsafe_allow_html=True)
else:
    t_home = st.selectbox("Squadra:", all_teams) if all_teams else st.text_input("Squadra:", "TEAM").upper()
    t_away = "N/A"

# Filtro Giocatori
df_t_players = df_roster[df_roster['squadra'] == t_home].copy() if not df_roster.empty else pd.DataFrame()
lista_nomi = sorted(df_t_players['nome'].tolist()) if not df_t_players.empty else []

st.divider()
cq, cp = st.columns([2, 1])
quintetto = cq.multiselect("Quintetto in campo (per +/-):", lista_nomi)
p_name = cp.selectbox("Giocatore Azione:", lista_nomi)

# --- TABS AZIONI ---
t_tiri, t_extra, t_opp = st.tabs(["🎯 Tiri", "📊 Stats Extra", "🚩 Avversari"])

with t_tiri:
    esito = st.radio("Esito:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)
    is_tl = "TL" in esito
    
    st.session_state.px = st.slider("X", -250, 250, int(st.session_state.px))
    st.session_state.py = st.slider("Y", -40, 420, int(st.session_state.py))
    
    # Mostriamo solo i tiri della squadra selezionata
    shots_view = [s for s in st.session_state.shots if s.get('team') == t_home]
    st.plotly_chart(create_basketball_court(st.session_state.px, st.session_state.py, shots_view), use_container_width=True)

    if st.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
        s_type = "TL" if is_tl else get_shot_type(st.session_state.px, st.session_state.py)
        made = "Segnato" in esito
        pts = 1 if is_tl else (int(s_type[0]) if made else 0)
        
        st.session_state.shots.append({
            "team": t_home, "player": p_name, "x": float(st.session_state.px), 
            "y": float(st.session_state.py), "made": made, "type": s_type, 
            "punti": pts, "on_court": quintetto
        })
        save_shots(user_id, st.session_state.shots)
        st.rerun()

with t_extra:
    def reg_ex(tipo):
        st.session_state.shots.append({"team": t_home, "player": p_name, "x": 0, "y": 0, "made": False, "type": tipo, "punti": 0, "on_court": quintetto})
        save_shots(user_id, st.session_state.shots); st.rerun()
    
    c1, c2, c3 = st.columns(3)
    if c1.button("🤝 Assist"): reg_ex("AST")
    if c2.button("🏀 Rimb. Off"): reg_ex("OREB")
    if c3.button("🛡️ Rimb. Dif"): reg_ex("DREB")
    
    st.divider()
    if st.button("🗑️ ANNULLA ULTIMA AZIONE", use_container_width=True):
        if st.session_state.shots:
            st.session_state.shots.pop()
            delete_last_shot(user_id)
            st.rerun()

with t_opp:
    def reg_opp(p):
        st.session_state.shots.append({"team": "AVVERSARI", "player": "OPP", "x": 0, "y": 0, "made": True, "type": "OPP_PTS", "punti": p, "on_court": quintetto})
        save_shots(user_id, st.session_state.shots); st.rerun()
    
    co1, co2, co3 = st.columns(3)
    if co1.button("+1 Avversario"): reg_opp(1)
    if co2.button("+2 Avversario"): reg_opp(2)
    if co3.button("+3 Avversario"): reg_opp(3)

# --- BOX SCORE ---
if st.session_state.shots:
    st.divider()
    df_box = pd.DataFrame(st.session_state.shots)
    df_t = df_box[df_box['team'] == t_home]
    
    if not df_t.empty:
        st.subheader("📊 Statistiche Live")
        # Calcolo +/- veloce
        pm_map = {p: 0 for p in lista_nomi}
        for _, r in df_box.iterrows():
            if r.get('punti', 0) > 0 and isinstance(r.get('on_court'), list):
                for p_on in r['on_court']:
                    if p_on in pm_map:
                        pm_map[p_on] += r['punti'] if r['team'] == t_home else -r['punti']
        
        stats = []
        for p in df_t['player'].unique():
            if p == "OPP" or p == "COACH": continue
            p_df = df_t[df_t['player'] == p]
            stats.append({
                "Giocatore": p,
                "PTS": p_df['punti'].sum(),
                "2PT": f"{p_df[p_df['type']=='2PT']['made'].sum()}/{len(p_df[p_df['type']=='2PT'])}",
                "3PT": f"{p_df[p_df['type']=='3PT']['made'].sum()}/{len(p_df[p_df['type']=='3PT'])}",
                "REB": len(p_df[p_df['type'].isin(['OREB', 'DREB'])]),
                "AST": len(p_df[p_df['type'] == "AST"]),
                "+/-": pm_map.get(p, 0)
            })
        st.dataframe(pd.DataFrame(stats).sort_values("PTS", ascending=False), use_container_width=True, hide_index=True)
