import numpy as np
import json
import os

def get_shot_type(x, y):
    # Distanza dal canestro posizionato in (0,0)
    dist = np.sqrt(x**2 + y**2)
    
    # Regola FIBA/NBA: 
    # 237.5 è il raggio dell'arco
    # abs(x) > 220 e y < 92.5 gestisce le tacche dritte negli angoli
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
