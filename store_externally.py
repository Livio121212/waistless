import streamlit as st
import json
import os
from datetime import datetime
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridge_page
from barcode_page import barcode_page
from recipe_page import recipepage

# Ensure all session state variables are initialized, just for testing
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

# Function to register a user and save user in json
def register_user(username, password):
    if os.path.exists("users.json"): # Checks if there's already a file with the name of the user
        with open("users.json", "r") as file: # Opens data in read modus and closes it afterwards immediately
            users = json.load(file) # Change to python
    else:
        users = {}

    if username in users: 
        st.error("Username already exists!")
        return False
    else:
        users[username] = password # Username will be the key and password the value
        with open("users.json", "w") as file: # Opens file in write modus
            json.dump(users, file) # Write the data from the variable into the json file
        return True

# Function to log in
def login_user(username, password):
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            users = json.load(file) 
    else:
        st.error("No users found! Please sign up first.")
        return False
    
    # Checks if the user name exist and the password ist the right, if True then load the data
    if username in users and users[username] == password: 
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state.update(load_data(username)) # updates account data
        return True
    else:
        st.error("Incorrect username or password!")
        return False

# Function for saving user-data in a JSON file 
def save_data(username, data):
    data_file = f"{username}_data.json"
    with open(data_file, "w") as file: # Opens file in write modus
        json.dump(data, file)

# Function to load flat data
def load_data(username):
    data_file = f"{username}_data.json"
    if os.path.exists(data_file):
        with open(data_file, "r") as file: # Opens file in read modus
            return json.load(file)
    else:
        return {}

# Function to sign in or sign, displays only if not alreay signed in 
def authentication():
    if not st.session_state["logged_in"]:
        account = st.sidebar.selectbox("Account:", ["Sign in", "Sign up"])

        username = st.sidebar.text_input("Flat")
        password = st.sidebar.text_input("Password", type="password") 

        if account == "Sign up":
            if st.sidebar.button("Sign up"):
                if register_user(username, password): # Function to register user
                    st.success("Successfully registered! Please sign in.")
        elif account == "Sign in":
            if st.sidebar.button("Sign in"):
                if login_user(username, password): # Function to sign in
                    st.success(f"Welcome, {username}!")
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    
                    # load data from JSON file into session_state
                    st.session_state["data"] = load_data(username)
                    st.session_state.update(st.session_state["data"])

# Function to automatically save flat data
def auto_save():
    if "username" in st.session_state and st.session_state["username"]: # Saves data only when a user is signed in
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
            "recipe_links": st.session_state.get("recipe_links", {})
        }
        save_data(st.session_state["username"], st.session_state["data"]) # Function for saving user-data in a JSON file 



# Function to delete the account
def delete_account():
    with st.expander("Delete account"):
        st.warning("This action is irreversible. Deleting your account will remove all your data.")
        confirm = st.button("Delete account")
        if confirm:
            delete_data() 
            st.session_state["logged_in"] = False # Used that we can sign in or sign up again

# Function to remove the user from the JSON file
def delete_data():
    username = st.session_state.get("username")
    if username:
        # Remove the user-specific data: username and password
        if os.path.exists("users.json"):
            with open("users.json", "r") as file: # Opens data in read modus and closes it afterwards immediately
                users = json.load(file)
            if username in users:
                del users[username] # Removes the user name from the dictionary
                with open("users.json", "w") as file: # Opens the file in write mode and overwrites the data
                    json.dump(users, file)
        
        # Removing the user-specific data file: inventory expenses...
        data_file = f"{username}_data.json"
        if os.path.exists(data_file):
            os.remove(data_file)
    st.session_state.clear()
        

# Display of the main page
if st.session_state["logged_in"]:

    # Sidebar navigation without account selection
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
    if st.sidebar.button("Log Out", type="primary"): # Log out button
        st.session_state["logged_in"] = False 
        st.session_state["username"] = None
        st.session_state["data"] = {}

    # Page display logic for the selected page
    if st.session_state["page"] == "overview":
        st.title(f"Overview: {st.session_state['flate_name']}")
        st.write("Welcome to your WG overview page!")
        auto_save()  # Automatically save data
    elif st.session_state["page"] == "fridge":
        fridge_page()
        auto_save()  # Automatically save data
    elif st.session_state["page"] == "scan":
        barcode_page()
        auto_save()  # Automatically save data
    elif st.session_state["page"] == "recipes":
        recipepage()
        auto_save()  # Automatically save data
    elif st.session_state["page"] == "settings":
        if not st.session_state["setup_finished"]:
            if st.session_state["flate_name"] == "":
                setup_flat_name()
            else:
                setup_roommates()
        else:
            settingspage()
            delete_account()
        auto_save()  # Automatically save data
else:
    # Sidebar with account selection
    st.title("Wasteless")
    st.write("Please sign in or sign up to continue.")
    authentication()
