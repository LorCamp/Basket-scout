import numpy as np
import json
import os
import pandas as pd

def get_shot_type(x, y):
    """Calcola se il tiro è da 2 o 3 punti (misure FIBA)."""
    dist = np.sqrt(x**2 + y**2)
    # 6.75m è circa 237.5 unità; i corner sono a 6.60m (x > 220)
    if dist >= 237.5 or (abs(x) > 220 and y < 92.5):
        return "3PT"
    return "2PT"

def save_shots(shots):
    """Salva i tiri della sessione in JSON."""
    with open("sessione_tiri.json", "w") as f:
        json.dump(shots, f)

def load_shots():
    """Carica i tiri salvati."""
    if os.path.exists("sessione_tiri.json"):
        with open("sessione_tiri.json", "r") as f:
            return json.load(f)
    return []

# --- FUNZIONI PER IL ROSTER (AGGIUNGI QUESTE) ---

def load_roster():
    """Legge i nomi dal file CSV del roster."""
    if os.path.exists("roster.csv"):
        try:
            df = pd.read_csv("roster.csv")
            # Restituisce la lista ordinata alfabeticamente
            return sorted(df['nome'].astype(str).tolist())
        except:
            return []
    return []

def save_player_to_roster(name):
    """Aggiunge un giocatore al CSV se non è già presente."""
    roster = load_roster()
    name = name.strip().upper()
    if name and name not in roster:
        roster.append(name)
        df = pd.DataFrame({'nome': roster})
        df.to_csv("roster.csv", index=False)
        return True
    return False
