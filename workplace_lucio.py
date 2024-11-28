import streamlit as st
import json
import os

# Funktionen für Benutzerverwaltung
def register_user(username, password):
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

def login_user(username, password):
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            users = json.load(file)
    else:
        st.error("No users found! Please register first.")
        return False

    return username in users and users[username] == password

# Speichern und Laden von Benutzer-Daten
def save_data(username, data):
    data_file = f"{username}_data.json"
    with open(data_file, "w") as file:
        json.dump(data, file)

def load_data(username):
    data_file = f"{username}_data.json"
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            return json.load(file)
    return {}

# Initialisierung des Session-States
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# Seitenlogik
if st.session_state["logged_in"]:
    # Haupt-Navigation für eingeloggte Benutzer
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Menu", ["Overview", "Fridge", "Scan", "Recipes", "Settings"])
    st.session_state["page"] = page

    if st.sidebar.button("Log Out", type="primary"):
        # Daten speichern und Session zurücksetzen
        if st.session_state["username"]:
            save_data(st.session_state["username"], st.session_state.get("data", {}))
        st.session_state.clear()
        st.session_state["logged_in"] = False
        st.session_state["page"] = "login"

# Login- und Registrierungsseite
if not st.session_state["logged_in"]:
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Menu", ["Log In", "Register"])

    st.title("Wasteless")
    if menu == "Log In":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Log In"):
            if login_user(username, password):
                st.success(f"Welcome, {username}!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["data"] = load_data(username)
                st.session_state["page"] = "overview"
            else:
                st.error("Incorrect username or password!")
    elif menu == "Register":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful! Please log in.")
            else:
                st.error("Username already exists!")

# Seiteninhalt für eingeloggte Benutzer
if st.session_state["logged_in"]:
    if st.session_state["page"] == "Overview":
        st.title("Overview")
        st.write("Welcome to the Overview page.")
    elif st.session_state["page"] == "Fridge":
        st.title("Fridge")
        st.write("This is the Fridge page.")
    elif st.session_state["page"] == "Scan":
        st.title("Scan")
        st.write("This is the Scan page.")
    elif st.session_state["page"] == "Recipes":
        st.title("Recipes")
        st.write("This is the Recipes page.")
    elif st.session_state["page"] == "Settings":
        st.title("Settings")
        st.write("This is the Settings page.")
