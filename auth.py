import streamlit as st
import os
import json
import hashlib

USERS_FILE = "users_db.json"
DATA_DIR = "data_users"

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Schermata di Benvenuto / Login / Registrazione
    st.title("🔐 Basket Scout Accesso")
    tab1, tab2 = st.tabs(["Login", "Registrati"])

    with tab1:
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type="password", key="login_pass")
        if st.button("Accedi"):
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r") as f:
                    db = json.load(f)
                if u in db and db[u] == hash_password(p):
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Credenziali errate")
            else:
                st.error("Nessun utente registrato")

    with tab2:
        new_u = st.text_input("Scegli Username", key="reg_user")
        new_p = st.text_input("Scegli Password", type="password", key="reg_pass")
        if st.button("Crea Account"):
            if new_u and new_p:
                db = {}
                if os.path.exists(USERS_FILE):
                    with open(USERS_FILE, "r") as f:
                        db = json.load(f)
                
                if new_u in db:
                    st.error("Utente già esistente")
                else:
                    db[new_u] = hash_password(new_p)
                    with open(USERS_FILE, "w") as f:
                        json.dump(db, f)
                    # Crea cartella utente
                    os.makedirs(os.path.join(DATA_DIR, new_u), exist_ok=True)
                    st.success("Account creato! Vai su Login.")
            else:
                st.error("Riempi tutti i campi")
    return False
