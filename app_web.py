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

# --- 1. INPUT GIOCATORE ED ESITO ---
p_name = st.text_input("Giocatore:", "PLAYER 1").upper()
esito_tipo = st.radio("Tipo e Esito:", 
                      ["Canestro 2/3PT", "Errore 2/3PT", "TL Segnato", "TL Sbagliato"], 
                      horizontal=True)

# --- 2. LOGICA POSIZIONE ---
is_tl = "TL" in esito_tipo
if is_tl:
    # Posizione fissa sulla lunetta per i tiri liberi
    pos_x, pos_y = 0, 142
    st.info("📌 Modalità Tiro Libero: posizione fissata sulla lunetta.")
else:
    st.write("### 🎯 Posiziona il tiro dal campo")
    pos_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=5)
    pos_y = st.slider("Distanza dal fondo", -50, 420, 100, step=5)

# --- 3. FUNZIONE DISEGNO CAMPO ---
def create_court_hybrid(px, py):
    fig = go.Figure()
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2))
    t_free = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_free), y=142.5+80*np.sin(t_free), mode='lines', line=dict(color='white', width=2), showlegend=False))
    t_3pt = np.linspace(np.arcsin(92.5/237.5), np.pi - np.arcsin(92.5/237.5), 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_3pt), y=237.5*np.sin(t_3pt), mode='lines', line_color='white', showlegend=False))
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="white")
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")
    
    # Mirino (Stella gialla)
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=20, symbol='star'), showlegend=False))
    
    # Tiri storici
    if st.session_state.shots:
        df_tmp = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_tmp[df_tmp['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=color, size=12, symbol=symbol), showlegend=False))
    
    fig.update_layout(width=420, height=480, template="plotly_dark", xaxis=dict(range=[-260, 260], visible=False, fixedrange=True), yaxis=dict(range=[-60, 450], visible=False, fixedrange=True), yaxis_scaleanchor="x", margin=dict(l=10, r=10, t=10, b=10), dragmode=False)
    return fig

st.plotly_chart(create_court_hybrid(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- 4. TASTO REGISTRAZIONE ---
if st.button("✅ REGISTRA AZIONE", width='stretch', type="primary"):
    if is_tl:
        s_type = "1PT (TL)"
        is_made = "Segnato" in esito_tipo
    else:
        s_type = get_shot_type(pos_x, pos_y)
        is_made = "Canestro" in esito_tipo
        
    new_shot = {"player": p_name, "x": pos_x, "y": pos_y, "made": is_made, "type": s_type}
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.rerun()

# --- 5. STATISTICHE AVANZATE ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    # Divisione Campo vs Liberi
    field = df[df['type'] != "1PT (TL)"]
    freethrows = df[df['type'] == "1PT (TL)"]
    
    def get_perc(data):
        if len(data) == 0: return 0, 0, 0
        m = len(data[data['made'] == True])
        t = len(data)
        return m, t, (m/t*100)

    m_f, t_f, p_f = get_perc(field)
    m_tl, t_tl, p_tl = get_perc(freethrows)

    st.write("### 📊 Tabellino Live")
    c1, c2 = st.columns(2)
    c1.metric("Tiri dal Campo", f"{m_f}/{t_f}", f"{p_f:.1f}%")
    c2.metric("Tiri Liberi", f"{m_tl}/{t_tl}", f"{p_tl:.1f}%")

    col_del, col_rep = st.columns(2)
    with col_del:
        if st.button("⬅️ Elimina Ultimo", width='stretch'):
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
    with col_rep:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica Report", data=csv, file_name="scout.csv", width='stretch')
