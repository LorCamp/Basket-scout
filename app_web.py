import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster, delete_last_shot
from reports import generate_player_report
from court_graphics import create_basketball_court

st.set_page_config(page_title="Scout Basket PRO", layout="wide")

# 1. AUTENTICAZIONE
if not check_password():
    st.stop()

user_id = st.session_state.get("username")
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots(user_id)
df_roster = load_roster(user_id)

# --- SIDEBAR ---
st.sidebar.title(f"👤 Coach: {user_id}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📂 Importa Roster")
up_file = st.sidebar.file_uploader("Carica .csv (numero, nome, ruolo, squadra)", type=["csv"])
if up_file:
    df_up = pd.read_csv(up_file)
    df_up.columns = [c.lower() for c in df_up.columns]
    path_r = f"data_users/{user_id}/roster.csv"
    os.makedirs(os.path.dirname(path_r), exist_ok=True)
    df_up.to_csv(path_r, index=False)
    st.sidebar.success("Roster caricato!")
    st.rerun()

with st.sidebar.expander("➕ Aggiungi Giocatore"):
    teams_db = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
    sq_in = st.selectbox("Squadra:", teams_db + ["+ NUOVA..."])
    final_sq = st.text_input("Nome Squadra:").upper() if sq_in == "+ NUOVA..." else sq_in
    c_num, c_ruolo = st.columns([1, 2])
    n_num = c_num.text_input("N°:")
    n_ruolo = c_ruolo.selectbox("Ruolo:", ["PG", "SG", "SF", "PF", "C"])
    n_nome = st.text_input("Nome Giocatore:").upper()
    if st.button("Salva nel Roster"):
        if n_nome and final_sq and n_num:
            save_player_to_roster(user_id, n_num, n_nome, n_ruolo, final_sq)
            st.rerun()

# --- MAIN APP ---
st.title("🏀 Scout Basket PRO")
c_top1, c_top2 = st.columns(2)
tipo = c_top1.selectbox("Sessione:", ["Allenamento", "Partita"])
teams_list = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
t_home = c_top2.selectbox("Squadra Attiva:", teams_list) if teams_list else c_top2.text_input("Squadra:", "TEAM").upper()

st.divider()

# Preparazione Dati Giocatori
df_team = df_roster[df_roster['squadra'] == t_home].copy() if not df_roster.empty else pd.DataFrame()
if not df_team.empty:
    df_team['display'] = df_team['numero'].astype(str) + " - " + df_team['nome'] + " (" + df_team['ruolo'] + ")"
    giocatori_dict = dict(zip(df_team['display'], df_team['nome']))
    lista_giocatori = sorted(giocatori_dict.keys())
else:
    lista_giocatori, giocatori_dict = [], {}

# --- GESTIONE QUINTETTO (Per +/-) ---
with st.expander("👥 Quintetto in campo (per +/-)", expanded=False):
    quintetto = st.multiselect("Seleziona i 5 giocatori in campo:", lista_giocatori, max_selections=5)
    st.caption("Il Plus/Minus verrà calcolato solo per i giocatori selezionati qui quando viene segnato un canestro.")

# --- SELEZIONE GIOCATORE ATTIVO ---
col_p, col_m = st.columns([2, 1])
if lista_giocatori:
    p_display = col_p.selectbox("Giocatore (Cerca n° o nome):", lista_giocatori)
    p_name = giocatori_dict.get(p_display)
else:
    p_name = col_p.text_input("Nome Giocatore (Roster Vuoto):", "PLAYER").upper()

p_time = col_m.text_input("Minuto:", "00:00")

# --- TABS AZIONI ---
tab_tiri, tab_extra = st.tabs(["🎯 Tiri", "📊 Altre Statistiche"])

with tab_tiri:
    esito = st.radio("Esito:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)
    is_tl = "TL" in esito
    cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))
    
    shots_to_plot = [s for s in st.session_state.shots if s['type'] in ['2PT', '3PT', 'TL']]
    st.plotly_chart(create_basketball_court(cur_x, cur_y, shots_to_plot), use_container_width=True)

    if st.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
        s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
        made = "Segnato" in esito
        pts = 1 if is_tl else (int(s_type[0]) if made else 0)
        
        # Salviamo anche chi era in campo per il +/-
        in_campo = [giocatori_dict[p] for p in quintetto] if quintetto else []
        
        st.session_state.shots.append({
            "team": t_home, "player": p_name, "tempo": p_time, "x": cur_x, "y": cur_y, 
            "made": made, "type": s_type, "punti": pts, "on_court": in_campo
        })
        save_shots(user_id, st.session_state.shots)
        st.rerun()

with tab_extra:
    def registra_extra(tipo_azione):
        in_campo = [giocatori_dict[p] for p in quintetto] if quintetto else []
        st.session_state.shots.append({
            "team": t_home, "player": p_name, "tempo": p_time, "x": 0, "y": 0, 
            "made": False, "type": tipo_azione, "punti": 0, "on_court": in_campo
        })
        save_shots(user_id, st.session_state.shots)
        st.rerun()

    c1, c2, c3 = st.columns(3)
    if c1.button("🤝 Assist", use_container_width=True): registra_extra("AST")
    if c2.button("🏀 Rimbalzo Off", use_container_width=True): registra_extra("OREB")
    if c3.button("🛡️ Rimbalzo Dif", use_container_width=True): registra_extra("DREB")
    c4, c5, c6 = st.columns(3)
    if c4.button("❌ Palla Persa", use_container_width=True): registra_extra("TOV")
    if c5.button("🥷 Recuperata", use_container_width=True): registra_extra("STL")
    if c6.button("🛑 Fallo Commesso", use_container_width=True): registra_extra("FC")
    if st.button("↩️ Undo (Annulla Ultimo)", use_container_width=True):
        if st.session_state.shots:
            st.session_state.shots.pop()
            delete_last_shot(user_id)
            st.rerun()

# --- BOX SCORE E CALCOLO +/- ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    df_t = df[df['team'] == t_home]
    
    if not df_t.empty:
        st.divider()
        st.subheader("👤 Box Score Individuale")
        
        rows = []
        # Calcolo +/-: Per ogni canestro segnato, i giocatori "on_court" prendono punti
        plus_minus_map = {p: 0 for p in df_t['player'].unique()}
        for _, row in df.iterrows():
            if row['punti'] > 0 and isinstance(row['on_court'], list):
                for p_on in row['on_court']:
                    if p_on in plus_minus_map:
                        plus_minus_map[p_on] += row['punti'] if row['team'] == t_home else -row['punti']

        for player in df_t['player'].unique():
            p_df = df_t[df_t['player'] == player]
            info = df_team[df_team['nome'] == player]
            
            rows.append({
                "N°": info['numero'].values[0] if not info.empty else "-",
                "Ruolo": info['ruolo'].values[0] if not info.empty else "-",
                "Giocatore": player,
                "PTS": p_df['punti'].sum(),
                "REB": len(p_df[p_df['type'].isin(['OREB', 'DREB'])]),
                "AST": len(p_df[p_df['type'] == 'AST']),
                "FC": len(p_df[p_df['type'] == 'FC']),
                "+/-": plus_minus_map.get(player, 0)
            })
            
        st.dataframe(pd.DataFrame(rows).sort_values(by="PTS", ascending=False), use_container_width=True)

        if st.sidebar.button("🚨 Reset Totale"):
            st.session_state.shots = []
            save_shots(user_id, [])
            st.rerun()
