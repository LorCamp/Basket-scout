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
col_name, col_res = st.columns([2, 1])
with col_name:
    p_name = st.text_input("Giocatore:", "PLAYER 1").upper()
with col_res:
    esito = st.radio("Esito:", ["Fatto", "Errore"], horizontal=True)

# --- 2. CONTROLLI DI POSIZIONE (SLIDERS) ---
st.write("### 🎯 Posiziona il tiro")
pos_x = st.slider("Sinistra <-> Destra", -250, 250, 0, step=5)
pos_y = st.slider("Distanza dal fondo", -50, 420, 100, step=5)

# --- 3. FUNZIONE DISEGNO CAMPO COMPLETO ---
def create_court_hybrid(px, py):
    fig = go.Figure()
    
    # Perimetro Esterno
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    
    # Area dei 3 Secondi (Rettangolo)
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2))
    
    # Lunetta Tiro Libero (Semicerchio superiore)
    t_free = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(
        x=80 * np.cos(t_free), 
        y=142.5 + 80 * np.sin(t_free), 
        mode='lines', line=dict(color='white', width=2), hoverinfo='skip', showlegend=False
    ))
    
    # Arco 3 Punti FIBA (Semicerchio + Linee dritte)
    t_3pt = np.linspace(np.arcsin(92.5/237.5), np.pi - np.arcsin(92.5/237.5), 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_3pt), y=237.5*np.sin(t_3pt), mode='lines', line_color='white', hoverinfo='skip', showlegend=False))
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white")

    # Canestro e Tabellone
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="white")
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")

    # MIRINO GIALLO (Stella)
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', 
                  marker=dict(color='yellow', size=20, symbol='star'), name="Mirino"))

    # Tiri Registrati (Pallini verdi/rossi)
    if st.session_state.shots:
        df = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df[df['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers',
                              marker=dict(color=color, size=14, symbol=symbol), showlegend=False))

    # Layout Fisso
    fig.update_layout(width=420, height=480, template="plotly_dark",
                      xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
                      yaxis=dict(range=[-60, 450], visible=False, fixedrange=True),
                      yaxis_scaleanchor="x", margin=dict(l=10, r=10, t=10, b=10),
                      dragmode=False, showlegend=False)
    return fig

# Mostriamo il grafico
st.plotly_chart(create_court_hybrid(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- 4. TASTO REGISTRAZIONE ---
if st.button("✅ REGISTRA TIRO", width='stretch', type="primary"):
    shot_type = get_shot_type(pos_x, pos_y)
    new_shot = {
        "player": p_name, "x": pos_x, "y": pos_y,
        "made": True if esito == "Fatto" else False,
        "type": shot_type
    }
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.success(f"Tiro registrato!")
    st.rerun()

# --- 5. STATISTICHE LIVE E AZIONI ---
if st.session_state.shots:
    st.divider()
    df_stats = pd.DataFrame(st.session_state.shots)
    
    #
    # Lunetta Tiro Libero (Semicerchio superiore)
    t_free = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(
        x=80 * np.cos(t_free), 
        y=142.5 + 80 * np.sin(t_free), 
        mode='lines', line=dict(color='white', width=2), hoverinfo='skip', showlegend=False
    ))
    
    # Arco 3 Punti FIBA (Semicerchio + Linee dritte)
    t_3pt = np.linspace(np.arcsin(92.5/237.5), np.pi - np.arcsin(92.5/237.5), 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_3pt), y=237.5*np.sin(t_3pt), mode='lines', line_color='white', hoverinfo='skip', showlegend=False))
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white")

    # Canestro e Tabellone
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="white") # Tabellone
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange") # Ferro

    # MIRINO GIALLO (Stella)
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', 
                  marker=dict(color='yellow', size=20, symbol='star'), name="Mirino"))

    # Tiri Registrati (Pallini verdi/rossi)
    if st.session_state.shots:
        df = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df[df['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers',
                              marker=dict(color=color, size=14, symbol=symbol), showlegend=False))

    # Layout Fisso (Niente zoom accidentale)
    fig.update_layout(width=420, height=480, template="plotly_dark",
                      xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
                      yaxis=dict(range=[-60, 450], visible=False, fixedrange=True),
                      yaxis_scaleanchor="x", margin=dict(l=10, r=10, t=10, b=10),
                      dragmode=False, showlegend=False)
    return fig

# Mostriamo il grafico
st.plotly_chart(create_court_hybrid(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- 4. TASTO REGISTRAZIONE ---
if st.button("✅ REGISTRA TIRO", width='stretch', type="primary"):
    shot_type = get_shot_type(pos_x, pos_y)
    new_shot = {
        "player": p_name, "x": pos_x, "y": pos_y,
        "made": True if esito == "Fatto" else False,
        "type": shot_type
    }
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.success(f"Tiro da {shot_type} registrato per {p_name}!")
    st.rerun()

# --- 5. STATISTICHE LIVE E AZIONI ---
if st.session_state.shots:
    st.divider()
    df_stats = pd.DataFrame(st.session_state.shots)
    
    # Metriche veloci
    totali = len(df_stats)
    segnati = len(df_stats[df_stats['made'] == True])
    perc = (segnati / totali * 100) if totali > 0 else 0
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Totali", totali)
    m2.metric("Segnati", segnati)
    m3.metric("Precisione", f"{perc:.1f}%")
        df = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df[df['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers',
                              marker=dict(color=color, size=12, symbol=symbol), showlegend=False))

    fig.update_layout(width=420, height=480, template="plotly_dark",
                      xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
                      yaxis=dict(range=[-60, 450], visible=False, fixedrange=True),
                      yaxis_scaleanchor="x", margin=dict(l=10, r=10, t=10, b=10),
                      dragmode=False, showlegend=False)
    return fig

# Mostriamo il grafico con la nuova proprietà width
st.plotly_chart(create_court_hybrid(pos_x, pos_y), width='stretch', config={'staticPlot': True})

# --- 4. TASTO REGISTRAZIONE ---
if st.button("✅ REGISTRA TIRO", width='stretch', type="primary"):
    shot_type = get_shot_type(pos_x, pos_y)
    new_shot = {
        "player": p_name, "x": pos_x, "y": pos_y,
        "made": True if esito == "Fatto" else False,
        "type": shot_type
    }
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.success(f"Tiro da {shot_type} registrato!")
    st.rerun()

# --- 5. AZIONI ---
if st.session_state.shots:
    st.divider()
    col_del, col_rep = st.columns(2)
    with col_del:
        if st.button("⬅️ Elimina Ultimo", width='stretch'):
            st.session_state.shots.pop()
            save_shots(st.session_state.shots)
            st.rerun()
    with col_rep:
        df_log = pd.DataFrame(st.session_state.shots)
        csv = df_log.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica CSV", data=csv, file_name="scout_basket.csv", width='stretch')
