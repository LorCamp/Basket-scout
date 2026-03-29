import streamlit as st
import pandas as pd
from auth import check_password
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report
from court_graphics import create_basketball_court

# 1. Accesso
if not check_password():
    st.stop()

st.set_page_config(page_title="Scout Basket PRO", layout="centered", page_icon="🏀")

# Inizializzazione dati
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

df_roster = load_roster()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Gestione Roster")
teams_in_roster = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []

# Aggiunta rapida giocatore
with st.sidebar.expander("➕ Aggiungi Giocatore"):
    sq_new = st.selectbox("Squadra Roster:", teams_in_roster + ["+ NUOVA..."])
    r_team = st.text_input("Nome Squadra:").upper() if sq_new == "+ NUOVA..." else sq_new
    r_name = st.text_input("Nome Giocatore:").upper()
    if st.button("Salva nel Roster"):
        if r_name and r_team:
            save_player_to_roster(r_name, r_team)
            st.rerun()

st.sidebar.divider()
if st.sidebar.button("🚨 Reset Tiri Partita"):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

# --- MAIN APP ---
st.title("🏀 Scout Basket PRO")

# 1. IMPOSTAZIONI SESSIONE
tipo_sessione = st.selectbox("Tipo Sessione:", ["Allenamento", "Partita"])

col_t1, col_t2 = st.columns(2)
# Seleziona squadra casa dai nomi nel roster o scrivi
t_home = col_t1.selectbox("Squadra Casa (Noi):", teams_in_roster) if teams_in_roster else col_t1.text_input("Squadra Casa:", "CASA").upper()
t_away = None
if tipo_sessione == "Partita":
    t_away = col_t2.text_input("Squadra Ospite:", "OSPITE").upper()

st.divider()

# 2. SELEZIONE AZIONE (FILTRATA)
c_team, c_player, c_time = st.columns([1, 1.5, 1])
target_team = c_team.radio("Team tira:", [t_home, t_away] if t_away else [t_home], horizontal=True)

# FILTRO GIOCATORI: Mostra solo i giocatori della squadra selezionata
giocatori_filtrati = []
if not df_roster.empty:
    giocatori_filtrati = df_roster[df_roster['squadra'] == target_team]['nome'].tolist()

if giocatori_filtrati:
    p_name = c_player.selectbox("Giocatore:", sorted(giocatori_filtrati))
else:
    p_name = c_player.text_input("Nome Giocatore:", "TEAM")

p_time = c_time.text_input("Minuto:", "00:00") if tipo_sessione == "Partita" else "N/A"

esito = st.radio("Risultato:", ["Segnato", "Errore", "TL Segnato", "TL Sbagliato"], horizontal=True)

# 3. POSIZIONAMENTO (SLIDERS PER EVITARE RETTANGOLO)
st.write("### 📍 Posiziona il tiro")
is_tl = "TL" in esito

if is_tl:
    cur_x, cur_y = 0, 142
    st.info("Tiro Libero: Posizione fissa.")
else:
    cur_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=10)
    cur_y = st.slider("Distanza dal fondo", -40, 420, 100, step=10)

# Grafico Statico (Niente rettangolo grigio)
fig = create_basketball_court(cur_x, cur_y, st.session_state.shots)
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True, 'displayModeBar': False})

if st.button("✅ REGISTRA AZIONE", type="primary", use_container_width=True):
    s_type = "TL" if is_tl else get_shot_type(cur_x, cur_y)
    made = "Segnato" in esito
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "sessione": tipo_sessione,
        "team": target_team,
        "player": p_name,
        "tempo": p_time,
        "x": cur_x, "y": cur_y, 
        "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- 4. EXPORT E PDF ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    st.write("📝 **Recap ultimi tiri:**")
    st.dataframe(df.tail(3)[['team', 'player', 'type', 'made']], use_container_width=True)
    
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    exp_col1.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "scout.csv", use_container_width=True)
    
    try:
        pdf_data = generate_player_report(df, t_home)
        exp_col2.download_button("📄 PDF", pdf_data, f"Report_{t_home}.pdf", "application/pdf", use_container_width=True)
    except:
        exp_col2.error("Errore PDF")

    if exp_col3.button("⬅️ Cancella", use_container_width=True):
        st.session_state.shots.pop()
        save_shots(st.session_state.shots)
        st.rerun()
