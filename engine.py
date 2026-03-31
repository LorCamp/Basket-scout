import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

def get_conn():
    return st.connection("supabase", type=SupabaseConnection)

def load_shots(user_id):
    """Carica solo i tiri dell'utente loggato da Supabase"""
    try:
        conn = get_conn()
        # Query: Seleziona tutto dalla tabella 'shots' dove user_id è uguale a...
        res = conn.query("*", table="shots", ttl=0).eq("user_id", user_id).execute()
        if res.data:
            return res.data
        return []
    except Exception as e:
        return []

def save_shots(user_id, shots_list):
    """Salva SOLO l'ultima azione aggiunta (molto più veloce!)"""
    if not shots_list:
        return
    try:
        conn = get_conn()
        # Prendiamo l'ultimo elemento della lista (l'azione appena fatta)
        last_shot = shots_list[-1]
        last_shot["user_id"] = user_id # Colleghiamo l'azione all'utente
        
        # Inseriamo la riga nel database
        conn.table("shots").insert(last_shot).execute()
    except Exception as e:
        st.error(f"Errore database: {e}")

def delete_last_shot(user_id):
    """Elimina l'ultima riga inserita da questo utente"""
    try:
        conn = get_conn()
        # Cerchiamo l'ID più alto dell'utente e lo eliminiamo
        res = conn.table("shots").select("id").eq("user_id", user_id).order("id", desc=True).limit(1).execute()
        if res.data:
            shot_id = res.data[0]['id']
            conn.table("shots").delete().eq("id", shot_id).execute()
    except Exception:
        pass

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
