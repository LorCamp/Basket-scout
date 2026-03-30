import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster, delete_last_shot
from court_graphics import create_basketball_court

st.set_page_config(page_title="Scout Basket PRO 2026", layout="wide")

# 1. ACCESSO
if not check_password():
    st.stop()

user_id = st.session_state.get("username")
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots(user_id)
df_roster = load_roster(user_id)

# --- SIDEBAR: GESTIONE ---
st.sidebar.title(f"👤 Coach: {user_id}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.sidebar.divider()

if st.sidebar.button("🚨 RESET PARTITA", type="primary", use_container_width=True):
    st.session_state.shots = []
    save_shots(user_id, [])
    st.rerun()

with st.sidebar.expander("📂 Database & Roster"):
    up_file = st.sidebar.file_uploader("Importa CSV LBA", type=["csv"])
    if up_file:
        df_up = pd.read_csv(up_file)
        df_up.columns = [c.lower() for c in df_up.columns]
        path_r = f"data_users/{user_id}/roster.csv"
        os.makedirs(os.path.dirname(path_r), exist_ok=True)
        df_up.to_csv(path_r, index=False)
        st.rerun()
    
    st.write("---")
    st.subheader("Aggiungi Giocatore")
    teams_db = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
    sq_in = st.selectbox("Squadra:", teams_db + ["+ NUOVA..."])
    final_sq = st.text_input("Nome Team:").upper() if sq_in == "+ NUOVA..." else sq_in
    c_n, c_r = st.columns([1, 2])
    n_num = c_n.text_input("N°:")
    n_ruolo = c_r.selectbox("Ruolo:", ["PG", "SG", "SF", "PF", "C"])
    n_nome = st.text_input("Cognome Nome:").upper()
    if st.button("Salva nel Roster"):
        if n_nome and final_sq and n_num:
            save_player_to_roster(user_id, n_num, n_nome, n_ruolo, final_sq)
            st.rerun()

# --- HEADER: MATCH CENTER ---
st.title("🏀 Scout Match Center")
all_teams = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []

c_s1, c_s2, c_s3 = st.columns([2, 1, 2])

# Selezione Squadre
t_home = c_s1.selectbox("Tua Squadra:", all_teams, key="h_sel") if all_teams else c_s1.text_input("Tua Squadra:", "HOME").upper()
away_opts = [t for t in all_teams if t != t_home]
t_away_sel = c_s3.selectbox("Avversari:", away_opts + ["+ ALTRA..."], key="a_sel")
t_away = c_s3.text_input("Nome Avversario:", "AVVERSARI").upper() if t_away_sel == "+ ALTRA..." else t_away_sel

# Calcolo Punteggio
df_all = pd.DataFrame(st.session_state.shots) if st.session_state.shots else pd.DataFrame()
pts_h = df_all[df_all['team'] == t_home]['punti'].sum() if not df_all.empty else 0
pts_a = df_all[df_all['team'] == "AVVERSARI"]['punti'].sum() if not df_all.empty else 0

c_s2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{pts_h} - {pts_a}</h1>", unsafe_allow_html=True)
st.divider()

# --- INPUT LIVE ---
df_team = df_roster[df_roster['squadra'] == t_home].copy() if not df_roster.empty else pd.DataFrame()
if not df_team.empty:
    df_team['display'] = df_team['numero'].astype(str) + " - " + df_team['nome'] + " (" + df_team['ruolo'] + ")"
    giocatori_dict = dict(zip(df_team['display'], df_team['nome']))
    lista_giocatori = sorted(giocatori_dict.keys())
else:
    lista_giocatori, giocatori_dict = [], {}

col_q, col_p, col_m = st.columns([1.5, 1.5, 1])
with col_q:
    quintetto = st.multiselect("5 in Campo (per +/-):", lista_giocatori, max_selections=5)
with col_p:
    p_disp = st.selectbox("Giocatore Attivo:", lista_giocatori)
    p_name = giocatori_dict.get(p_disp)
with col_m:
    p_time = st.text_input("Minuto:", "00:00")

# --- AZIONI ---
t_shots, t_stat, t_opp = st.tabs(["🎯 Tiri", "📊 Stats Extra", "🚩 Avversari"])

with t_shots:
    esito = st.radio("Esito:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)
    is_tl = "TL" in esito
    cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))
    
    # Shot Chart
    s_plot = [s for s in st.session_state.shots if s.get('team') == t_home and s.get('type') in ['2PT', '3PT', 'TL']]
    st.plotly_chart(create_basketball_court(cur_x, cur_y, s_plot), use_container_width=True)

    if st.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
        s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
        made = "Segnato" in esito
        pts = 1 if is_tl else (int(s_type[0]) if made else 0)
        in_campo = [giocatori_dict[p] for p in quintetto]
        
        st.session_state.shots.append({
            "team": t_home, "player": p_name, "tempo": p_time, "x": cur_x, "y": cur_y, 
            "made": made, "type": s_type, "punti": pts, "on_court": in_campo
        })
        save_shots(user_id, st.session_state.shots)
        st.rerun()

with t_stat:
    def reg_extra(tipo):
        in_campo = [giocatori_dict[p] for p in quintetto]
        st.session_state.shots.append({
            "team": t_home, "player": p_name, "tempo": p_time, "x": 0, "y": 0, 
            "made": False, "type": tipo, "punti": 0, "on_court": in_campo
        })
        save_shots(user_id, st.session_state.shots)
        st.rerun()

    c1, c2, c3 = st.columns(3)
    if c1.button("🤝 Assist", use_container_width=True): reg_extra("AST")
    if c2.button("🏀 Rimbalzo Off", use_container_width=True): reg_extra("OREB")
    if c3.button("🛡️ Rimbalzo Dif", use_container_width=True): reg_extra("DREB")
    c4, c5, c6 = st.columns(3)
    if c4.button("❌ Palla Persa", use_container_width=True): reg_extra("TOV")
    if c5.button("🥷 Recuperata", use_container_width=True): reg_extra("STL")
    if c6.button("🛑 Fallo", use_container_width=True): reg_extra("FC")
    if st.button("↩️ Annulla Ultimo (Undo)", use_container_width=True):
        if st.session_state.shots: st.session_state.shots.pop(); delete_last_shot(user_id); st.rerun()

with t_opp:
    st.subheader(f"Segna Punti per {t_away}")
    ca1, ca2, ca3 = st.columns(3)
    def reg_opp(p):
        in_campo = [giocatori_dict[p] for p in quintetto]
        st.session_state.shots.append({
            "team": "AVVERSARI", "player": "OPPONENT", "tempo": p_time, "x": 0, "y": 0, 
            "made": True, "type": "OPP_PTS", "punti": p, "on_court": in_campo
        })
        save_shots(user_id, st.session_state.shots)
        st.rerun()
    if ca1.button("➕1 Libero", use_container_width=True): reg_opp(1)
    if ca2.button("➕2 Canestro", use_container_width=True): reg_opp(2)
    if ca3.button("➕3 Tripla", use_container_width=True): reg_opp(3)

# --- BOX SCORE ANALITICO ---
if not df_all.empty:
    df_t = df_all[df_all['team'] == t_home]
    if not df_t.empty:
        st.divider()
        st.subheader(f"📊 Box Score: {t_home}")
        
        rows = []
        plus_minus_map = {p: 0 for p in df_t['player'].unique()}
        
        # Calcolo +/-
        if 'on_court' in df_all.columns:
            for _, row in df_all.iterrows():
                if isinstance(row.get('on_court'), list) and row.get('punti', 0) > 0:
                    for p_on in row['on_court']:
                        if p_on in plus_minus_map:
                            plus_minus_map[p_on] += row['punti'] if row['team'] == t_home else -row['punti']

        for p in df_t['player'].unique():
            p_df = df_t[df_t['player'] == p]
            info = df_team[df_team['nome'] == p]
            
            # Funzione Rapporto Tiri
            def get_r(typ):
                sub = p_df[p_df['type'] == typ]
                return f"{sub['made'].sum()}/{len(sub)}" if not sub.empty else "0/0"
            
            # eFG%
            fga = len(p_df[p_df['type'].isin(['2PT', '3PT'])])
            fgm = p_df[p_df['type'].isin(['2PT', '3PT'])]['made'].sum()
            fg3m = p_df[(p_df['type'] == '3PT') & (p_df['made'] == True)]['made'].count()
            efg = ((fgm + 0.5 * fg3m) / fga * 100) if fga > 0 else 0

            rows.append({
                "N°": info['numero'].values[0] if not info.empty else "-",
                "R": info['ruolo'].values[0] if not info.empty else "-",
                "Giocatore": p,
                "PTS": p_df['punti'].sum(),
                "2PT": get_r("2PT"),
                "3PT": get_r("3PT"),
                "TL": get_r("TL"),
                "REB": len(p_df[p_df['type'].isin(['OREB', 'DREB'])]),
                "AST": len(p_df[p_df['type'] == "AST"]),
                "FC": len(p_df[p_df['type'] == "FC"]),
                "+/-": plus_minus_map.get(p, 0),
                "eFG%": f"{efg:.1f}%"
            })
            
        st.dataframe(pd.DataFrame(rows).sort_values(by="PTS", ascending=False), use_container_width=True)
