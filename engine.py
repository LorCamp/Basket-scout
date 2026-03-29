import pandas as pd
import os

def get_user_folder():
    """Ritorna il percorso della cartella dell'utente corrente."""
    user = st.session_state.username
    path = f"data_users/{user}"
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def load_roster():
    import streamlit as st # Import locale per evitare conflitti
    path = f"{get_user_folder()}/roster.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=['nome', 'squadra'])

def save_player_to_roster(nome, squadra):
    df = load_roster()
    new_p = pd.DataFrame([[nome, squadra]], columns=['nome', 'squadra'])
    df = pd.concat([df, new_p], ignore_index=True).drop_duplicates()
    df.to_csv(f"{get_user_folder()}/roster.csv", index=False)

def save_shots(shots_list):
    pd.DataFrame(shots_list).to_csv(f"{get_user_folder()}/shots.csv", index=False)

def load_shots():
    path = f"{get_user_folder()}/shots.csv"
    if os.path.exists(path):
        return pd.read_csv(path).to_dict('records')
    return []

def get_shot_type(x, y):
    # Logica per determinare se è 2PT o 3PT (già esistente)
    dist = (x**2 + y**2)**0.5
    if y < 92.5 and abs(x) > 220: return "3PT"
    return "3PT" if dist > 237.5 else "2PT"
