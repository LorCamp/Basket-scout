import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from engine import get_shot_type, save_shots, load_shots, load_roster, save_player_to_roster

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Basket Scout PRO", layout="centered")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

# --- SIDEBAR: GESTIONE GIOCATORI ---
st.sidebar.title("👥 Roster")
new_player = st.sidebar.text_input("Nuovo Giocatore:").upper()
if st.sidebar.button("Aggiungi"):
    if new_player:
        if save_player_to_roster(new_player):
            st.sidebar.success(f"{new_player} aggiunto!")
            st.rerun()
        else:
            st.sidebar.warning("Giocatore già presente.")

roster_list = load_roster()

# --- MAIN APP ---
st.title("🏀 Basket Scout PRO")

col_type, col_team = st.columns(2)
tipo_sessione = col_type.selectbox("Sessione:", ["Allenamento", "Partita"])
p_team = col_team.text_input("Squadra:", "MIA SQUADRA").upper()

st.divider()

col_name, col_time = st.columns([2, 1])
if roster_list:
    p_name = col_name.selectbox("Tiratore:", roster_list)
else:
    p_name = col_name.text_input("Giocatore:", "PLAYER 1").upper()
p_time = col_time.text_input("Tempo:", "00:00")

esito_tipo = st.radio("Esito:", ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], horizontal=True)

is_tl = "TL" in esito_tipo
if is_tl:
    pos_x, pos_y = 0, 142
    st.info(f"📌 Tiro Libero per {p_name}")
else:
    st.write("### 🎯 Posiziona il tiro")
    pos_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=5)
    pos_y = st.slider("Distanza dal fondo", -50, 420, 100, step=5)

# --- FUNZIONE DISEGNO CAMPO ---
def create_court_final(px, py):
    fig = go.Figure()
    
    # Perimetro e Area
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2))
    
    # Lunetta Tiro Libero
    t_free = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_free), y=142.5+80*np.sin(t_free), mode='lines', line=dict(color='white', width=2), showlegend=False, hoverinfo='skip'))
    
    # Arco 3 Punti FIBA (Linee Corner + Curva)
    # Linee laterali dritte
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white", line_width=2)
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white", line_width=2)
    
    # Parte curva
    angle_start = np.arcsin(92.5/237.5)
    t_arc = np.linspace(angle_start, np.pi - angle_start, 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_arc), y=237.5*np.sin(t_arc), mode='lines', line=dict(color='white', width=2), showlegend=False, hoverinfo='skip'))
    
    # Canestro e Tabellone
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="white")
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")
    
    # Mirino Attuale (Stella)
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=20, symbol='star'), showlegend=False))
    
    # Storico tiri
    if st.session_state.shots:
        df_tmp = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_tmp[df_tmp['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=color, size=14, symbol=symbol), showlegend=False))
    
    fig.update_layout(
        width=420, height=520, template="plotly_dark",
        xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
        yaxis=dict(range=[-60, 450], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=10, b=10)
    )
    return fig

# Rendering del grafico
st.plotly_chart(create_court_final(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- REGISTRAZIONE ---
if st.button("✅ REGISTRA AZIONE", width='stretch', type="primary"):
    if is_tl:
        s_type, is_m = "TL", "Segnato" in esito_tipo
        pts = 1 if is_m else 0
    else:
        s_type, is_m = get_shot_type(pos_x, pos_y), "Canestro" in esito_tipo
        pts = int(s_type[0]) if is_m else 0
        
    new_shot = {
        "sessione": tipo_sessione, "team": p_team, "player": p_name, "tempo": p_time,
        "x": pos_x, "y": pos_y, "made": is_m, "type": s_type, "punti": pts
    }
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.rerun()

# --- STATISTICHE ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    c1, c2, c3 = st.columns(3)
    for i, t in enumerate(["2PT", "3PT", "TL"]):
        sub = df[df['type'] == t]
        m, tot = len(sub[sub['made'] == True]), len(sub)
        p = (m/tot*100) if tot > 0 else 0
        [c1, c2, c3][i].metric(t, f"{m}/{tot}", f"{p:.1f}%")

    col_del, col_rep = st.columns(2)
    with col_del:
        if st.button("⬅️ Elimina Ultimo", width='stretch'):
            st.session_state.shots.pop(); save_shots(st.session_state.shots); st.rerun()
    with col_rep:
        st.download_button("📥 Report CSV", df.to_csv(index=False).encode('utf-8'), f"scout_{p_team}.csv", width='stretch')