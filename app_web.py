import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from engine import get_shot_type, save_shots, load_shots

st.set_page_config(page_title="Basket Scout Live", layout="centered")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

st.title("🏀 Basket Scout Live")

def create_court():
    fig = go.Figure()
    # Sfondo e linee
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white")
    
    # Arco 3PT
    t = np.linspace(np.arcsin(92.5/237.5), np.pi - np.arcsin(92.5/237.5), 50)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t), y=237.5*np.sin(t), mode='lines', line=dict(color='white', width=2), hoverinfo='skip'))
    
    # Canestro
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")

    if st.session_state.shots:
        df = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df[df['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers',
                              marker=dict(color=color, size=12, symbol=symbol), showlegend=False))

    fig.update_layout(width=400, height=450, template="plotly_dark",
                      xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
                      yaxis=dict(range=[-60, 450], visible=False, fixedrange=True),
                      yaxis_scaleanchor="x", margin=dict(l=5, r=5, t=5, b=5),
                      clickmode='event+select', dragmode=False)
    return fig

# --- INPUT ---
col1, col2 = st.columns([2,1])
with col1: p_name = st.text_input("Giocatore", "PLAYER 1").upper()
with col2: esito = st.radio("Esito", ["Fatto", "Errore"], horizontal=True)

# --- TOUCH LOGIC ---
event = st.plotly_chart(create_court(), width='stretch', on_select="rerun")

if event and event.get("selection") and event["selection"]["points"]:
    pt = event["selection"]["points"][0]
    new_shot = {
        "player": p_name, "x": pt["x"], "y": pt["y"],
        "made": True if esito == "Fatto" else False,
        "type": get_shot_type(pt["x"], pt["y"])
    }
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.rerun()
