import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster
from reports import generate_player_report

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Basket Scout PRO", layout="centered")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

# --- SIDEBAR: GESTIONE ROSTER E APP ---
st.sidebar.title("⚙️ Pannello Controllo")

if st.sidebar.button("🚨 NUOVA PARTITA (Reset Tiri)", use_container_width=True):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("👥 Gestione Roster")
r_name = st.sidebar.text_input("Nome Giocatore:").upper()
r_team_new = st.sidebar.text_input("Squadra Giocatore:").upper()

if st.sidebar.button("➕ Salva nel Roster", use_container_width=True, type="primary"):
    if r_name and r_team_new:
        save_player_to_roster(r_name, r_team_new)
        st.sidebar.success(f"Aggiunto: {r_name}")
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💾 Backup & Ripristino")

# Caricamento roster esistente per il download
df_roster = load_roster()

if not df_roster.empty:
    st.sidebar.download_button(
        label="📥 Scarica Roster sul Telefono",
        data=df_roster.to_csv(index=False).encode('utf-8'),
        file_name="mio_roster_basket.csv",
        mime="text/csv",
        use_container_width=True
    )

# Upload Roster dal telefono
uploaded_roster = st.sidebar.file_uploader("📂 Carica Roster da File", type=["csv"])
if uploaded_roster is not None:
    try:
        new_df = pd.read_csv(uploaded_roster)
        if 'nome' in new_df.columns and 'squadra' in new_df.columns:
            new_df.to_csv("roster.csv", index=False)
            st.sidebar.success("Roster caricato! Riavvio...")
            st.rerun()
    except:
        st.sidebar.error("File non valido.")

if st.sidebar.button("🗑️ SVUOTA TUTTO IL ROSTER", use_container_width=True):
    if os.path.exists("roster.csv"):
        os.remove("roster.csv")
        st.rerun()

# --- MAIN APP ---
st.title("🏀 Basket Scout PRO")

# Selezione Team e Sessione
col_sess, col_team_sel = st.columns(2)
tipo_sessione = col_sess.selectbox("Sessione:", ["Allenamento", "Partita"])

with col_team_sel:
    if not df_roster.empty and 'squadra' in df_roster.columns:
        lista_squadre = sorted(df_roster['squadra'].unique().tolist())
        lista_squadre.append("+ AGGIUNGI NUOVA...")
        scelta_squadra = st.selectbox("Seleziona Squadra:", lista_squadre)
        p_team = st.text_input("Nome Squadra:").upper() if scelta_squadra == "+ AGGIUNGI NUOVA..." else scelta_squadra
    else:
        p_team = st.text_input("Squadra:", "MIA SQUADRA").upper()

st.divider()

# Selezione Giocatore Filtrata
col_name, col_time = st.columns([2, 1])
with col_name:
    if not df_roster.empty and 'squadra' in df_roster.columns:
        giocatori_squadra = df_roster[df_roster['squadra'] == p_team]['nome'].tolist()
        p_name = st.selectbox("Tiratore:", giocatori_squadra) if giocatori_squadra else st.text_input("Giocatore (manuale):").upper()
    else:
        p_name = st.text_input("Giocatore (manuale):").upper()
p_time = col_time.text_input("Tempo:", "00:00")

esito_tipo = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Logica Posizione
is_tl = "TL" in esito_tipo
pos_x, pos_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0), st.slider("Y", -50, 420, 100))

# Disegno Campo
def create_court_final(px, py):
    fig = go.Figure()
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line_color="white", line_width=2)
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line_color="white", line_width=2)
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white", line_width=2)
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white", line_width=2)
    ang = np.arcsin(92.5/237.5)
    t_a = np.linspace(ang, np.pi - ang, 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_a), y=237.5*np.sin(t_a), mode='lines', line_color='white', showlegend=False))
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=18, symbol='star'), showlegend=False))
    
    if st.session_state.shots:
        df_s = pd.DataFrame(st.session_state.shots)
        for m, c, s in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_s[df_s['made'] == m]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=c, size=12, symbol=s), showlegend=False))
    
    fig.update_layout(width=420, height=500, template="plotly_dark", xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), margin=dict(l=10, r=10, t=10, b=10))
    return fig

st.plotly_chart(create_court_final(pos_x, pos_y), width='stretch', config={'staticPlot': True})

if st.button("✅ REGISTRA TIRO", use_container_width=True, type="primary"):
    s_type = "TL" if is_tl else get_shot_type(pos_x, pos_y)
    made = "Canestro" in esito_tipo or "Segnato" in esito_tipo
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    st.session_state.shots.append({"sessione": tipo_sessione, "team": p_team, "player": p_name, "tempo": p_time, "x": pos_x, "y": pos_y, "made": made, "type": s_type, "punti": pts})
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE E DOWNLOAD ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    
    # Statistiche Individuali
    df_p = df[(df['team'] == p_team) & (df['player'] == p_name)]
    if not df_p.empty:
        st.subheader(f"👤 Individuale: {p_name}")
        c = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_p[df_p['type'] == t]
            m, tot = len(sub[sub['made']==True]), len(sub)
            c[i].metric(t, f"{m}/{tot}", f"{(m/tot*100) if tot>0 else 0:.1f}%")
        st.divider()

    # Statistiche Team
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
        st.session_state.shots.pop()
        save_shots(st.session_state.shots)
        st.rerun()
    c_csv.download_button("📥 CSV", df.to_csv(index=False).encode('utf-8'), "scout.csv", use_container_width=True)
    try:
        pdf_bytes = generate_player_report(df, p_team)
        c_pdf.download_button("📄 PDF", pdf_bytes, f"Report_{p_team}.pdf", "application/pdf", use_container_width=True)
    except:
        c_pdf.error("Errore PDF")
