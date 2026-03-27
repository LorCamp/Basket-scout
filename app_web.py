import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from engine import get_shot_type, save_shots, load_shots

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Basket Scout ANALYTICS", layout="centered")

if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

st.title("🏀 Basket Scout ANALYTICS")

# --- 1. INPUT GIOCATORE ED ESITO ---
p_name = st.text_input("Giocatore:", "PLAYER 1").upper()
esito_tipo = st.radio("Tipo e Esito:", 
                      ["Canestro (Campo)", "Errore (Campo)", "TL Segnato", "TL Sbagliato"], 
                      horizontal=True)

# Verifica se è un tiro libero
is_tl = "TL" in esito_tipo

if is_tl:
    pos_x, pos_y = 0, 142  # Posizione fissa sulla lunetta
    st.info("📌 MODALITÀ TIRO LIBERO: Posizione fissata sulla lunetta.")
else:
    st.write("### 🎯 Posiziona il tiro dal campo")
    pos_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=5)
    pos_y = st.slider("Distanza dal fondo", -50, 420, 100, step=5)

# --- 2. FUNZIONE DISEGNO CAMPO (PROPORZIONATO) ---
def create_court_hybrid(px, py):
    fig = go.Figure()
    
    # Linee base campo (FIBA)
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2))
    
    # Lunetta Tiro Libero
    t_free = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_free), y=142.5+80*np.sin(t_free), mode='lines', line=dict(color='white', width=2), showlegend=False, hoverinfo='skip'))
    
    # Arco 3 Punti
    t_3pt = np.linspace(np.arcsin(92.5/237.5), np.pi - np.arcsin(92.5/237.5), 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_3pt), y=237.5*np.sin(t_3pt), mode='lines', line_color='white', showlegend=False, hoverinfo='skip'))
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white")
    
    # Canestro e Tabellone
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="white")
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")
    
    # Mirino Attuale (Stella)
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(color='yellow', size=18, symbol='star'), showlegend=False))
    
    # Tiri storici registrati
    if st.session_state.shots:
        df_tmp = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_tmp[df_tmp['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', marker=dict(color=color, size=12, symbol=symbol), showlegend=False))
    
    # --- FIX PROPORZIONI ---
    fig.update_layout(
        width=420, height=520, template="plotly_dark",
        xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
        yaxis=dict(
            range=[-60, 450], visible=False, fixedrange=True,
            scaleanchor="x", scaleratio=1  # Questo impedisce la deformazione
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        dragmode=False
    )
    return fig

# Visualizzazione Grafico
st.plotly_chart(create_court_hybrid(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- 3. LOGICA REGISTRAZIONE ---
if st.button("✅ REGISTRA AZIONE", width='stretch', type="primary"):
    if is_tl:
        s_type = "TL"
        made_val = "Segnato" in esito_tipo
        punti = 1 if made_val else 0
    else:
        s_type = get_shot_type(pos_x, pos_y)
        made_val = "Canestro" in esito_tipo
        punti = int(s_type[0]) if made_val else 0
        
    new_shot = {
        "player": p_name, 
        "x": pos_x, "y": pos_y, 
        "made": made_val, 
        "type": s_type,
        "punti": punti
    }
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.rerun()

# --- 4. TABELLINO LIVE ---
if st.session_state.shots:
    st.divider()
    df = pd.DataFrame(st.session_state.shots)
    
    def calc_stats(data, t_name):
        sub = data[data['type'] == t_name]
        m = len(sub[sub['made'] == True])
        t = len(sub)
        p = (m/t*100) if t > 0 else 0
        return f"{m}/{t}", f"{p:.1f}%"

    s2, p2 = calc_stats(df, "2PT")
    s3, p3 = calc_stats(df, "3PT")
    stl, ptl = calc_stats(df, "TL")

    st.write("### 📊 Statistiche Squadra")
    c1, c2, c3 = st.columns(3)
    c1.metric("2PT", s2, p2)
    c2.metric("3PT", s3, p3)
    c3.metric("TL", stl, ptl)

    # Azioni e Download
    col_del, col_rep = st.columns(2)
    with col_del:
        if st.button("⬅️ Elimina Ultimo", width='stretch'):
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
    with col_rep:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica Report CSV", data=csv, file_name="scout_basket.csv", width='stretch')
