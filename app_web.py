import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster, delete_last_shot
from reports import generate_player_report
from court_graphics import create_basketball_court

st.set_page_config(page_title="Scout Basket PRO", layout="wide")

if not check_password(): st.stop()
user_id = st.session_state.get("username")
if 'shots' not in st.session_state: st.session_state.shots = load_shots(user_id)
df_roster = load_roster(user_id)

# --- SIDEBAR ---
st.sidebar.title(f"👤 Coach: {user_id}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

st.sidebar.divider()

st.sidebar.subheader("📂 Importa Roster")
up_file = st.sidebar.file_uploader("Carica .csv (colonne: numero, nome, ruolo, squadra)", type=["csv"])
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
    new_num = c_num.text_input("N°:")
    new_ruolo = c_ruolo.selectbox("Ruolo:", ["Playmaker (PG)", "Guardia (SG)", "Ala Piccola (SF)", "Ala Grande (PF)", "Centro (C)"])
    new_n = st.text_input("Nome Giocatore:").upper()
    
    if st.button("Salva nel Roster"):
        if new_n and final_sq and new_num:
            r_sigla = new_ruolo.split("(")[1].replace(")", "") # Estrae PG, SG, ecc.
            save_player_to_roster(user_id, new_num, new_n, r_sigla, final_sq)
            st.rerun()

st.sidebar.divider()
if st.sidebar.button("🚨 Reset Tiri Sessione"):
    st.session_state.shots = []
    save_shots(user_id, [])
    st.rerun()

# --- MAIN APP ---
st.title("🏀 Scout Basket PRO")
c_top1, c_top2 = st.columns(2)
tipo = c_top1.selectbox("Sessione:", ["Allenamento", "Partita"])
teams_list = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
t_home = c_top2.selectbox("Squadra Attiva:", teams_list) if teams_list else c_top2.text_input("Squadra:", "TEAM").upper()

st.divider()

# Preparazione Dropdown con Ricerca Rapida (Num - Nome)
df_team = df_roster[df_roster['squadra'] == t_home].copy() if not df_roster.empty else pd.DataFrame()
if not df_team.empty:
    df_team['display'] = df_team['numero'].astype(str) + " - " + df_team['nome'] + " (" + df_team['ruolo'] + ")"
    giocatori_dict = dict(zip(df_team['display'], df_team['nome'])) # Mappa la stringa visiva al nome reale
    lista_dropdown = sorted(giocatori_dict.keys())
else:
    lista_dropdown, giocatori_dict = [], {}

# Input
col_p, col_m = st.columns([2, 1])
p_display = col_p.selectbox("Giocatore (Cerca n° o nome):", lista_dropdown) if lista_dropdown else None
p_name = giocatori_dict.get(p_display, col_p.text_input("Nome:", "PLAYER")) if p_display else col_p.text_input("Nome:", "PLAYER")
p_time = col_m.text_input("Minuto:", "00:00")

# --- TABS ---
tab_tiri, tab_extra = st.tabs(["🎯 Tiri", "📊 Altre Statistiche"])

with tab_tiri:
    esito = st.radio("Esito Tiro:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)
    is_tl = "TL" in esito
    cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))
    
    shots_to_plot = [s for s in st.session_state.shots if s['type'] in ['2PT', '3PT', 'TL']]
    st.plotly_chart(create_basketball_court(cur_x, cur_y, shots_to_plot), use_container_width=True)

    b1, b2 = st.columns([4, 1])
    if b1.button("✅ REGISTRA TIRO", type="primary", use_container_width=True):
        s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
        made = "Segnato" in esito
        pts = 1 if is_tl else (int(s_type[0]) if made else 0)
        st.session_state.shots.append({"team": t_home, "player": p_name, "tempo": p_time, "x": cur_x, "y": cur_y, "made": made, "type": s_type, "punti": pts})
        save_shots(user_id, st.session_state.shots)
        st.rerun()
    if b2.button("↩️ Undo", use_container_width=True):
        if st.session_state.shots:
            st.session_state.shots.pop()
            delete_last_shot(user_id)
            st.rerun()

with tab_extra:
    def registra_extra(tipo_azione):
        st.session_state.shots.append({"team": t_home, "player": p_name, "tempo": p_time, "x": 0, "y": 0, "made": False, "type": tipo_azione, "punti": 0})
        save_shots(user_id, st.session_state.shots)
        st.rerun()

    ce1, ce2, ce3 = st.columns(3)
    if ce1.button("🤝 Assist", use_container_width=True): registra_extra("AST")
    if ce2.button("🏀 Rimb. Off", use_container_width=True): registra_extra("OREB")
    if ce3.button("🛡️ Rimb. Dif", use_container_width=True): registra_extra("DREB")
    
    ce4, ce5, ce6 = st.columns(3)
    if ce4.button("❌ Palla Persa", use_container_width=True): registra_extra("TOV")
    if ce5.button("🥷 Recuperata", use_container_width=True): registra_extra("STL")
    if ce6.button("⛔ Stoppata", use_container_width=True): registra_extra("BLK")

    ce7, ce8, ce9 = st.columns(3)
    if ce7.button("🛑 Fallo Commesso", use_container_width=True): registra_extra("FC")
    if ce8.button("🤕 Fallo Subito", use_container_width=True): registra_extra("FS")
    if ce9.button("↩️ Annulla Ultimo", use_container_width=True):
        if st.session_state.shots:
            st.session_state.shots.pop()
            delete_last_shot(user_id)
            st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    df_t = df[df['team'] == t_home]
    
    if not df_t.empty:
        st.divider()
        st.header(f"📊 Report {t_home}")
        
        # BOX SCORE INDIVIDUALE AGGIORNATO (Con N° e Ruolo)
        st.subheader("👤 Box Score Individuale")
        def get_shot_ratio(player_df, shot_type):
            sub = player_df[player_df['type'] == shot_type]
            return f"{sub['made'].sum()}/{len(sub)}" if not sub.empty else "0/0"

        rows = []
        for player in df_t['player'].unique():
            p_df = df_t[df_t['player'] == player]
            
            # Recupera n° e ruolo dal roster
            info_roster = df_team[df_team['nome'] == player]
            p_num = info_roster['numero'].values[0] if not info_roster.empty else "-"
            p_ruolo = info_roster['ruolo'].values[0] if not info_roster.empty else "-"
            
            fga_df = p_df[p_df['type'].isin(['2PT', '3PT'])]
            fga = len(fga_df)
            fgm = fga_df['made'].sum()
            fg3m = p_df[(p_df['type'] == '3PT') & (p_df['made'] == True)]['made'].count()
            fta = len(p_df[p_df['type'] == 'TL'])
            pts = p_df['punti'].sum()
            
            efg = ((fgm + 0.5 * fg3m) / fga * 100) if fga > 0 else 0
            
            rows.append({
                "N°": p_num,
                "Ruolo": p_ruolo,
                "Giocatore": player,
                "PTS": pts,
                "2PT": get_shot_ratio(p_df, "2PT"),
                "3PT": get_shot_ratio(p_df, "3PT"),
                "TL": get_shot_ratio(p_df, "TL"),
                "REB": len(p_df[p_df['type'].isin(['OREB', 'DREB'])]),
                "AST": len(p_df[p_df['type'] == 'AST']),
                "STL": len(p_df[p_df['type'] == 'STL']),
                "TOV": len(p_df[p_df['type'] == 'TOV']),
                "BLK": len(p_df[p_df['type'] == 'BLK']),
                "FC": len(p_df[p_df['type'] == 'FC']),
                "eFG%": f"{efg:.1f}%"
            })
            
        st.dataframe(pd.DataFrame(rows).sort_values(by="PTS", ascending=False), use_container_width=True)

        d1, d2 = st.columns(2)
        d1.download_button("Scarica Dati Grezzi (CSV)", df.to_csv(index=False).encode('utf-8'), "scout_completo.csv", use_container_width=True)
