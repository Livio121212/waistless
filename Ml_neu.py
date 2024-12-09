import streamlit as st
import json
import os

# Funktion zum Registrieren eines Benutzers
def register_user(username, password):
    """Registriere einen neuen Benutzer."""
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            users = json.load(file)
    else:
        users = {}

    if username in users:
        st.error("Username already exists!")
        return False
    else:
        users[username] = password
        with open("users.json", "w") as file:
            json.dump(users, file)
        return True

# Funktion zum Einloggen eines Benutzers
def login_user(username, password):
    """Logge einen Benutzer ein."""
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            users = json.load(file)
    else:
        st.err
