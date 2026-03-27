import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from engine import get_shot_type, save_shots, load_shots

st.set_page_config(page_title="Basket Scout ANALYTICS", layout="centered")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

st.title("🏀 Basket Scout ANALYTICS")

# --- 1. INPUT ---
p_name = st.text_input("Giocatore:", "PLAYER 1").upper()
esito_tipo = st.radio("Tipo e Esito:", 
                      ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], 
                      horizontal=True)

is_tl = "TL" in esito_tipo
if is_tl:
    pos_x, pos_y = 0, 142
    st.info("📌 TIRO LIBERO: Posizione fissata.")
else:
    st.write("### 🎯 Posiziona il tiro dal campo")
    pos_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=5)
    pos_y = st.slider("Distanza dal fondo", -50, 420, 100, step=5)

# --- 2. DISEGNO CAMPO ---
def create_court_hybrid(px, py):
    fig = go.Figure()
    # Linee base campo
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2))
    t_free = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_free), y=142.5+80*np.sin(t_free), mode='lines', line_color='white', showlegend=False))
    t_3pt = np.linspace(np.arcsin(92.5/237.5), np.pi - np.arcsin(92.5/237.5), 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_3pt), y=237.5*np.sin(t_3pt), mode='lines', line_color='white', showlegend=False))
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="white")
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")
    
    # Mirino
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=20, symbol='star'), showlegend=False))
    
    # Storico tiri
    if st.session_state.shots:
        df_tmp = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_tmp[df_tmp['made'] == True if is_made else df_tmp['made'] == False]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=color, size=12, symbol=symbol), showlegend=False))
    
    fig.update_layout(width=420, height=480, template="plotly_dark", xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True), margin=dict(l=10, r=10, t=10, b=10))
    return fig

st.plotly_chart(create_court_hybrid(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- 3. REGISTRAZIONE ---
if st.button("✅ REGISTRA AZIONE", width='stretch', type="primary"):
    if is_tl:
        s_type = "TL"
        is_made = "Segnato" in esito_tipo
        punti = 1 if is_made else 0
    else:
        s_type = get_shot_type(pos_x, pos_y)
        is_made = "Canestro" in esito_tipo
        punti = int(s_type[0]) if is_made else 0
        
    new_shot = {
        "player": p_name, 
        "x": pos_x, "y": pos_y, 
        "made": is_made, 
        "type": s_type,
        "punti_realizzati": punti
    }
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.rerun()

# --- 4. STATISTICHE SPECIFICHE 2PT - 3PT - TL ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    def get_stats(d, tipo):
        sub = d[d['type'] == tipo]
        m = len(sub[sub['made'] == True])
        t = len(sub)
        p = (m/t*100) if t > 0 else 0
        return f"{m}/{t}", f"{p:.1f}%"

    s2, p2 = get_stats(df, "2PT")
    s3, p3 = get_stats(df, "3PT")
    stl, ptl = get_stats(df, "TL")

    st.write("### 📈 Percentuali di Squadra")
    c1, c2, c3 = st.columns(3)
    c1.metric("Da Due (2PT)", s2, p2)
    c2.metric("Da Tre (3PT)", s3, p3)
    c3.metric("Liberi (TL)", stl, ptl)

    # Azioni e Download
    col_del, col_rep = st.columns(2)
    with col_del:
        if st.button("⬅️ Elimina Ultimo", width='stretch'):
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
    with col_rep:
        # Arricchiamo il CSV per l'analisi
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica Report CSV", data=csv, file_name="scout_analitico.csv", width='stretch')
