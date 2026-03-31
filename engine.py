import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def get_conn():
    # Crea la connessione usando l'URL definito nei Secrets
    return st.connection("gsheets", type=GSheetsConnection)

def load_shots(user_id):
    try:
        conn = get_conn()
        # Legge i dati dal foglio specificato nei secrets
        # ttl=0 serve per avere dati sempre freschi senza cache
        df = conn.read(spreadsheet=st.secrets["public_gsheets_url"], ttl=0)
        if df.empty:
            return []
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return []

def save_shots(user_id, shots_list):
    if not shots_list:
        return
    try:
        conn = get_conn()
        df = pd.DataFrame(shots_list)
        # Sovrascrive il foglio con i nuovi dati
        conn.update(spreadsheet=st.secrets["public_gsheets_url"], data=df)
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
