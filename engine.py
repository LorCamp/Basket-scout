import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def get_conn():
    # Sostituisce il caricamento da file locale con la connessione Google
    return st.connection("gsheets", type=GSheetsConnection)

def load_shots(user_id):
    """Carica i dati dal foglio Google"""
    try:
        conn = get_conn()
        # Legge il foglio 'Shots'. Assicurati che il foglio esista!
        df = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
        if df is None or df.empty:
            return []
        return df.to_dict('records')
    except Exception as e:
        return []

def save_shots(user_id, shots_list):
    """Salva i dati sul foglio Google"""
    if not shots_list:
        return
    try:
        conn = get_conn()
        df = pd.DataFrame(shots_list)
        # Sovrascrive il foglio Google con la lista aggiornata
        conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=df)
    except Exception as e:
        st.error(f"Errore nel salvataggio su Google Sheets: {e}")

def delete_last_shot(user_id):
    """Rimuove l'ultima riga dal database Google"""
    shots = load_shots(user_id)
    if shots:
        shots.pop()
        save_shots(user_id, shots)

def get_shot_type(x, y):
    """Logica per determinare se il tiro è da 2 o 3 punti"""
    import math
    dist = math.sqrt(x**2 + y**2)
    # 6.75 metri è la distanza FIBA (scala circa 238 unità nel grafico)
    if dist > 238:
        return "3PT"
    return "2PT"

def load_roster(user_id):
    """Carica il roster da file locale (o puoi portarlo su Sheets in futuro)"""
    import os
    path = f"data_users/{user_id}/roster.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=['numero', 'nome', 'ruolo', 'squadra'])

def save_player_to_roster(user_id, numero, nome, ruolo, squadra):
    import os
    path = f"data_users/{user_id}/roster.csv"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new_p = pd.DataFrame([[numero, nome, ruolo, squadra]], columns=['numero', 'nome', 'ruolo', 'squadra'])
    df = load_roster(user_id)
    df = pd.concat([df, new_p], ignore_index=True)
    df.to_csv(path, index=False)
