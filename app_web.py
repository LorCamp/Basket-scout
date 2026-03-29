import streamlit as st
import pandas as pd
import os
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# 1. BLOCCO ACCESSO (Indispensabile come prima riga)
if not check_password():
    st.stop()

# 2. GESTIONE SICURA DELLE VARIABILI DI SESSIONE
# Usiamo .get() per evitare l'AttributeError se l'app si aggiorna bruscamente
user_id = st.session_state.get("username")

if not user_id:
    st.warning("Problema con la sessione. Per favore effettua di nuovo il login.")
    if st.button("Torna al Login"):
        st.session_state.authenticated = False
        st.rerun()
    st.stop()

# 3. CARICAMENTO DATI (Ora siamo sicuri che user_id esiste)
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

df_roster = load_roster()

# --- SIDEBAR ---
st.sidebar.title(f"👤 Coach: {user_id}")

if st.sidebar.button("Logout"):
    # Pulizia totale per evitare residui tra un utente e l'altro
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.divider()

# AGGIUNTA GIOCATORE
with st.sidebar.expander("➕ Aggiungi Giocatore"):
    teams_in_db = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []
    sq_input = st.selectbox("Squadra:", teams_in_db + ["+ NUOVA..."])
    final_sq = st.text_input("Nome Nuova Squadra:").upper() if sq_input == "+ NUOVA..." else sq_input
    new_n = st.text_input("Nome Giocatore:").upper()
    if st.button("Salva Giocatore"):
        if new_n and final_sq:
            save_player_to_roster(new_n, final_sq)
            st.rerun()

st.sidebar.divider()

# CARICAMENTO CSV
up_file = st.sidebar.file_uploader("Carica CSV Roster", type=["csv"])
if up_file:
    df_up = pd.read_csv(up_file)
    # Assicurati che il percorso esista
    os.makedirs(f"data_users/{user_id}", exist_ok=True)
    df_up.to_csv(f"data_users/{user_id}/roster.csv", index=False)
    st.sidebar.success("Roster caricato!")
    st.rerun()

# --- MAIN INTERFACE (Tiri e Stats) ---
st.title("🏀 Scout Basket PRO")
tipo_sessione = st.selectbox("Tipo Sessione:", ["Allenamento", "Partita"])

col_t1, col_t2 = st.columns(2)
teams_in_roster = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []

t_home = col_t1.selectbox("Squadra Casa:", teams_in_roster) if teams_in_roster else col_t1.text_input("Squadra Casa:", "CASA").upper()
t_away = col_t2.text_input("Ospite:", "OSPITE").upper() if tipo_sessione == "Partita" else None

st.divider()

# Logica di selezione azione
c_team, c_player, c_time = st.columns([1, 1.5, 1])
target_team = c_team.radio("Tira:", [t_home, t_away] if t_away else [t_home], horizontal=True)

giocatori_filtrati = df_roster[df_roster['squadra'] == target_team]['nome'].tolist() if not df_roster.empty else []
p_name = c_player.selectbox("Giocatore:", sorted(giocatori_filtrati)) if giocatori_filtrati else c_player.text_input("Giocatore:", "TEAM")
p_time = c_time.text_input("Minuto:", "00:00") if tipo_sessione == "Partita" else "N/A"

esito = st.radio("Risultato:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Grafico Statico
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

# --- STATISTICHE LIVE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    sc1, sc2 = st.columns(2)
    sc1.metric(t_home, f"{df[df['team']==t_home]['punti'].sum()} pts")
    if t_away: sc2.metric(t_away, f"{df[df['team']==t_away]['punti'].sum()} pts")
    
    df_t = df[df['team'] == target_team]
    if not df_t.empty:
        st.write(f"📊 Stats {target_team}:")
        stats = df_t.groupby('player').agg(PTS=('punti', 'sum'), Seg=('made', 'sum'), Tot=('made', 'count'))
        stats['%'] = (stats['Seg']/stats['Tot']*100).round(1).astype(str)+'%'
        st.table(stats.sort_values(by='PTS', ascending=False))
        
        # Download
        pdf_b, csv_b = st.columns(2)
        csv_b.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "partita.csv")
        try:
            pdf_data = generate_player_report(df, t_home)
            pdf_b.download_button("📄 PDF", pdf_data, "Report.pdf", "application/pdf")
        except: pass
