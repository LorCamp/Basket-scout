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
up_file = st.sidebar.file_uploader("Carica .csv (colonne: nome, squadra)", type=["csv"])
if up_file:
    df_up = pd.read_csv(up_file)
    df_up.columns = [c.lower() for c in df_up.columns]
    path_r = f"data_users/{user_id}/roster.csv"
    os.makedirs(os.path.dirname(path_r), exist_ok=True)
    df_up.to_csv(path_r, index=False)
    st.sidebar.success("Roster caricato!")
    st.rerun()

with st.sidebar.expander("➕ Aggiungi Giocatore Manuale"):
    teams_db = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
    sq_in = st.selectbox("Squadra:", teams_db + ["+ NUOVA..."])
    final_sq = st.text_input("Nome Squadra:").upper() if sq_in == "+ NUOVA..." else sq_in
    new_n = st.text_input("Nome Giocatore:").upper()
    if st.button("Salva nel Roster"):
        if new_n and final_sq:
            save_player_to_roster(user_id, new_n, final_sq)
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

# Input Giocatore e Tempo
col_p, col_m = st.columns([2, 1])
giocatori = df_roster[df_roster['squadra'] == t_home]['nome'].tolist() if not df_roster.empty else []
p_name = col_p.selectbox("Giocatore Selezionato:", sorted(giocatori)) if giocatori else col_p.text_input("Nome:", "PLAYER")
p_time = col_m.text_input("Minuto:", "00:00")

# --- PANNELLO REGISTRAZIONE AZIONI (TABS) ---
tab_tiri, tab_extra = st.tabs(["🎯 Tiri", "📊 Altre Statistiche"])

# TAB 1: TIRI
with tab_tiri:
    esito = st.radio("Esito Tiro:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)
    is_tl = "TL" in esito
    cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))
    
    # Filtra solo i tiri per il grafico
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
    if b2.button("↩️ Undo", help="Elimina ultimo evento", key="undo_tiro"):
        if st.session_state.shots:
            st.session_state.shots.pop()
            delete_last_shot(user_id)
            st.rerun()

# TAB 2: ALTRE STATISTICHE E FALLI
with tab_extra:
    st.write(f"Registra azione per **{p_name}** al minuto **{p_time}**:")
    
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

# --- STATISTICHE E PLAY-BY-PLAY ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    df_t = df[df['team'] == t_home]
    
    if not df_t.empty:
        st.divider()
        st.header(f"📊 Report {t_home}")
        
        # 1. STATISTICHE TOTALI DI SQUADRA (Compresi i Falli)
        st.subheader("🏢 Totali di Squadra")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PUNTI TOTALI", df_t['punti'].sum())
        
        def team_perc(shot_type):
            sub = df_t[df_t['type'] == shot_type]
            if sub.empty: return "0/0 (0%)"
            m = sub['made'].sum()
            t = len(sub)
            return f"{m}/{t} ({(m/t*100):.1f}%)"

        c2.metric("Tiri da 2", team_perc("2PT"))
        c3.metric("Tiri da 3", team_perc("3PT"))
        c4.metric("Tiri Liberi", team_perc("TL"))

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Assist Totali", len(df_t[df_t['type'] == 'AST']))
        c6.metric("Rimbalzi (Off / Dif)", f"{len(df_t[df_t['type'] == 'OREB'])} / {len(df_t[df_t['type'] == 'DREB'])}")
        c7.metric("Palle Perse / Rec", f"{len(df_t[df_t['type'] == 'TOV'])} / {len(df_t[df_t['type'] == 'STL'])}")
        c8.metric("Falli (Commessi/Subiti)", f"{len(df_t[df_t['type'] == 'FC'])} / {len(df_t[df_t['type'] == 'FS'])}")
        
        # 2. BOX SCORE INDIVIDUALE (Compresi FC e FS)
        st.subheader("👤 Box Score Individuale (Avanzato)")
        def get_shot_ratio(player_df, shot_type):
            sub = player_df[player_df['type'] == shot_type]
            return f"{sub['made'].sum()}/{len(sub)}" if not sub.empty else "0/0"

        rows = []
        for player in df_t['player'].unique():
            p_df = df_t[df_t['player'] == player]
            
            fga_df = p_df[p_df['type'].isin(['2PT', '3PT'])]
            fga = len(fga_df)
            fgm = fga_df['made'].sum()
            fg3m = p_df[(p_df['type'] == '3PT') & (p_df['made'] == True)]['made'].count()
            fta = len(p_df[p_df['type'] == 'TL'])
            pts = p_df['punti'].sum()
            
            efg = ((fgm + 0.5 * fg3m) / fga * 100) if fga > 0 else 0
            ts = (pts / (2 * (fga + 0.44 * fta)) * 100) if (fga + fta) > 0 else 0
            
            rows.append({
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
                "FS": len(p_df[p_df['type'] == 'FS']),
                "eFG%": f"{efg:.1f}%",
                "TS%": f"{ts:.1f}%"
            })
            
        st.dataframe(pd.DataFrame(rows).sort_values(by="PTS", ascending=False), use_container_width=True)

        # 3. PLAY-BY-PLAY
        st.subheader("📜 Play-by-Play")
        pbp_data = []
        for s in reversed(st.session_state.shots):
            if s['team'] != t_home: continue # Mostra solo azioni della squadra attiva
            
            azione = ""
            if s['type'] in ['2PT', '3PT', 'TL']:
                azione = f"{s['type']} {'Segnato ✅' if s['made'] else 'Sbagliato ❌'}"
            elif s['type'] == 'AST': azione = "Assist 🤝"
            elif s['type'] == 'OREB': azione = "Rimbalzo Offensivo 🏀"
            elif s['type'] == 'DREB': azione = "Rimbalzo Difensivo 🛡️"
            elif s['type'] == 'TOV': azione = "Palla Persa ❌"
            elif s['type'] == 'STL': azione = "Palla Recuperata 🥷"
            elif s['type'] == 'BLK': azione = "Stoppata ⛔"
            elif s['type'] == 'FC': azione = "Fallo Commesso 🛑"
            elif s['type'] == 'FS': azione = "Fallo Subito 🤕"
            
            pbp_data.append({
                "Min": s['tempo'],
                "Giocatore": s['player'],
                "Evento": azione,
                "Pts": s['punti']
            })
        
        st.dataframe(pd.DataFrame(pbp_data), use_container_width=True)

        # DOWNLOADS
        d1, d2 = st.columns(2)
        d1.download_button("Scarica Dati Grezzi (CSV)", df.to_csv(index=False).encode('utf-8'), "scout_completo.csv", use_container_width=True)
        try:
            pdf_data = generate_player_report(df, t_home)
            d2.download_button("Scarica Report (PDF)", pdf_data, "Report.pdf", "application/pdf", use_container_width=True)
        except: pass
