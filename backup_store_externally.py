import streamlit as st
import json
import os
from datetime import datetime
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridge_page
from barcode_page import barcode_page
from machlear_page import recipepage, initialize_session_state

# Initialize session state variables
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
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "data" not in st.session_state:
    st.session_state["data"] = {}
if "user_preferences" not in st.session_state:
    st.session_state["user_preferences"] = {}
if "ml_models" not in st.session_state:
    st.session_state["ml_models"] = {}
if "user_low_rated_recipes" not in st.session_state:
    st.session_state["user_low_rated_recipes"] = {}

def register_user(username, password):
    """Register a new user"""
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
    """Log in an existing user"""
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            users = json.load(file)
    else:
        st.error("No users found! Please sign up first.")
        return False
    
    if username in users and users[username] == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state.update(load_data(username))
        return True
    else:
        st.error("Incorrect username or password!")
        return False

def save_data(username, data):
    """Save user data to JSON file"""
    data_file = f"{username}_data.json"
    with open(data_file, "w") as file:
        json.dump(data, file)

def load_data(username):
    """Load user data from JSON file"""
    data_file = f"{username}_data.json"
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            return json.load(file)
    else:
        return {}

def authentication():
    """Handle user authentication"""
    if not st.session_state["logged_in"]:
        account = st.sidebar.selectbox("Account:", ["Sign in", "Sign up"])
        username = st.sidebar.text_input("Flat")
        password = st.sidebar.text_input("Password", type="password")

        if account == "Sign up":
            if st.sidebar.button("Sign up"):
                if register_user(username, password):
                    st.success("Successfully registered! Please sign in.")
        elif account == "Sign in":
            if st.sidebar.button("Sign in"):
                if login_user(username, password):
                    st.success(f"Welcome, {username}!")
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["data"] = load_data(username)
                    st.session_state.update(st.session_state["data"])

def auto_save():
    """Automatically save user data"""
    if "username" in st.session_state and st.session_state["username"]:
        st.session_state["data"] = {
            "flate_name": st.session_state.get("flate_name", ""),
            "roommates": st.session_state.get("roommates", []),
            "setup_finished": st.session_state.get("setup_finished", False),
            "inventory": st.session_state.get("inventory", {}),
            "expenses": st.session_state.get("expenses", {}),
            "purchases": st.session_state.get("purchases", {}),
            "consumed": st.session_state.get("consumed", {}),
            "recipe_suggestions": st.session_state.get("recipe_suggestions", []),
            "selected_recipe": st.session_state.get("selected_recipe", None),
            "selected_recipe_link": st.session_state.get("selected_recipe_link", None),
            "cooking_history": st.session_state.get("cooking_history", []),
            "recipe_links": st.session_state.get("recipe_links", {}),
            "user_preferences": st.session_state.get("user_preferences", {}),
            "user_low_rated_recipes": st.session_state.get("user_low_rated_recipes", {})
        }
        save_data(st.session_state["username"], st.session_state["data"])

def delete_account():
    """Delete user account and associated data"""
    with st.expander("Delete account"):
        st.warning("This action is irreversible. Deleting your account will remove all your data.")
        confirm = st.button("Delete account")
        if confirm:
            delete_data()
            st.session_state["logged_in"] = False

def delete_data():
    """Remove user data from storage"""
    username = st.session_state.get("username")
    if username:
        if os.path.exists("users.json"):
            with open("users.json", "r") as file:
                users = json.load(file)
            if username in users:
                del users[username]
                with open("users.json", "w") as file:
                    json.dump(users, file)
        
        data_file = f"{username}_data.json"
        if os.path.exists(data_file):
            os.remove(data_file)
    st.session_state.clear()