import pandas as pd
import os

def get_user_folder(user_id):
    """Crea e ritorna la cartella specifica per l'utente."""
    path = f"data_users/{user_id}"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

def load_roster(user_id):
    """Carica il roster gestendo file vuoti o mancanti."""
    path = f"{get_user_folder(user_id)}/roster.csv"
    cols = ['numero', 'nome', 'ruolo', 'squadra']
    
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if df.empty:
                return pd.DataFrame(columns=cols)
            
            # Controllo e aggiunta colonne mancanti (retrocompatibilità)
            if 'numero' not in df.columns: df.insert(0, 'numero', '0')
            if 'ruolo' not in df.columns: df['ruolo'] = 'N/A'
            return df
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            # Se il file è corrotto o vuoto, ritorna un DF pulito
            return pd.DataFrame(columns=cols)
            
    return pd.DataFrame(columns=cols)

def save_player_to_roster(user_id, numero, nome, ruolo, squadra):
    """Aggiunge un singolo giocatore al roster dell'utente."""
    df = load_roster(user_id)
    new_p = pd.DataFrame([[str(numero), str(nome).upper(), str(ruolo).upper(), str(squadra).upper()]], 
                         columns=['numero', 'nome', 'ruolo', 'squadra'])
    df = pd.concat([df, new_p], ignore_index=True).drop_duplicates()
    df.to_csv(f"{get_user_folder(user_id)}/roster.csv", index=False)

def load_shots(user_id):
    """Carica la cronologia delle azioni/tiri salvati."""
    path = f"{get_user_folder(user_id)}/shots.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if df.empty:
                return []
            return df.to_dict('records')
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            return []
    return []

def save_shots(user_id, shots_list):
    """Salva la lista delle azioni nel file CSV."""
    path = f"{get_user_folder(user_id)}/shots.csv"
    if not shots_list:
        # Se la lista è vuota, creiamo un file con solo l'header per evitare EmptyDataError
        pd.DataFrame(columns=['team', 'player', 'tempo', 'x', 'y', 'made', 'type', 'punti']).to_csv(path, index=False)
    else:
        pd.DataFrame(shots_list).to_csv(path, index=False)

def delete_last_shot(user_id):
    """Rimuove l'ultima azione registrata."""
    shots = load_shots(user_id)
    if shots:
        shots.pop()
        save_shots(user_id, shots)
    return shots

def get_shot_type(x, y):
    """Determina il valore del tiro in base alla posizione sul campo."""
    # Distanza dal canestro (0,0)
    dist = (x**2 + y**2)**0.5
    
    # Regola degli angoli (linea da 3 dritta a 6.75m / 220 pollici circa dalle linee laterali)
    if y < 92.5 and abs(x) > 220: 
        return "3PT"
    
    # Linea dei 3 punti standard (6.75m -> 237.5 pollici nel sistema FIBA/NBA scalato)
    return "3PT" if dist > 237.5 else "2PT"
