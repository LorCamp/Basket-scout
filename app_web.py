import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from engine import get_shot_type, save_shots, load_shots

# Configurazione Pagina
st.set_page_config(page_title="Basket Scout Live", layout="centered")

# Inizializzazione Sessione
if 'shots' not in st.session_state:
    st.session_state.shots = load_shots()

st.title("🏀 Basket Scout Live")

# --- FUNZIONE DISEGNO CAMPO ---
def create_court():
    fig = go.Figure()
    
    # Perimetro e linee base
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white")
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white")
    
    # Arco 3 Punti (FIBA)
    t = np.linspace(np.arcsin(92.5/237.5), np.pi - np.arcsin(92.5/237.5), 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t), y=237.5*np.sin(t), mode='lines', 
                              line=dict(color='white', width=2), hoverinfo='skip'))
    
    # Tabellone e Canestro
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="white")
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")

    # Disegno tiri registrati
    if st.session_state.shots:
        df = pd.DataFrame(st.session_state.shots)
        for is_made, color, symbol in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df[df['made'] == is_made]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers',
                              marker=dict(color=color, size=14, symbol=symbol), showlegend=False))

    # Configurazione Layout e Modebar
    fig.update_layout(
        width=420, height=480, template="plotly_dark",
        xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
        yaxis=dict(range=[-60, 450], visible=False, fixedrange=True),
        yaxis_scaleanchor="x",
        margin=dict(l=10, r=10, t=10, b=10),
        clickmode='event+select',
        dragmode=False,
        showlegend=False,
        modebar=dict(
            remove=["zoom", "pan", "select", "lasso2d", "zoomIn", "zoomOut", "autoScale", "resetScale"],
            orientation='h', bgcolor='rgba(0,0,0,0)'
        )
    )
    return fig

# --- INTERFACCIA INPUT ---
col1, col2 = st.columns([2, 1])
with col1:
    p_name = st.text_input("Giocatore:", "PLAYER 1").upper()
with col2:
    esito = st.radio("Esito:", ["Fatto", "Errore"], horizontal=True)

# --- GRAFICO INTERATTIVO ---
event = st.plotly_chart(
    create_court(), 
    width='stretch', 
    on_select="rerun", 
    key="basket_chart",
    config={'displayModeBar': True, 'scrollZoom': False}
)

# --- LOGICA DI SALVATAGGIO (CORRETTA) ---
if event is not None:
    selection = event.get("selection", {})
    points = selection.get("points", [])
    
    if points:
        pt = points[0]
        pos_x = pt.get("x")
        pos_y = pt.get("y")
        
        if pos_x is not None and pos_y is not None:
            # Calcolo tipo tiro tramite engine.py
            shot_type = get_shot_type(pos_x, pos_y)
            
            new_shot = {
                "player": p_name, 
                "x": pos_x, 
                "y": pos_y,
                "made": True if esito == "Fatto" else False,
                "type": shot_type
            }
            
            # Aggiunta e salvataggio
            st.session_state.shots.append(new_shot)
            save_shots(st.session_state.shots)
            
            # Reset per permettere nuovi tocchi
            st.rerun()

# --- TABELLA E AZIONI ---
if st.session_state.shots:
    st.divider()
    if st.button("⬅️ Elimina Ultimo Tiro", width='stretch'):
        st.session_state.shots.pop()
        save_shots(st.session_state.shots)
        st.rerun()
    
    # Tabella rapida
    df_stats = pd.DataFrame(st.session_state.shots)
    st.dataframe(df_stats[['player', 'type', 'made']].tail(5), width=None)
    fig.update_layout(
        width=400, height=450, template="plotly_dark",
        xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
        yaxis=dict(range=[-60, 450], visible=False, fixedrange=True),
        yaxis_scaleanchor="x",
        margin=dict(l=5, r=5, t=5, b=5),
        clickmode='event+select',
        dragmode=False, # Disabilitiamo il trascinamento per evitare zoom
        showlegend=False,
        # Pulizia icone Modebar
        modebar=dict(
            remove=["zoom", "pan", "select", "lasso2d", "zoomIn", "zoomOut", "autoScale", "resetScale"],
            orientation='h',
            bgcolor='rgba(0,0,0,0)'
        )
    )
    return fig
# --- INTERFACCIA UTENTE ---
p_name = st.text_input("Giocatore", "PLAYER 1").upper()
esito = st.radio("Esito", ["Fatto", "Errore"], horizontal=True)

# DEBUG: Vedere cosa succede al tocco (puoi rimuoverlo quando funziona)
# st.write("Dati evento:", st.session_state.get('last_event'))

# --- MOSTRA GRAFICO ---
# Il parametro config va qui fuori per attivare la barra strumenti correttamente
event = st.plotly_chart(
    create_court(), 
    width='stretch', 
    on_select="rerun", 
    key="basket_chart",
    config={'displayModeBar': True, 'scrollZoom': False}
)

# --- LOGICA DI SALVATAGGIO ---
if event and "selection" in event and event["selection"]["points"]:
    pt = event["selection"]["points"][0]
    
    # Creiamo il record del tiro
    new_shot = {
        "player": p_name, 
        "x": pt["x"], 
        "y": pt["y"],
        "made": True if esito == "Fatto" else False,
        "type": get_shot_type(pt["x"], pt["y"])
    }
    
    # Salviamo solo se il punto è nuovo (evita doppi clic)
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    st.rerun()

# --- AZIONI ---
if st.button("⬅️ Annulla Ultimo", width='stretch'):
    if st.session_state.shots:
        st.session_state.shots.pop()
        save_shots(st.session_state.shots)
        st.rerun()
    new_shot = {
        "player": p_name, 
        "x": pt["x"], 
        "y": pt["y"],
        "made": True if esito == "Fatto" else False,
        "type": get_shot_type(pt["x"], pt["y"])
    }
    
    # Aggiungiamo il tiro e salviamo
    st.session_state.shots.append(new_shot)
    save_shots(st.session_state.shots)
    
    # Reset della selezione per evitare loop infiniti
    st.rerun()
