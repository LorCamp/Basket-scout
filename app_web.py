import streamlit as st
import pandas as pd
import datetime
from auth import check_password
from engine import (
    get_shot_type, save_shots, load_shots, 
    load_roster, save_player_to_roster, delete_last_shot
)
from court_graphics import create_basketball_court
from reports import generate_player_report

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Scout Basket PRO 2026", layout="wide", page_icon="🏀")

# 2. CONTROLLO ACCESSO
if not check_password():
    st.stop()

user_id = st.session_state.get("username")

# 3. INIZIALIZZAZIONE DATI
all_teams = []
df_roster = pd.DataFrame()
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots(user_id)

df_roster = load_roster(user_id)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"🏀 Coach: {user_id}")
    tipo_sessione = st.radio("MODALITÀ:", ["Partita 🏟️", "Allenamento 🏃‍♂️"])
    st.divider()

    # --- GESTIONE ROSTER & SQUADRE ---
    with st.expander("📂 Gestione Roster e Squadre"):
        st.subheader("Crea Squadra")
        nuova_sq = st.text_input("Nome Squadra (es: U19)").upper()
        if st.button("Registra Squadra"):
            if nuova_sq:
                save_player_to_roster(user_id, "0", "COACH", "STAFF", nuova_sq)
                st.success(f"Squadra {nuova_sq} creata!")
                st.rerun()

        st.divider()
        st.subheader("Aggiunta Manuale Giocatore")
        if all_teams:
            sq_target = st.selectbox("Squadra:", all_teams, key="sq_man")
            c1, c2 = st.columns([1, 3])
            m_num = c1.text_input("N°", key="m_num")
            m_nome = c2.text_input("Nome", key="m_nome").upper()
            if st.button("Salva Giocatore"):
                if m_nome and m_num:
                    save_player_to_roster(user_id, m_num, m_nome, "G", sq_target)
                    st.toast(f"{m_nome} salvato!")
                    st.rerun()
        else:
            st.info("Crea prima una squadra.")

    st.divider()

    # --- EXPORT PDF ---
    if st.session_state.shots:
        st.subheader("📊 Report")
        try:
            df_export = pd.DataFrame(st.session_state.shots)
            t_report = df_export[df_export['team'] != 'AVVERSARI']['team'].unique()[0] if not df_export.empty else "TEAM"
            pdf_bytes = generate_player_report(df_export, t_report)
            st.download_button("📥 Scarica Referto PDF", data=pdf_bytes, file_name=f"report_{t_report}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"Errore PDF: {e}")

    # --- RESET & LOGOUT ---
    st.divider()
    if st.button("🚨 RESET TIRI", use_container_width=True, help="Cancella tutti i tiri della sessione"):
        from engine import get_conn
        get_conn().table("shots").delete().eq("user_id", user_id).execute()
        st.session_state.shots = []
        st.rerun()

    if st.button("🚪 Logout", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- CORPO CENTRALE ---
st.title(f"🏀 {tipo_sessione}")

# Definizione Squadre
all_teams = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []

if tipo_sessione == "Partita 🏟️":
    c_s1, c_s2, c_s3 = st.columns([2, 1, 2])
    t_home = c_s1.selectbox("Tua Squadra:", all_teams) if all_teams else c_s1.text_input("Tua Squadra:", "HOME").upper()
    
    # Gestione Avversari
    away_opts = [t for t in all_teams if t != t_home]
    t_away_sel = c_s3.selectbox("Avversari:", away_opts + ["+ NUOVA..."])
    t_away = c_s3.text_input("Nome Avversario:", "AVVERSARI").upper() if t_away_sel == "+ NUOVA..." else t_away_sel
    
    # Calcolo Punteggio Live
    df_all = pd.DataFrame(st.session_state.shots) if st.session_state.shots else pd.DataFrame()
    pts_h = df_all[df_all['team'] == t_home]['punti'].sum() if not df_all.empty else 0
    pts_a = df_all[df_all['team'] == "AVVERSARI"]['punti'].sum() if not df_all.empty else 0
    c_s2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{pts_h}-{pts_a}</h1>", unsafe_allow_html=True)
else:
    t_home = st.selectbox("Squadra:", all_teams) if all_teams else st.text_input("Squadra:", "TEAM").upper()
    t_away = "N/A"

st.divider()

# --- SELEZIONE GIOCATORE & QUINTETTO ---
df_team = df_roster[df_roster['squadra'] == t_home].copy() if not df_roster.empty else pd.DataFrame()
if not df_team.empty:
    df_team['display'] = df_team['numero'].astype(str) + " - " + df_team['nome']
    giocatori_dict = dict(zip(df_team['display'], df_team['nome']))
    lista_giocatori = sorted(giocatori_dict.keys())
else:
    lista_giocatori, giocatori_dict = [], {}

col_q, col_p, col_t = st.columns([1.5, 1.5, 1])
quintetto = col_q.multiselect("5 in Campo (per +/-):", lista_giocatori, max_selections=5)
p_disp = col_p.selectbox("Giocatore Azione:", lista_giocatori)
p_name = giocatori_dict.get(p_disp)
p_time = col_t.text_input("Minuto:", "00:00")

# --- TABS AZIONI ---
t1, t2, t3 = st.tabs(["🎯 Tiri", "📊 Stats Extra", "🚩 Avversari"])

with t1:
    esito = st.radio("Esito:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)
    is_tl = "TL" in esito
    
    # Coordinate e Campo
    cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0), st.slider("Y", -40, 420, 100))
    st.plotly_chart(create_basketball_court(cur_x, cur_y, st.session_state.shots), use_container_width=True)

    if st.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
        s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
        made = "Segnato" in esito
        pts = 1 if is_tl else (int(s_type[0]) if made else 0)
        in_campo = [giocatori_dict[p] for p in quintetto]
        
        nuovo_tiro = {
            "team": t_home, "player": p_name, "tempo": p_time, "x": cur_x, "y": cur_y, 
            "made": made, "type": s_type, "punti": pts, "on_court": in_campo
        }
        st.session_state.shots.append(nuovo_tiro)
        save_shots(user_id, st.session_state.shots)
        st.rerun()

with t2:
    c1, c2, c3 = st.columns(3)
    def reg_extra(tipo):
        in_campo = [giocatori_dict[p] for p in quintetto]
        st.session_state.shots.append({"team": t_home, "player": p_name, "tempo": p_time, "x": 0, "y": 0, "made": False, "type": tipo, "punti": 0, "on_court": in_campo})
        save_shots(user_id, st.session_state.shots); st.rerun()
    
    if c1.button("🤝 Assist"): reg_extra("AST")
    if c2.button("🏀 Rimb. Off"): reg_extra("OREB")
    if c3.button("🛡️ Rimb. Dif"): reg_extra("DREB")
    
    st.divider()
    if st.button("↩️ ANNULLA ULTIMA AZIONE (UNDO)", use_container_width=True):
        if st.session_state.shots:
            st.session_state.shots.pop()
            delete_last_shot(user_id)
            st.rerun()

with t3:
    st.subheader(f"Punti segnati da {t_away}")
    ca1, ca2, ca3 = st.columns(3)
    def reg_opp(p):
        in_campo = [giocatori_dict[p] for p in quintetto]
        st.session_state.shots.append({"team": "AVVERSARI", "player": "OPP", "tempo": p_time, "x": 0, "y": 0, "made": True, "type": "OPP_PTS", "punti": p, "on_court": in_campo})
        save_shots(user_id, st.session_state.shots); st.rerun()
    if ca1.button("+1 (Libero)"): reg_opp(1)
    if ca2.button("+2 (Canestro)"): reg_opp(2)
    if ca3.button("+3 (Tripla)"): reg_opp(3)

# --- BOX SCORE FINALE ---
if st.session_state.shots:
    st.divider()
    st.subheader("📊 Box Score Squadra")
    df_all = pd.DataFrame(st.session_state.shots)
    df_t = df_all[df_all['team'] == t_home]
    
    if not df_t.empty:
        rows = []
        # Calcolo Plus/Minus
        pm_map = {p: 0 for p in df_t['player'].unique()}
        for _, r in df_all.iterrows():
            if isinstance(r.get('on_court'), list) and r.get('punti', 0) > 0:
                for p_on in r['on_court']:
                    if p_on in pm_map:
                        pm_map[p_on] += r['punti'] if r['team'] == t_home else -r['punti']

        for p in df_t['player'].unique():
            p_df = df_t[df_t['player'] == p]
            fga = len(p_df[p_df['type'].isin(['2PT', '3PT'])])
            fgm = p_df[p_df['type'].isin(['2PT', '3PT'])]['made'].sum()
            fg3m = p_df[(p_df['type'] == '3PT') & (p_df['made'] == True)]['made'].count()
            efg = ((fgm + 0.5 * fg3m) / fga * 100) if fga > 0 else 0
            
            rows.append({
                "Giocatore": p, "PTS": p_df['punti'].sum(),
                "2PT": f"{p_df[p_df['type']=='2PT']['made'].sum()}/{len(p_df[p_df['type']=='2PT'])}",
                "3PT": f"{p_df[p_df['type']=='3PT']['made'].sum()}/{len(p_df[p_df['type']=='3PT'])}",
                "REB": len(p_df[p_df['type'].isin(['OREB', 'DREB'])]),
                "AST": len(p_df[p_df['type'] == "AST"]),
                "+/-": pm_map.get(p, 0),
                "eFG%": f"{efg:.1f}%"
            })
        st.dataframe(pd.DataFrame(rows).sort_values(by="PTS", ascending=False), use_container_width=True, hide_index=True)
