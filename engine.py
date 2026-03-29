import pandas as pd
import os

def get_user_folder(user_id):
    """Crea e ritorna la cartella specifica per l'utente."""
    path = f"data_users/{user_id}"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

def load_roster(user_id):
    """Carica il roster dell'utente specifico."""
    path = f"{get_user_folder(user_id)}/roster.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=['nome', 'squadra'])

def save_player_to_roster(user_id, nome, squadra):
    """Aggiunge un giocatore al roster dell'utente."""
    df = load_roster(user_id)
    new_p = pd.DataFrame([[nome, squadra]], columns=['nome', 'squadra'])
    df = pd.concat([df, new_p], ignore_index=True).drop_duplicates()
    df.to_csv(f"{get_user_folder(user_id)}/roster.csv", index=False)

def save_shots(user_id, shots_list):
    """Salva i tiri nella cartella dell'utente."""
    path = f"{get_user_folder(user_id)}/shots.csv"
    pd.DataFrame(shots_list).to_csv(path, index=False)

def load_shots(user_id):
    """Carica i tiri dell'utente specifico."""
    path = f"{get_user_folder(user_id)}/shots.csv"
    if os.path.exists(path):
        # Converte il CSV in lista di dizionari per Streamlit
        return pd.read_csv(path).to_dict('records')
    return []

def get_shot_type(x, y):
    """Determina se il tiro è da 2 o 3 punti basandosi sulle coordinate."""
    dist = (x**2 + y**2)**0.5
    # Logica semplificata arco 3 punti FIBA
    if y < 92.5 and abs(x) > 220: 
        return "3PT"
    return "3PT" if dist > 237.5 else "2PT"
