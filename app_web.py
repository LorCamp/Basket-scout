import streamlit as st
import pandas as pd
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# 1. Controllo Accesso (Deve essere la prima cosa)
if not check_password():
    st.stop()

# 2. Inizializzazione sicura dei dati utente
# Usiamo .get() per evitare l'AttributeError se non loggato correttamente
user_id = st.session_state.get("username", "Ospite")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

df_roster = load_roster()

# --- SIDEBAR ---
st.sidebar.title(f"👤 Coach: {user_id}")
if st.sidebar.button("Log Out"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📂 Carica Roster")
up_file = st.sidebar.file_uploader("CSV (nome, squadra)", type=["csv"])
if up_file:
    df_up = pd.read_csv(up_file)
    # Salvataggio nella cartella specifica dell'utente
    df_up.to_csv(f"data_users/{user_id}/roster.csv", index=False)
    st.sidebar.success("Roster caricato!")
    st.rerun()

if st.sidebar.button("🚨 Reset Tiri"):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

# --- MAIN APP ---
st.title("🏀 Scout Basket PRO")
tipo_sessione = st.selectbox("Tipo Sessione:", ["Allenamento", "Partita"])

col_t1, col_t2 = st.columns(2)
teams_in_roster = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
t_home = col_t1.selectbox("Squadra Casa:", teams_in_roster) if teams_in_roster else col_t1.text_input("Squadra Casa:", "CASA").upper()
t_away = col_t2.text_input("Ospite:", "OSPITE").upper() if tipo_sessione == "Partita" else None

st.divider()

# Selezione Azione
c_team, c_player, c_time = st.columns([1, 1.5, 1])
target_team = c_team.radio("Tira:", [t_home, t_away] if t_away else [t_home], horizontal=True)

giocatori = df_roster[df_roster['squadra'] == target_team]['nome'].tolist() if not df_roster.empty else []
p_name = c_player.selectbox("Giocatore:", sorted(giocatori)) if giocatori else c_player.text_input("Giocatore:", "TEAM")
p_time = c_time.text_input("Minuto:", "00:00") if tipo_sessione == "Partita" else "N/A"

esito = st.radio("Risultato:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Posizionamento (Anti-Rettangolo)
is_tl = "TL" in esito
cur_x, cur_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, 10), st.slider("Y", -40, 420, 100, 10))

fig = create_basketball_court(cur_x, cur_y, st.session_state.shots)
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})

if st.button("✅ REGISTRA AZIONE", type="primary", use_container_width=True):
    s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
    made = "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "team": target_team, "player": p_name, "tempo": p_time,
        "x": cur_x, "y": cur_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    # Live Score
    st.subheader("🏆 Punteggio")
    s1, s2 = st.columns(2)
    s1.metric(t_home, f"{df[df['team']==t_home]['punti'].sum()} pts")
    if t_away: s2.metric(t_away, f"{df[df['team']==t_away]['punti'].sum()} pts")

    # Stats Squadra & Giocatori
    df_team = df[df['team'] == target_team]
    if not df_team.empty:
        st.write(f"📊 **Dettaglio {target_team}:**")
        m1, m2, m3 = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_team[df_team['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            perc = f"{(m/tot*100):.1f}%" if tot > 0 else "0%"
            [m1, m2, m3][i].metric(t, f"{m}/{tot}", perc)

        stats = df_team.groupby('player').agg(PTS=('punti', 'sum'), Seg=('made', 'sum'), Tot=('made', 'count'))
        stats['%'] = (stats['Seg']/stats['Tot']*100).round(1).astype(str)+'%'
        st.table(stats.sort_values(by='PTS', ascending=False))

    # Export
    exp1, exp2 = st.columns(2)
    exp1.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "scout.csv")
    try:
        pdf_data = generate_player_report(df, t_home)
        exp2.download_button("📄 PDF", pdf_data, "Report.pdf", "application/pdf")
    except: st.error("Errore PDF")
