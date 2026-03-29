import plotly.graph_objects as go
import numpy as np
import pandas as pd

def create_basketball_court(px, py, shots_list):
    fig = go.Figure()

    # --- DISEGNO LINEE CAMPO ---
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line_color="white", line_width=2)
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line_color="white", line_width=2)
    
    t_f = np.linspace(0, np.pi, 30)
    fig.add_trace(go.Scatter(x=80*np.cos(t_f), y=142.5+80*np.sin(t_f), mode='lines', line_color='white', showlegend=False))
    
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="white", line_width=2)
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="white", line_width=2)
    
    ang = np.arcsin(92.5/237.5)
    t_a = np.linspace(ang, np.pi - ang, 60)
    fig.add_trace(go.Scatter(x=237.5*np.cos(t_a), y=237.5*np.sin(t_a), mode='lines', line_color='white', showlegend=False))
    
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="orange")

    # --- STORICO TIRI ---
    if shots_list:
        df_s = pd.DataFrame(shots_list)
        for m, c, s in [(True, "#2ecc71", "circle"), (False, "#e74c3c", "x")]:
            mask = df_s[df_s['made'] == m]
            if not mask.empty:
                fig.add_trace(go.Scatter(x=mask['x'], y=mask['y'], mode='markers', 
                                         marker=dict(color=c, size=10, symbol=s), showlegend=False))

    # --- MIRINO (Stella Gialla) ---
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', 
                             marker=dict(color='yellow', size=15, symbol='star'), showlegend=False))

    fig.update_layout(
        width=400, height=450, template="plotly_dark",
        xaxis=dict(range=[-260, 260], visible=False, fixedrange=True),
        yaxis=dict(range=[-60, 450], visible=False, fixedrange=True, scaleanchor="x"),
        margin=dict(l=10, r=10, t=10, b=10),
        dragmode=False, # Disabilita ogni interazione diretta sul grafico
        hovermode=False
    )
    return fig
