import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

def get_conn():
    # Si collega a Supabase usando i Secrets [connections.supabase]
    return st.connection("supabase", type=SupabaseConnection)

# --- GESTIONE TIRI (Tabella 'shots') ---

def load_shots(user_id):
    """Carica i tiri dell'utente dal database"""
    try:
        conn = get_conn()
        res = conn.table("shots").select("*").eq("user_id", user_id).execute()
        return res.data if res.data else []
    except Exception:
        return []

def save_shots(user_id, shots_list):
    """Salva l'ultima azione registrata"""
    if not shots_list:
        return
    try:
        conn = get_conn()
        last_shot = shots_list[-1]
        last_shot["user_id"] = user_id
        # Inserisce la riga singola (molto più efficiente)
        conn.table("shots").insert(last_shot).execute()
    except Exception as e:
        st.error(f"Errore salvataggio tiro: {e}")

def delete_last_shot(user_id):
    """Cancella l'ultima azione dell'utente (per il tasto Undo)"""
    try:
        conn = get_conn()
        res = conn.table("shots").select("id").eq("user_id", user_id).order("id", desc=True).limit(1).execute()
        if res.data:
            conn.table("shots").delete().eq("id", res.data[0]['id']).execute()
    except Exception:
        pass

# --- GESTIONE ROSTER (Tabella 'roster') ---

def load_roster(user_id):
    """Carica i giocatori dell'utente dal database"""
    try:
        conn = get_conn()
        res = conn.table("roster").select("*").eq("user_id", user_id).execute()
        if res.data:
            return pd.DataFrame(res.data)
        return pd.DataFrame(columns=['numero', 'nome', 'ruolo', 'squadra'])
    except Exception:
        return pd.DataFrame(columns=['numero', 'nome', 'ruolo', 'squadra'])

def save_player_to_roster(user_id, numero, nome, ruolo, squadra):
    """Aggiunge un giocatore al database cloud"""
    try:
        conn = get_conn()
        player_data = {
            "user_id": user_id,
            "numero": str(numero),
            "nome": nome.upper(),
            "ruolo": ruolo,
            "squadra": squadra.upper()
        }
        conn.table("roster").insert(player_data).execute()
        return True
    except Exception as e:
        st.error(f"Errore salvataggio giocatore: {e}")
        return False

def get_shot_type(x, y):
    """Logica distanza tiro (scala FIBA)"""
    import math
    dist = math.sqrt(x**2 + y**2)
    return "3PT" if dist > 238 else "2PT"
