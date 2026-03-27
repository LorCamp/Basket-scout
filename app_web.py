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
else:
    st.write("### 🎯 Posiziona il tiro")
    pos_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=5)
    pos_y = st.slider("Distanza dal fondo", -50, 420, 100, step=5)

# --- FUNZIONE DISEGNO CAMPO (ALLINEATA A SINISTRA) ---
def create_court_final(px, py):
    fig = go.Figure()
    
    # Perimetro e Area
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2))
    
    # Lunetta Tiro Libero
    t_free =
