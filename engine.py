import numpy as np
import json
import os
import pandas as pd

# --- Funzioni esistenti ---
def get_shot_type(x, y):
    dist = np.sqrt(x**2 + y**2)
    if dist >= 237.5 or (abs(x) > 220 and y < 92.5):
        return "3PT"
    return "2PT"

def save_shots(shots):
    with open("sessione_tiri.json", "w") as f:
        json.dump(shots, f)

def load_shots():
    if os.path.exists("sessione_tiri.json"):
        with open("sessione_tiri.json", "r") as f:
            return json.load(f)
    return []

# --- NUOVE FUNZIONI PER IL ROSTER ---
def load_roster():
    if os.path.exists("roster.csv"):
        df = pd.read_csv("roster.csv")
        return df['nome'].tolist()
    return []

def save_player_to_roster(name):
    roster = load_roster()
    if name not in roster:
        df = pd.DataFrame({'nome': roster + [name]})
        df.to_csv("roster.csv", index=False)
        return True
    return False
