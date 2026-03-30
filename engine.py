import pandas as pd
import os

def get_user_folder(user_id):
    path = f"data_users/{user_id}"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

def load_roster(user_id):
    path = f"{get_user_folder(user_id)}/roster.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        # Retro-compatibilità: se mancano le colonne, le aggiunge
        if 'numero' not in df.columns: df.insert(0, 'numero', '0')
        if 'ruolo' not in df.columns: df['ruolo'] = 'N/A'
        return df
    return pd.DataFrame(columns=['numero', 'nome', 'ruolo', 'squadra'])

def save_player_to_roster(user_id, numero, nome, ruolo, squadra):
    df = load_roster(user_id)
    new_p = pd.DataFrame([[numero, nome, ruolo, squadra]], columns=['numero', 'nome', 'ruolo', 'squadra'])
    df = pd.concat([df, new_p], ignore_index=True).drop_duplicates()
    df.to_csv(f"{get_user_folder(user_id)}/roster.csv", index=False)

def save_shots(user_id, shots_list):
    path = f"{get_user_folder(user_id)}/shots.csv"
    pd.DataFrame(shots_list).to_csv(path, index=False)

def load_shots(user_id):
    path = f"{get_user_folder(user_id)}/shots.csv"
    if os.path.exists(path):
        try: return pd.read_csv(path).to_dict('records')
        except: return []
    return []

def delete_last_shot(user_id):
    shots = load_shots(user_id)
    if shots:
        shots.pop()
        save_shots(user_id, shots)
    return shots

def get_shot_type(x, y):
    dist = (x**2 + y**2)**0.5
    if y < 92.5 and abs(x) > 220: return "3PT"
    return "3PT" if dist > 237.5 else "2PT"
