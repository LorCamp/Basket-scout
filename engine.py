import numpy as np
import json
import os

def get_shot_type(x, y):
    dist = np.sqrt(x**2 + y**2)
    # Regola FIBA: Arco a 6.75m (circa 237.5 unità) e corner a 6.60m
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
