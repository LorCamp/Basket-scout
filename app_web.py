import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Basket Scout PRO", layout="centered")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

# --- SIDEBAR: PANNELLO DI CONTROLLO ---
st.sidebar.title("⚙️ Impostazioni")

# 1. Tasto Reset Tiri (Nuova Partita)
if st.sidebar.button("🚨 NUOVA PARTITA (Reset Tiri)", use_container_width=True):
    st.session_state.shots = []
    save_shots([])
    st.rerun()

st.sidebar.divider()

# 2. Gestione Roster
st.sidebar.subheader("👥 Aggiungi al Roster")
r_name = st.sidebar.text_input("Nome Giocatore:").upper()
r_team = st.sidebar.text_input("Squadra:").upper()

if st.sidebar.button("Salva Giocatore", use_container_width=True, type="primary"):
    if r_name and r_team:
        save_player_to_roster(r_name, r_team)
        st.sidebar.success(f"Aggiunto: {r_name}")
        st.rerun()

st.sidebar.divider()

# 3. Tasto Emergenza Roster (Se l'app dà errore sui nomi)
if st.sidebar.button("🗑️ CANCELLA TUTTO IL ROSTER", use_container_width=True):
    if os.path.exists("roster.csv"):
        os.remove("roster.csv")
        st.sidebar.warning("Roster eliminato. Riavvio...")
        st.rerun()

# Caricamento dati roster
df_roster = load_roster()

# --- MAIN APP ---
st.title("🏀 Basket Scout PRO")

col_type, col_team = st.columns(2)
tipo_sessione = col_type.selectbox("Sessione:", ["Allenamento", "Partita"])
# La squadra scritta qui filtra i giocatori sotto
p_team = col_team.text_input("Squadra in campo:", "MIA SQUADRA").upper()

st.divider()

# --- SELEZIONE GIOCATORE FILTRATA ---
col_name, col_time = st.columns([2, 1])
with col_name:
    # Filtro dinamico: mostra solo i giocatori della squadra inserita sopra
    if not df_roster.empty and 'squadra' in df_roster.columns:
        giocatori_squadra = df_roster[df_roster['squadra'] == p_team]['nome'].tolist()
        if giocatori_squadra:
            p_name = st.selectbox("Tiratore:", giocatori_squadra)
        else:
            p_name = st.text_input("Giocatore (manuale):").upper()
            st.caption("Nessun giocatore in roster per questa squadra.")
    else:
        p_name = st.text_input("Giocatore (manuale):").upper()

with col_time:
    p_time = st.text_input("Tempo:", "00:00")

esito_tipo = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Posizionamento
is_tl = "TL" in esito_tipo
pos_x, pos_y = (0, 142) if is_tl else (st.slider("X", -250, 250, 0), st.slider("Y", -50, 420, 100))

# --- DISEGNO CAMPO ---
def create_court_final(px, py):
    fig = go.Figure()
    # Linee base, Area, Lunetta
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line_color="white", line_width=2)
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line_color="white", line_width=2)
    t_f = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_f), y=142.5+80*np.sin(t_f), mode='lines', line_color='white', showlegend=False))
    
    # Arco 3PT (Linee dritte corner + curva)
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white", line_width=2)
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white", line_width=2)
    ang = np.arcsin(92.5/237.5)
    t_a = np.linspace(ang, np.pi - ang, 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_a), y=237.5*np.sin(t_a), mode='lines', line_color='white', showlegend=False))
    
    # Canestro e Mirino
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=18, symbol='star'), showlegend=False))
    
    # Storico
    if st.session_state.shots:
        df_s = pd.DataFrame(st.session_state.shots)
        for m, c, s in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_s[df_s['made'] == m]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=c, size=12, symbol=s), showlegend=False))
    
    fig.update_layout(width=420, height=500, template="plotly_dark", xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), margin=dict(l=10, r=10, t=10, b=10))
    return fig

st.plotly_chart(create_court_final(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- REGISTRAZIONE ---
if st.button("✅ REGISTRA TIRO", use_container_width=True, type="primary"):
    s_type = "TL" if is_tl else get_shot_type(pos_x, pos_y)
    made = "Canestro" in esito_tipo or "Segnato" in esito_tipo
    pts = 1 if is_tl else (int(s_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "sessione": tipo_sessione, "team": p_team, "player": p_name, "tempo": p_time,
        "x": pos_x, "y": pos_y, "made": made, "type": s_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    df_t = df[df['team'] == p_team]
    if not df_t.empty:
        st.write(f"### Recap: {p_team}")
        cols = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_t[df_t['type'] == t]
            m, tot = len(sub[sub['made'] == True]), len(sub)
            p = (m/tot*100) if tot > 0 else 0
            cols[i].metric(t, f"{m}/{tot}", f"{p:.1f}%")

    c_del, c_csv = st.columns(2)
    if c_del.button("⬅️ Elimina Ultimo", use_container_width=True):
        st.session_state.shots.pop()
        save_shots(st.session_state.shots)
        st.rerun()
    c_csv.download_button("📥 Scarica CSV", df.to_csv(index=False).encode('utf-8'), "scout_basket.csv", use_container_width=True)
