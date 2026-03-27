import numpy as np
import json
import os
import pandas as pd

def get_shot_type(x, y):
    """Calcola se il tiro è da 2 o 3 punti in base alle coordinate FIBA."""
    dist = np.sqrt(x**2 + y**2)
    # Regola FIBA: Arco a 6.75m (circa 237.5 unità) e corner a 6.60m (x > 220)
    if dist >= 237.5 or (abs(x) > 220 and y < 92.5):
        return "3PT"
    return "2PT"

def save_shots(shots):
    """Salva la sessione dei tiri in un file JSON."""
    with open("sessione_tiri.json", "w") as f:
        json.dump(shots, f)

def load_shots():
    """Carica i tiri salvati se il file esiste."""
    if os.path.exists("sessione_tiri.json"):
        with open("sessione_tiri.json", "r") as f:
            return json.load(f)
    return []

# --- NUOVE FUNZIONI PER IL ROSTER (MANCANTI) ---

def load_roster():
    """Carica l'elenco dei nomi dei giocatori dal file CSV."""
    if os.path.exists("roster.csv"):
        try:
            df = pd.read_csv("roster.csv")
            return df['nome'].tolist()
        except:
            return []
    return []

def save_player_to_roster(name):
    """Aggiunge un nuovo giocatore al file CSV se non esiste già."""
    roster = load_roster()
    name = name.strip().upper()
    if name and name not in roster:
        roster.append(name)
        df = pd.DataFrame({'nome': roster})
        df.to_csv("roster.csv", index=False)
        return True
    return False
