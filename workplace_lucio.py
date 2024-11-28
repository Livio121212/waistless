import streamlit as st
import json
import os
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridge_page
from barcode_page import barcode_page
from recipe_page import recipepage

# Function to register a user
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

# Function to log in a user
def login_user(username, password):
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            users = json.load(file)
    else:
        st.error("No users found! Please register first.")
        return False

    if username in users and users[username] == password:
        return True
    else:
        st.error("Incorrect username or password!")
        return False

# Function to save WG data
def save_data(username, data):
    data_file = f"{username}_data.json"
    with open(data_file, "w") as file:
        json.dump(data, file)

# Function to load WG data
def load_data(username):
    data_file = f"{username}_data.json"
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            return json.load(file)
    else:
        return {}

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "data" not in st.session_state:
    st.session_state["data"] = {}

# Sidebar navigation and user handling
if st.session_state["logged_in"]:
    # Sidebar for navigation
    menu = st.sidebar.selectbox("Menu", ["Overview", "Fridge", "Scan", "Recipes", "Settings"])

    # Logout button
    if st.sidebar.button("Log Out", type="primary"):
        st.session_state.clear()  # Clear all session states
        st.session_state["logged_in"] = False  # Explicitly set logged_in to False
        st.experimental_set_query_params(page="login")  # Ensure URL state reflects logout
        st.session_state["force_rerun"] = True  # Trigger rerun
else:
    menu = st.sidebar.selectbox("Menu", ["Log In", "Register"])

# Login/Register logic
if not st.session_state["logged_in"]:
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
                st.experimental_set_query_params(page="main")  # Set URL to indicate logged-in state
    elif menu == "Register":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(username, password):
                st.success("Successfully registered! Please log in.")

# Ensure default session state variables are initialized
if "flate_name" not in st.session_state:
    st.session_state["flate_name"] = ""
if "roommates" not in st.session_state:
    st.session_state["roommates"] = []
if "setup_finished" not in st.session_state:
    st.session_state["setup_finished"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "settings"
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {}
if "expenses" not in st.session_state:
    st.session_state["expenses"] = {}
if "purchases" not in st.session_state:
    st.session_state["purchases"] = {}
if "consumed" not in st.session_state:
    st.session_state["consumed"] = {}
if "recipe_suggestions" not in st.session_state:
    st.session_state["recipe_suggestions"] = []
if "selected_recipe" not in st.session_state:
    st.session_state["selected_recipe"] = None
if "selected_recipe_link" not in st.session_state:
    st.session_state["selected_recipe_link"] = None
if "cooking_history" not in st.session_state:
    st.session_state["cooking_history"] = []
if "recipe_links" not in st.session_state:
    st.session_state["recipe_links"] = {}

# Main page handling for logged-in users
if st.session_state["logged_in"]:
    st.sidebar.title("Navigation")
    if st.sidebar.button("Overview"):
        st.session_state["page"] = "overview"
    if st.sidebar.button("Fridge"):
        st.session_state["page"] = "fridge"
    if st.sidebar.button("Scan"):
        st.session_state["page"] = "scan"
    if st.sidebar.button("Recipes"):
        st.session_state["page"] = "recipes"
    if st.sidebar.button("Settings"):
        st.session_state["page"] = "settings"

    # Display the selected page
    if st.session_state["page"] == "overview":
        st.title(f"Overview: {st.session_state['flate_name']}")
        st.write("Welcome to your WG overview page!")
    elif st.session_state["page"] == "fridge":
        fridge_page()
    elif st.session_state["page"] == "scan":
        barcode_page()
    elif st.session_state["page"] == "recipes":
        recipepage()
    elif st.session_state["page"] == "settings":
        if not st.session_state["setup_finished"]:
            if st.session_state["flate_name"] == "":
                setup_flat_name()
            else:
                setup_roommates()
        else:
            settingspage()
else:
    st.write("Please log in or register to continue.")
