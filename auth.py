import streamlit as st
import os
import json
import hashlib

USERS_FILE = "users_db.json"
DATA_DIR = "data_users"

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password():
    # Inizializzazione variabili se non esistono
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None

    # Se è già loggato, ritorna True immediatamente
    if st.session_state.authenticated:
        return True

    # Schermata di Login/Registrazione
    st.title("🏀 Basket Scout Accesso")
    tab1, tab2 = st.tabs(["Login", "Registrati"])

    with tab1:
        u = st.text_input("Username", key="l_user")
        p = st.text_input("Password", type="password", key="l_pass")
        if st.button("Accedi"):
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r") as f:
                    db = json.load(f)
                if u in db and db[u] == hash_password(p):
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.rerun() # Forza il ricaricamento dell'app loggata
                else:
                    st.error("Credenziali errate")
            else:
                st.error("Nessun utente registrato. Vai sulla scheda Registrati.")

    with tab2:
        new_u = st.text_input("Scegli Username", key="r_user")
        new_p = st.text_input("Scegli Password", type="password", key="r_pass")
        if st.button("Crea Account"):
            if new_u and new_p:
                db = {}
                if os.path.exists(USERS_FILE):
                    with open(USERS_FILE, "r") as f:
                        db = json.load(f)
                
                if new_u in db:
                    st.error("Username già occupato")
                else:
                    db[new_u] = hash_password(new_p)
                    with open(USERS_FILE, "w") as f:
                        json.dump(db, f)
                    os.makedirs(os.path.join(DATA_DIR, new_u), exist_ok=True)
                    st.success("Account creato! Ora vai su Login.")
            else:
                st.error("Riempi tutti i campi")
    
    return False # Blocca l'app qui finché non avviene il login
