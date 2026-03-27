import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Basket Scout PRO", layout="centered")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

# --- SIDEBAR ---
st.sidebar.title("⚙️ Pannello Controllo")

# Tasto Nuova Partita
if st.sidebar.button("🚨 NUOVA PARTITA (Reset Tiri)", use_container_width=True, type="secondary"):
    st.session_state.shots = []
    save_shots([])
    st.sidebar.success("Sessione tiri azzerata!")
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("👥 Gestione Roster")
r_name = st.sidebar.text_input("Nome Giocatore:").upper()
r_team = st.sidebar.text_input("Squadra del Giocatore:").upper()

if st.sidebar.button("Salva nel Roster", use_container_width=True):
    if r_name and r_team:
        if save_player_to_roster(r_name, r_team):
            st.sidebar.success(f"{r_name} aggiunto a {r_team}!")
            st.rerun()
    else:
        st.sidebar.error("Inserisci sia nome che squadra!")

df_roster = load_roster()

# --- MAIN APP ---
st.title("🏀 Basket Scout PRO")

col_type, col_team = st.columns(2)
tipo_sessione = col_type.selectbox("Sessione:", ["Allenamento", "Partita"])
# La squadra selezionata qui filtrerà il roster
p_team = col_team.text_input("Squadra in campo:", "MIA SQUADRA").upper()

st.divider()

# --- FILTRO GIOCATORI PER SQUADRA ---
col_name, col_time = st.columns([2, 1])
with col_name:
    # Filtriamo il dataframe del roster per la squadra scritta sopra
    giocatori_filtrati = df_roster[df_roster['squadra'] == p_team]['nome'].tolist()
    
    if giocatori_filtrati:
        p_name = st.selectbox("Tiratore:", giocatori_filtrati)
    else:
        p_name = st.text_input("Giocatore (manuale):", "PLAYER 1").upper()
        st.caption("Nessun giocatore in roster per questa squadra.")

with col_time:
    p_time = st.text_input("Tempo:", "00:00")

esito_tipo = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True)

# Logica posizione
is_tl = "TL" in esito_tipo
if is_tl:
    pos_x, pos_y = 0, 142
else:
    pos_x = st.slider("X", -250, 250, 0, step=5)
    pos_y = st.slider("Y", -50, 420, 100, step=5)

# --- DISEGNO CAMPO ---
def create_court_v3(px, py):
    fig = go.Figure()
    # Perimetro, Area e Lunetta
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line_color="white", line_width=2)
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line_color="white", line_width=2)
    t_free = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_free), y=142.5+80*np.sin(t_free), mode='lines', line_color='white', showlegend=False))
    
    # Arco 3PT FIBA
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white", line_width=2)
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white", line_width=2)
    a = np.arcsin(92.5/237.5)
    t_arc = np.linspace(a, np.pi - a, 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_arc), y=237.5*np.sin(t_arc), mode='lines', line_color='white', showlegend=False))
    
    # Canestro
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")
    
    # Mirino Stella
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=18, symbol='star'), showlegend=False))
    
    # Tiri storici
    if st.session_state.shots:
        df_s = pd.DataFrame(st.session_state.shots)
        for m, c, s in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_s[df_s['made'] == m]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=c, size=12, symbol=s), showlegend=False))
    
    fig.update_layout(width=420, height=500, template="plotly_dark", xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), margin=dict(l=10, r=10, t=10, b=10))
    return fig

st.plotly_chart(create_court_v3(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- REGISTRAZIONE ---
if st.button("✅ REGISTRA AZIONE", use_container_width=True, type="primary"):
    shot_type = "TL" if is_tl else get_shot_type(pos_x, pos_y)
    made = "Canestro" in esito_tipo or "Segnato" in esito_tipo
    pts = 1 if is_tl else (int(shot_type[0]) if made else 0)
    
    st.session_state.shots.append({
        "sessione": tipo_sessione, "team": p_team, "player": p_name, "tempo": p_time,
        "x": pos_x, "y": pos_y, "made": made, "type": shot_type, "punti": pts
    })
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    df = pd.DataFrame(st.session_state.shots)
    st.divider()
    # Mostra solo statistiche della squadra selezionata
    df_team = df[df['team'] == p_team]
    if not df_team.empty:
        st.write(f"### Statistiche Team: {p_team}")
        c1, c2, c3 = st.columns(3)
        for i, t in enumerate(["2PT", "3PT", "TL"]):
            sub = df_team[df_team['type'] == t]
            m, tot = len(sub[sub['made'] == True]), len(sub)
            p = (m/tot*100) if tot > 0 else 0
            [c1, c2, c3][i].metric(t, f"{m}/{tot}", f"{p:.1f}%")

    col_del, col_rep = st.columns(2)
    col_del.button("⬅️ Elimina Ultimo", on_click=lambda: (st.session_state.shots.pop(), save_shots(st.session_state.shots)), use_container_width=True)
    col_rep.download_button("📥 Scarica CSV", df.to_csv(index=False).encode('utf-8'), f"scout_full.csv", use_container_width=True)
