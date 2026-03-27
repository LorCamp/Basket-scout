import json
import os
import numpy as np

def get_shot_type(x, y):
    """Calcola se il tiro è da 2, 3 o un libero"""
    y_rel = y % 845
    dist = np.sqrt(x**2 + y_rel**2)
    
    # Area Tiro Libero
    if 138 <= y_rel <= 148 and abs(x) <= 15: 
        return "FT"
    
    # Tiro da 3 (Arco o Angoli)
    if dist >= 237.5 or (abs(x) > 220 and y_rel < 92.5): 
        return "3PT"
    
    return "2PT"

def save_shots(shots, filename="sessione_tiri.json"):
    """Salva la lista di tiri in un file JSON"""
    with open(filename, 'w') as f:
        json.dump(shots, f, indent=4)

def load_shots(filename="sessione_tiri.json"):
    """Carica i tiri salvati se il file esiste"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return []
    return []
