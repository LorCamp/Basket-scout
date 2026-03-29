import streamlit as st
import os
import json
import hashlib

# Cartella dove salveremo i dati degli utenti
DATA_DIR = "data_users"
USERS_FILE = "users_db.json"

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = hash_password(password)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)
    # Crea la cartella personale dell'utente
    user_path = os.path.join(DATA_DIR, username)
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    return True

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("🔐 Accesso Basket Scout")
    tab1, tab2 = st.tabs(["Login", "Registrati"])

    with tab1:
        user_login = st.text_input("Username", key="l_user")
        pass_login = st.text_input("Password", type="password", key="l_pass")
        if st.button("Accedi"):
            users = load_users()
            if user_login in users and users[user_login] == hash_password(pass_login):
                st.session_state.authenticated = True
                st.session_state.username = user_login
                st.rerun()
            else:
                st.error("Username o Password errati")

    with tab2:
        new_user = st.text_input("Scegli Username", key="r_user")
        new_pass = st.text_input("Scegli Password", type="password", key="r_pass")
        conf_pass = st.text_input("Conferma Password", type="password", key="r_conf")
        if st.button("Crea Account"):
            if new_pass != conf_pass:
                st.error("Le password non coincidono")
            elif len(new_pass) < 6:
                st.error("La password deve avere almeno 6 caratteri")
            else:
                if save_user(new_user, new_pass):
                    st.success("Account creato! Ora puoi fare il login.")
                else:
                    st.error("Username già esistente")
    return False
