import numpy as np
import json
import os
import pandas as pd

if os.path.exists("roster.csv"):
    os.remove("roster.csv") # Questo elimina il file corrotto all'avvio


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
        try:
            with open("sessione_tiri.json", "r") as f:
                return json.load(f)
        except: return []
    return []

def load_roster():
    if os.path.exists("roster.csv"):
        try:
            return pd.read_csv("roster.csv")
        except:
            return pd.DataFrame(columns=['nome', 'squadra'])
    return pd.DataFrame(columns=['nome', 'squadra'])

def save_player_to_roster(name, team):
    df = load_roster()
    name = name.strip().upper()
    team = team.strip().upper()
    if not ((df['nome'] == name) & (df['squadra'] == team)).any():
        new_row = pd.DataFrame({'nome': [name], 'squadra': [team]})
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("roster.csv", index=False)
        return True
    return False
