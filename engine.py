import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

def get_connection():
    # Crea la connessione con Google Sheets
    return st.connection("gsheets", type=GSheetsConnection)

def load_shots(user_id):
    """Carica i tiri da Google Sheets."""
    try:
        conn = get_connection()
        # Legge il foglio 'Shots'
        df = conn.read(worksheet="Shots", ttl="0s") # ttl=0 evita la cache
        if df.empty:
            return []
        # Filtriamo per utente se aggiungi una colonna user_id, 
        # altrimenti restituisce tutto
        return df.to_dict('records')
    except Exception:
        return []

def save_shots(user_id, shots_list):
    """Salva la lista azioni su Google Sheets."""
    if not shots_list:
        return
    
    conn = get_connection()
    df = pd.DataFrame(shots_list)
    
    # Aggiorna il foglio Google
    conn.update(worksheet="Shots", data=df)
