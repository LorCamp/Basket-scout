import streamlit as st

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Accesso Riservato")
        def password_entered():
            if st.session_state["password"] == "BASKET2026": # Personalizzala qui
                st.session_state["password_correct"] = True
                del st.session_state["password"]
            else:
                st.session_state["password_correct"] = False

        st.text_input("Password:", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("Password errata")
        return False
    return st.session_state["password_correct"]
