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
if "page" not in st.session_state:
    st.session_state["page"] = "login"  # Default page

# Handle Logout: Redirect to Login
if "logout_triggered" in st.session_state and st.session_state["logout_triggered"]:
    st.session_state.clear()  # Clear all session states
    st.session_state["logged_in"] = False
    st.session_state["page"] = "login"  # Redirect to login page
    del st.session_state["logout_triggered"]  # Remove the trigger
    st.experimental_rerun()  # Force reload the app

# Sidebar logic based on login status
if st.session_state["logged_in"]:
    # Sidebar for navigation if user is logged in
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("Menu", ["Overview", "Fridge", "Scan", "Recipes", "Settings"])

    # Logout button
    if st.sidebar.button("Log Out", type="primary"):
        save_data(st.session_state["username"], st.session_state["data"])  # Save data before logout
        st.session_state["logout_triggered"] = True  # Set a trigger for logout

    # Handle navigation for logged-in users
    if menu == "Overview":
        st.title("Overview")
        st.write("Welcome to the overview page.")
    elif menu == "Fridge":
        fridge_page()
    elif menu == "Scan":
        barcode_page()
    elif menu == "Recipes":
        recipepage()
    elif menu == "Settings":
        if not st.session_state["setup_finished"]:
            if st.session_state["flate_name"] == "":
                setup_flat_name()
            else:
                setup_roommates()
        else:
            settingspage()

else:
    # Sidebar for login and register options if user is not logged in
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Menu", ["Log In", "Register"])

    # Login/Register logic
    if menu == "Log In":
        st.title("Wasteless - Log In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Log In"):
            if login_user(username, password):
                st.success(f"Welcome, {username}!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["data"] = load_data(username)
                st.session_state["page"] = "main"  # Redirect to main dashboard
                st.experimental_rerun()
    elif menu == "Register":
        st.title("Wasteless - Register")
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
