import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster, delete_last_shot
from court_graphics import create_basketball_court

st.set_page_config(page_title="Scout Basket PRO 2026", layout="wide")

if not check_password(): st.stop()

user_id = st.session_state.get("username")
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots(user_id)
df_roster = load_roster(user_id)

# --- SIDEBAR ---
st.sidebar.title(f"🏀 Coach: {user_id}")
tipo_sessione = st.sidebar.radio("MODALITÀ:", ["Partita 🏟️", "Allenamento 🏃‍♂️"])

if st.sidebar.button("🚨 RESET DATI", type="primary", use_container_width=True):
    st.session_state.shots = []
    save_shots(user_id, [])
    st.rerun()

st.sidebar.divider()

# --- EXPORT REPORT ---
if st.session_state.shots:
    st.sidebar.subheader("📊 Report Finale")
    df_export = pd.DataFrame(st.session_state.shots)
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Scarica Box Score (CSV)",
        data=csv,
        file_name=f"report_{tipo_sessione}_{user_id}.csv",
        mime='text/csv',
        use_container_width=True
    )

with st.sidebar.expander("📂 Gestione Roster"):
    # 1. CARICAMENTO CSV (Opzionale)
    up_file = st.file_uploader("Carica CSV LBA", type=["csv"])
    if up_file:
        df_up = pd.read_csv(up_file)
        df_up.columns = [c.lower() for c in df_up.columns]
        # Ciclo per caricare ogni riga del CSV su Supabase
        for _, row in df_up.iterrows():
            save_player_to_roster(
                user_id, 
                row.get('numero', '0'), 
                row.get('nome', 'Sconosciuto'), 
                row.get('ruolo', '-'), 
                row.get('squadra', 'MIA SQUADRA')
            )
        st.success("Roster caricato su Cloud!")
        st.rerun()
    st.divider()
    
    # 2. INSERIMENTO MANUALE (Quello che mancava nella foto)
    st.subheader("Aggiungi Giocatore")
    teams_db = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
    sq_in = st.selectbox("Squadra:", teams_db + ["+ NUOVA..."])
    final_sq = st.text_input("Nome Team:").upper() if sq_in == "+ NUOVA..." else sq_in
    
    c_n, c_r = st.columns([1, 2])
    n_num = c_n.text_input("N°:")
    n_ruolo = c_r.selectbox("Ruolo:", ["PG", "SG", "SF", "PF", "C"])
    n_nome = st.text_input("Cognome Nome:").upper()
    
    if st.button("Salva nel Database Cloud", use_container_width=True):
        if n_nome and final_sq and n_num:
            success = save_player_to_roster(user_id, n_num, n_nome, n_ruolo, final_sq)
            if success:
                st.toast("Giocatore salvato!", icon="✅")
                st.rerun()
# --- HEADER & PUNTEGGIO ---
st.title(f"🏀 {tipo_sessione}")
all_teams = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []

if tipo_sessione == "Partita 🏟️":
    c_s1, c_s2, c_s3 = st.columns([2, 1, 2])
    t_home = c_s1.selectbox("Tua Squadra:", all_teams, key="h_sel") if all_teams else c_s1.text_input("Tua Squadra:", "HOME").upper()
    away_opts = [t for t in all_teams if t != t_home]
    t_away_sel = c_s3.selectbox("Avversari:", away_opts + ["+ ALTRA..."], key="a_sel")
    t_away = c_s3.text_input("Nome Avversario:", "AVVERSARI").upper() if t_away_sel == "+ ALTRA..." else t_away_sel
    
    df_all = pd.DataFrame(st.session_state.shots) if st.session_state.shots else pd.DataFrame()
    pts_h = df_all[df_all['team'] == t_home]['punti'].sum() if not df_all.empty else 0
    pts_a = df_all[df_all['team'] == "AVVERSARI"]['punti'].sum() if not df_all.empty else 0
    c_s2.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{pts_h}-{pts_a}</h1>", unsafe_allow_html=True)
else:
    t_home = st.selectbox("Squadra in Allenamento:", all_teams) if all_teams else st.text_input("Squadra:", "TEAM").upper()
    t_away = "N/A"

st.divider()

# --- SELEZIONE GIOCATORE ---
df_team = df_roster[df_roster['squadra'] == t_home].copy() if not df_roster.empty else pd.DataFrame()
if not df_team.empty:
    df_team['display'] = df_team['numero'].astype(str) + " - " + df_team['nome'] + " (" + df_team['ruolo'] + ")"
    giocatori_dict = dict(zip(df_team['display'], df_team['nome']))
    lista_giocatori = sorted(giocatori_dict.keys())
else:
    lista_giocatori, giocatori_dict = [], {}

cols = st.columns([1.5, 1.5, 1])
if tipo_sessione == "Partita 🏟️":
    quintetto = cols[0].multiselect("5 in Campo:", lista_giocatori, max_selections=5)
else:
    cols[0].info("Modalità Allenamento: +/- disattivato")
    quintetto = []

p_name = giocatori_dict.get(cols[1].selectbox("Giocatore:", lista_giocatori))
p_time = cols[2].text_input("Minuto/Note:", "00:00")

# --- AZIONI ---
tabs = ["🎯 Tiri", "📊 Stats Extra"]
if tipo_sessione == "Partita 🏟️": tabs.append("🚩 Avversari")
t_list = st.tabs(tabs)

with t_list[0]:
    esito = st.radio("Esito:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)
    is_tl = "TL" in esito
    cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))
    s_plot = [s for s in st.session_state.shots if s.get('team') == t_home and s.get('type') in ['2PT', '3PT', 'TL']]
    st.plotly_chart(create_basketball_court(cur_x, cur_y, s_plot), use_container_width=True)

    if st.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
        s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
        made = "Segnato" in esito
        pts = 1 if is_tl else (int(s_type[0]) if made else 0)
        in_campo = [giocatori_dict[p] for p in quintetto]
        st.session_state.shots.append({"team": t_home, "player": p_name, "tempo": p_time, "x": cur_x, "y": cur_y, "made": made, "type": s_type, "punti": pts, "on_court": in_campo})
        save_shots(user_id, st.session_state.shots); st.rerun()

with t_list[1]:
    def reg_e(tipo):
        in_campo = [giocatori_dict[p] for p in quintetto]
        st.session_state.shots.append({"team": t_home, "player": p_name, "tempo": p_time, "x": 0, "y": 0, "made": False, "type": tipo, "punti": 0, "on_court": in_campo})
        save_shots(user_id, st.session_state.shots); st.rerun()
    c1, c2, c3 = st.columns(3)
    if c1.button("🤝 Assist"): reg_e("AST")
    if c2.button("🏀 Rimb. Off"): reg_e("OREB")
    if c3.button("🛡️ Rimb. Dif"): reg_e("DREB")
    if st.button("↩️ Undo", use_container_width=True):
        if st.session_state.shots: st.session_state.shots.pop(); delete_last_shot(user_id); st.rerun()

if tipo_sessione == "Partita 🏟️":
    with t_list[2]:
        st.subheader(f"Punti subiti da {t_away}")
        ca1, ca2, ca3 = st.columns(3)
        def reg_o(p):
            in_campo = [giocatori_dict[p] for p in quintetto]
            st.session_state.shots.append({"team": "AVVERSARI", "player": "OPP", "tempo": p_time, "x": 0, "y": 0, "made": True, "type": "OPP_PTS", "punti": p, "on_court": in_campo})
            save_shots(user_id, st.session_state.shots); st.rerun()
        if ca1.button("+1 Libero"): reg_o(1)
        if ca2.button("+2 Canestro"): reg_o(2)
        if ca3.button("+3 Tripla"): reg_o(3)

# --- BOX SCORE ---
if st.session_state.shots:
    df_all = pd.DataFrame(st.session_state.shots)
    df_t = df_all[df_all['team'] == t_home]
    if not df_t.empty:
        st.divider()
        st.subheader("📊 Box Score")
        rows = []
        pm_map = {p: 0 for p in df_t['player'].unique()}
        if 'on_court' in df_all.columns:
            for _, r in df_all.iterrows():
                if isinstance(r.get('on_court'), list) and r.get('punti', 0) > 0:
                    for p_on in r['on_court']:
                        if p_on in pm_map: pm_map[p_on] += r['punti'] if r['team'] == t_home else -r['punti']

        for p in df_t['player'].unique():
            p_df = df_t[df_t['player'] == p]
            info = df_team[df_team['nome'] == p]
            fga = len(p_df[p_df['type'].isin(['2PT', '3PT'])])
            fgm = p_df[p_df['type'].isin(['2PT', '3PT'])]['made'].sum()
            fg3m = p_df[(p_df['type'] == '3PT') & (p_df['made'] == True)]['made'].count()
            efg = ((fgm + 0.5 * fg3m) / fga * 100) if fga > 0 else 0
            rows.append({
                "N°": info['numero'].values[0] if not info.empty else "-",
                "Giocatore": p, "PTS": p_df['punti'].sum(),
                "2PT": f"{p_df[p_df['type']=='2PT']['made'].sum()}/{len(p_df[p_df['type']=='2PT'])}",
                "3PT": f"{p_df[p_df['type']=='3PT']['made'].sum()}/{len(p_df[p_df['type']=='3PT'])}",
                "REB": len(p_df[p_df['type'].isin(['OREB', 'DREB'])]),
                "AST": len(p_df[p_df['type'] == "AST"]),
                "+/-": pm_map.get(p, 0) if tipo_sessione == "Partita 🏟️" else "-",
                "eFG%": f"{efg:.1f}%"
            })
        st.dataframe(pd.DataFrame(rows).sort_values(by="PTS", ascending=False), use_container_width=True)
