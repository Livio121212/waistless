import streamlit as st
import json
import os

# Funktionen für Benutzerverwaltung
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file)

def register_user(username, password):
    users = load_users()
    if username in users:
        st.error("Username already exists!")
        return False
    users[username] = password
    save_users(users)
    return True

def login_user(username, password):
    users = load_users()
    return username in users and users[username] == password

# Funktion zum Speichern und Laden von Benutzer-Daten
def save_data(username, data):
    with open(f"{username}_data.json", "w") as file:
        json.dump(data, file)

def load_data(username):
    if os.path.exists(f"{username}_data.json"):
        with open(f"{username}_data.json", "r") as file:
            return json.load(file)
    return {}

# Initialisiere den Session-State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "data" not in st.session_state:
    st.session_state["data"] = {}

# Login/Logout-Logik
if st.session_state["logged_in"]:
    # Navigation und Logout
    st.sidebar.title("Navigation")
    st.session_state["page"] = st.sidebar.radio("Menu", ["Overview", "Fridge", "Scan", "Recipes", "Settings"])
    if st.sidebar.button("Log Out", type="primary"):
        save_data(st.session_state["username"], st.session_state["data"])
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["data"] = {}
        st.session_state["page"] = "login"
        st.experimental_rerun()
else:
    # Login und Registrierung
    menu = st.sidebar.radio("Menu", ["Log In", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if menu == "Log In" and st.button("Log In"):
        if login_user(username, password):
            st.success(f"Welcome, {username}!")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["data"] = load_data(username)
            st.session_state["page"] = "overview"
            st.experimental_rerun()
        else:
            st.error("Incorrect username or password!")

    if menu == "Register" and st.button("Register"):
        if register_user(username, password):
            st.success("Registration successful! Please log in.")
        else:
            st.error("Registration failed. Username might already exist.")

# Seiteninhalt abhängig vom Status und der Seite
if st.session_state["logged_in"]:
    st.title(f"Welcome, {st.session_state['username']}!")
    if st.session_state["page"] == "Overview":
        st.write("This is the Overview page.")
    elif st.session_state["page"] == "Fridge":
        st.write("This is the Fridge page.")
    elif st.session_state["page"] == "Scan":
        st.write("This is the Scan page.")
    elif st.session_state["page"] == "Recipes":
        st.write("This is the Recipes page.")
    elif st.session_state["page"] == "Settings":
        st.write("This is the Settings page.")
else:
    st.title("Wasteless")
    st.write("Please log in or register to continue.")
