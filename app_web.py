import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from engine import get_shot_type, save_shots, load_shots

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Basket Scout PRO", layout="centered")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

st.title("🏀 Basket Scout PRO")

# --- 1. SETTING SESSIONE (Allenamento/Partita e Squadra) ---
col_type, col_team = st.columns(2)
with col_type:
    tipo_sessione = st.selectbox("Tipo Sessione:", ["Allenamento", "Partita"])
with col_team:
    p_team = st.text_input("Squadra:", "MIA SQUADRA").upper()

# --- 2. INPUT GIOCATORE E TEMPO ---
st.divider()
col_name, col_time = st.columns([2, 1])
with col_name:
    p_name = st.text_input("Giocatore:", "PLAYER 1").upper()
with col_time:
    p_time_input = st.text_input("Tempo Tot:", "00")

esito_tipo = st.radio("Esito:", 
                      ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], 
                      horizontal=True)

# Verifica se è un tiro libero
is_tl = "TL" in esito_tipo

if is_tl:
    pos_x, pos_y = 0, 142
    st.info(f"📌 Tiro Libero per {p_name}")
else:
    st.write("### 🎯 Posiziona il tiro")
    pos_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=5)
    pos_y = st.slider("Distanza dal fondo", -50, 420, 100, step=5)

# --- 3. FUNZIONE DISEGNO CAMPO (PROPORZIONATO) ---
def create_court_final(px, py):
    fig = go.Figure()
    # Linee FIBA
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2))
    t_free = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_free), y=142.5+80*np.sin(t_free), mode='lines', line_color='white', showlegend=False))
    t_3pt = np.linspace(np.arcsin(92.5/237.5), np.pi - np.arcsin(92.5/237.5), 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_3pt), y=237.5*np.sin(t_3pt), mode='lines', line_color='white', showlegend=False))
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="white")
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")
    
    # Mirino Attuale
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=20, symbol='star'), showlegend=False))
    
    # Tiri storici
    if st.session_state.shots:
        df_tmp = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_tmp[df_tmp['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=color, size=14, symbol=symbol), showlegend=False))
    
    fig.update_layout(width=420, height=520, template="plotly_dark", xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True, scaleanchor="x", scaleratio=1), margin=dict(l=10, r=10, t=10, b=10))
    return fig

st.plotly_chart(create_court_final(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- 4. REGISTRAZIONE ---
if st.button("✅ REGISTRA AZIONE", width='stretch', type="primary"):
    if is_tl:
        s_type, is_m = "TL", "Segnato" in esito_tipo
        pts = 1 if is_m else 0
    else:
        s_type, is_m = get_shot_type(pos_x, pos_y), "Canestro" in esito_tipo
        pts = int(s_type[0]) if is_m else 0
        
    new_shot = {
        "sessione": tipo_sessione,
        "team": p_team,
        "player": p_name,
        "tempo": p_time_input,
        "x": pos_x, "y": pos_y, 
        "made": is_m, 
        "type": s_type,
        "punti": pts
    }
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.rerun()

# --- 5. STATISTICHE E DOWNLOAD ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    st.write(f"### 📊 Report: {p_team} ({tipo_sessione})")
    c1, c2, c3 = st.columns(3)
    for i, t in enumerate(["2PT", "3PT", "TL"]):
        sub = df[df['type'] == t]
        m = len(sub[sub['made'] == True])
        tot = len(sub)
        p = (m/tot*100) if tot > 0 else 0
        [c1, c2, c3][i].metric(t, f"{m}/{tot}", f"{p:.1f}%")

    col_del, col_rep = st.columns(2)
    with col_del:
        if st.button("⬅️ Elimina Ultimo", width='stretch'):
            st.session_state.shots.pop(); save_shots(st.session_state.shots); st.rerun()
    with col_rep:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica CSV", data=csv, file_name=f"scout_{tipo_sessione}_{p_team}.csv", width='stretch')
