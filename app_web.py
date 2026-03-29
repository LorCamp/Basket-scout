import streamlit as st
import pandas as pd
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# Controllo Accesso
if not check_password():
    st.stop()

# Benvenuto
st.sidebar.write(f"👤 Coach: **{st.session_state.username}**")
if st.sidebar.button("Log Out"):
    st.session_state.authenticated = False
    st.rerun()

# Caricamento Dati Utente
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

df_roster = load_roster()

# --- SIDEBAR: CARICAMENTO ROSTER PERSONALE ---
st.sidebar.divider()
st.sidebar.subheader("📂 Carica il tuo Roster")
up_file = st.sidebar.file_uploader("CSV (nome, squadra)", type=["csv"])
if up_file:
    df_up = pd.read_csv(up_file)
    df_up.to_csv(f"data_users/{st.session_state.username}/roster.csv", index=False)
    st.sidebar.success("Roster aggiornato!")
    st.rerun()

# --- MAIN APP ---
st.title("🏀 Scout Basket PRO")

tipo_sessione = st.selectbox("Tipo Sessione:", ["Allenamento", "Partita"])

col_t1, col_t2 = st.columns(2)
teams_in_roster = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
t_home = col_t1.selectbox("Squadra Casa (Noi):", teams_in_roster) if teams_in_roster else col_t1.text_input("Squadra Casa:", "CASA").upper()
t_away = None
if tipo_sessione == "Partita":
    t_away = col_t2.text_input("Squadra Ospite:", "OSPITE").upper()

st.divider()

# Selezione Azione
c_team, c_player, c_time = st.columns([1, 1.5, 1])
target_team = c_team.radio("Team tira:", [t_home, t_away] if t_away else [t_home], horizontal=True)

giocatori_filtrati = []
if not df_roster.empty:
    giocatori_filtrati = df_roster[df_roster['squadra'] == target_team]['nome'].tolist()

if giocatori_filtrati:
    p_name = c_player.selectbox("Giocatore:", sorted(giocatori_filtrati))
else:
    p_name = c_player.text_input("Nome Giocatore:", "TEAM")

p_time = c_time.text_input("Minuto:", "00:00") if tipo_sessione == "Partita" else "N/A"
esito = st.radio("Risultato:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Posizionamento
is_tl = "TL" in esito
if is_tl:
    cur_x, cur_y = 0, 142
else:
    cur_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=10)
    cur_y = st.slider("Distanza dal fondo", -40, 420, 100, step=10)

fig = create_basketball_court(cur_x, cur_y, st.session_state.shots)
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})

if st.button("✅ REGISTRA AZIONE", type="primary", use_container_width=True):
    s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
    made = "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "sessione": tipo_sessione, "team": target_team, "player": p_name,
        "tempo": p_time, "x": cur_x, "y": cur_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    # 1. LIVE SCORE COMPARISON
    st.subheader("🏆 Punteggio Live")
    s1, s2 = st.columns(2)
    s1.metric(t_home, f"{df[df['team']==t_home]['punti'].sum()} pts")
    if t_away:
        s2.metric(t_away, f"{df[df['team']==t_away]['punti'].sum()} pts")

    # 2. STATS SQUADRA SELEZIONATA
    df_team = df[df['team'] == target_team]
    if not df_team.empty:
        st.write(f"📊 **Dettaglio Percentuali: {target_team}**")
        m1, m2, m3 = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_team[df_team['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            perc = f"{(m/tot*100):.1f}%" if tot > 0 else "0%"
            [m1, m2, m3][i].metric(t, f"{m}/{tot}", perc)

        # 3. TABELLA GIOCATORI
        st.write("👤 **Performance Giocatori**")
        stats = df_team.groupby('player').agg(
            PTS=('punti', 'sum'),
            Segnati=('made', 'sum'),
            Totali=('made', 'count')
        )
        stats['%'] = (stats['Segnati'] / stats['Totali'] * 100).round(1).astype(str) + '%'
        st.table(stats.sort_values(by='PTS', ascending=False))

    # --- EXPORT ---
    st.divider()
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    exp_col1.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "scout.csv", use_container_width=True)
    try:
        pdf_data = generate_player_report(df, t_home)
        exp_col2.download_button("📄 PDF", pdf_data, f"Report_{t_home}.pdf", "application/pdf", use_container_width=True)
    except:
        exp_col2.error("Errore PDF")
    if exp_col3.button("⬅️ Cancella Ultimo", use_container_width=True):
        st.session_state.shots.pop()
        save_shots(st.session_state.shots)
        st.rerun()
