import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report

# --- FUNZIONE ACCESSO ---
def check_password():
    """Restituisce True se l'utente ha inserito la password corretta."""

    def password_entered():
        """Controlla se la password inserita è corretta."""
        if st.session_state["password"] == "ErFaLo142127": # <--- CAMBIA QUI LA TUA PASSWORD
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Rimuove la password dalla sessione per sicurezza
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Visualizza l'input per la password
        st.title("🔐 Accesso Riservato")
        st.text_input(
            "Inserisci la password per gestire lo Scout:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        if "password_correct" in st.session_state:
            st.error("😕 Password errata")
        return False
    else:
        return st.session_state["password_correct"]

# --- CONTROLLO ACCESSO ---
if not check_password():
    st.stop()  # Ferma l'esecuzione qui finché la password non è corretta

# --- DA QUI IN POI PARTE IL RESTO DEL TUO CODICE (Configurazione, Sidebar, ecc.) ---
st.set_page_config(page_title="Basket Scout PRO", layout="centered")
# ... tutto il resto del codice che abbiamo scritto finora ...


# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Basket Scout PRO", layout="centered")

# Inizializzazione sessione tiri
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

# Caricamento roster iniziale
df_roster = load_roster()

# --- SIDEBAR: GESTIONE ROSTER ---
st.sidebar.title("⚙️ Pannello Controllo")

if st.sidebar.button("🚨 NUOVA PARTITA (Reset Tiri)", use_container_width=True):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("👥 Aggiungi al Roster")

# Logica ibrida: Selezione squadra esistente o Nuova
if not df_roster.empty:
    lista_squadre_roster = sorted(df_roster['squadra'].unique().tolist())
    lista_squadre_roster.append("+ NUOVA SQUADRA...")
    scelta_t_roster = st.sidebar.selectbox("Squadra per il giocatore:", lista_squadre_roster)
    
    if scelta_t_roster == "+ NUOVA SQUADRA...":
        r_team_final = st.sidebar.text_input("Nome Nuova Squadra:").upper().strip()
    else:
        r_team_final = scelta_t_roster
else:
    r_team_final = st.sidebar.text_input("Nome Squadra:").upper().strip()

r_name = st.sidebar.text_input("Nome Giocatore:").upper().strip()

if st.sidebar.button("➕ Salva nel Roster", use_container_width=True, type="primary"):
    if r_name and r_team_final:
        save_player_to_roster(r_name, r_team_final)
        st.sidebar.success(f"Aggiunto: {r_name}")
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💾 Backup & Ripristino")

if not df_roster.empty:
    st.sidebar.download_button(
        label="📥 Scarica Roster (CSV)",
        data=df_roster.to_csv(index=False).encode('utf-8'),
        file_name="mio_roster_basket.csv",
        mime="text/csv",
        use_container_width=True
    )

uploaded_roster = st.sidebar.file_uploader("📂 Carica Roster da File", type=["csv"], key="roster_uploader")
if uploaded_roster is not None:
    try:
        new_df = pd.read_csv(uploaded_roster)
        new_df.columns = [c.strip().lower() for c in new_df.columns]
        if 'nome' in new_df.columns and 'squadra' in new_df.columns:
            new_df[['nome', 'squadra']].to_csv("roster.csv", index=False)
            st.sidebar.success("✅ Roster caricato!")
            st.rerun()
    except:
        st.sidebar.error("File non valido.")

if st.sidebar.button("🗑️ SVUOTA TUTTO IL ROSTER", use_container_width=True):
    if os.path.exists("roster.csv"):
        os.remove("roster.csv")
        st.rerun()

# --- MAIN APP: GESTIONE PARTITA ---
st.title("🏀 Basket Scout PRO")

# Selezione Squadre (Casa e Ospite)
col_sess, col_t1, col_t2 = st.columns([1, 1.5, 1.5])
tipo_sessione = col_sess.selectbox("Sessione:", ["Allenamento", "Partita"])

teams_exist = sorted(df_roster['squadra'].unique().tolist()) if not df_roster.empty else []

with col_t1:
    s_h = st.selectbox("Squadra Casa:", teams_exist + ["+ AGGIUNGI..."], key="h_sel")
    team_home = st.text_input("Nome Casa:", "CASA").upper().strip() if s_h == "+ AGGIUNGI..." else s_h

with col_t2:
    if tipo_sessione == "Partita":
        s_a = st.selectbox("Squadra Ospite:", teams_exist + ["+ AGGIUNGI..."], key="a_sel")
        team_away = st.text_input("Nome Ospite:", "OSPITE").upper().strip() if s_a == "+ AGGIUNGI..." else s_a
    else:
        team_away = None

st.divider()

# Selezione Team Attivo e Giocatore
col_act, col_name, col_time = st.columns([1.2, 1.8, 1])

with col_act:
    p_team = st.radio("Squadra al tiro:", [team_home, team_away] if team_away else [team_home])

with col_name:
    giocatori_squadra = df_roster[df_roster['squadra'] == p_team]['nome'].tolist() if not df_roster.empty else []
    if giocatori_squadra:
        p_name = st.selectbox("Tiratore:", giocatori_squadra)
    else:
        p_name = st.text_input("Giocatore:").upper().strip()

with col_time:
    p_time = st.text_input("Tempo:", "00:00")

esito_tipo = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Posizionamento
is_tl = "TL" in esito_tipo
pos_x, pos_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0, step=5), st.slider("Y", -50, 420, 100, step=5))

# --- DISEGNO CAMPO ---
def create_court_final(px, py):
    fig = go.Figure()
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line_color="white", line_width=2)
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line_color="white", line_width=2)
    t_f = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_f), y=142.5+80*np.sin(t_f), mode='lines', line_color='white', showlegend=False, hoverinfo='skip'))
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white", line_width=2)
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white", line_width=2)
    ang = np.arcsin(92.5/237.5)
    t_a = np.linspace(ang, np.pi - ang, 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_a), y=237.5*np.sin(t_a), mode='lines', line_color='white', showlegend=False, hoverinfo='skip'))
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=18, symbol='star'), showlegend=False))
    
    if st.session_state.shots:
        df_s = pd.DataFrame(st.session_state.shots)
        for m, c, s in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_s[df_s['made'] == m]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=c, size=12, symbol=s), showlegend=False))
    
    fig.update_layout(width=420, height=500, template="plotly_dark",
        xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
        yaxis=dict(range=[-60, 450], visible=False, fixedrange=True, scaleanchor="x"),
        margin=dict(l=10, r=10, t=10, b=10))
    return fig

st.plotly_chart(create_court_final(pos_x, pos_y), width='stretch', config={'staticPlot': True})

if st.button("✅ REGISTRA AZIONE", use_container_width=True, type="primary"):
    s_type = "TL" if is_tl else get_shot_type(pos_x, pos_y)
    made = "Canestro" in esito_tipo or "Segnato" in esito_tipo
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    st.session_state.shots.append({"sessione": tipo_sessione, "team": p_team, "player": p_name, "tempo": p_time, "x": pos_x, "y": pos_y, "made": made, "type": s_type, "punti": pts})
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    
    # Statistiche Individuali del giocatore selezionato
    df_p = df[(df['team'] == p_team) & (df['player'] == p_name)]
    if not df_p.empty:
        st.subheader(f"👤 Individuale: {p_name}")
        c = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_p[df_p['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            c[i].metric(t, f"{m}/{tot}", f"{(m/tot*100) if tot>0 else 0:.1f}%")
        st.divider()

    # Statistiche Squadra selezionata
    df_t = df[df['team'] == p_team]
    if not df_t.empty:
        st.subheader(f"📊 Team: {p_team}")
        c = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_t[df_t['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            c[i].metric(t, f"{m}/{tot}", f"{(m/tot*100) if tot>0 else 0:.1f}%")

    st.divider()
    c_del, c_csv, c_pdf = st.columns(3)
    if c_del.button("⬅️ Elimina Ultimo", use_container_width=True):
        if st.session_state.shots:
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
    c_csv.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "scout.csv", use_container_width=True)
    try:
        pdf_bytes = generate_player_report(df, team_home) # Report centrato sulla tua squadra
        c_pdf.download_button("📄 PDF", pdf_bytes, f"Report_{team_home}.pdf", "application/pdf", use_container_width=True)
    except:
        c_pdf.error("Errore PDF")
