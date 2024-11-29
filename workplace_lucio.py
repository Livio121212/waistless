import streamlit as st
import json
import os
import pandas as pd
from PIL import Image
from datetime import datetime
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridge_page
from barcode_page import barcode_page
from recipe_page import recipepage


#register a user
def register_user(username, password):
    if os.path.exists("users.json"): #check if data file already exists
        with open("users.json", "r") as file: #open dataset if it already exists, "r" means it's only in "read mode"
            users = json.load(file) #load file an content into users
    else:
        users = {} #if user doen't exist create an empty dictionary

    if username in users: #check if username already exists
        st.error("Username already exists!") #show an error message if user already exists
        return False #stop the function
    else:
        users[username] = password #if username doesn't exist, add a new dictionary
        with open("users.json", "w") as file: #"w" -> overwrite with new data
            json.dump(users, file) #save the dictionary into the file ->
        return True #signal successful registration

#user login
def login_user(username, password):
    if os.path.exists("users.json"): #check if file exists
        with open("users.json", "r") as file: #if not open in read mode
            users = json.load(file) #load data into dic. users
    else:
        st.error("No users found! Please register first.") #if user not found instrution to register
        return False #stop function

    if username in users and users[username] == password:#check username already exists in dic. and if password matches the one that was saved in the json file
        return True
    else:
        st.error("Incorrect username or password!") #error message if either username doesn't exist or password incorrect
        return False #stop funtion

# Save Wg data like roommates,fridge inventory, etc
def save_data(username, data):
    data_file = f"{username}_data.json" #create file based on the user
    with open(data_file, "w") as file: #open file in "write mode (w)", so that existing content can be replaced
        json.dump(data, file) #turn data into json format

# load WG data when user logs in
def load_data(username): #load data that was saved
    data_file = f"{username}_data.json" # look for file named after username
    if os.path.exists(data_file):
        with open(data_file, "r") as file: #if data exists it is loaded and returned into python dic.
            return json.load(file)
    else:
        return {} #return empty dic. -> no saved data

# Initialize session state to store data temporarly while using waistless, otherwise data would reset
if "logged_in" not in st.session_state: #CHeck if logged in
    st.session_state["logged_in"] = False
if "username" not in st.session_state:#store name of logged in user
    st.session_state["username"] = None
if "data" not in st.session_state:#store data like inventory, expenses, etc
    st.session_state["data"] = {}

menu = st.sidebar.selectbox("Menu", ["Log In", "Register"]) #show dropdown menu for log in and registration

#show a title when user is not logged in
if not st.session_state["logged_in"]:
    st.title("Wasteless")

#Check if a user clicks on "regiser" while logged in
if st.session_state["logged_in"] and menu == "Register":
    #make sure to log out first
    st.session_state["logged_in"] = False #no longer logged in
    st.session_state["username"] = None #clear logged in name
    st.session_state["data"] = {} #clear user data
    st.experimental_set_query_params()  # Simulate a rerun by setting query params
    st.stop()  #stop execution

#if user is not logged
if not st.session_state["logged_in"]: #code runs when user is not logged in
    username = st.sidebar.text_input("Username") #display field for input
    password = st.sidebar.text_input("Password", type="password") #show password as dots (type password)
    
    #registration
    if menu == "Register":
        if st.sidebar.button("Register"):
            if register_user(username, password):#calls the defined funtion for registration
                st.success("Successfully registered! Please log in.")
    elif menu == "Log In":#runs if user clicks on login button
        if st.sidebar.button("Log In"):
            if login_user(username, password):#call the defined login function
                st.success(f"Welcome, {username}!") #welcome user if succesful
                st.session_state["logged_in"] = True #mark user as logged in
                st.session_state["username"] = username #save name
                #load WG data from json and assign to session state
                st.session_state["data"] = load_data(username)
                #make data avilable as separat keys -> helps to simplify the code and makes data available throughput the app
                st.session_state.update(st.session_state["data"])

#initialize all session state variables
if "flate_name" not in st.session_state: #store name of flat
    st.session_state["flate_name"] = ""
if "roommates" not in st.session_state: #store list of roomates
    st.session_state["roommates"] = []
if "setup_finished" not in st.session_state:#track if setup of flat is complete
    st.session_state["setup_finished"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "settings" #app starts on settings page so that roomates can be registered
if "inventory" not in st.session_state:# track items in fridge
    st.session_state["inventory"] = {}
if "expenses" not in st.session_state:#track expenses
    st.session_state["expenses"] = {}
if "purchases" not in st.session_state: #track individual purchases
    st.session_state["purchases"] = {}
if "consumed" not in st.session_state: #track consumed items
    st.session_state["consumed"] = {}
if "recipe_suggestions" not in st.session_state: #track a list
    st.session_state["recipe_suggestions"] = []
if "selected_recipe" not in st.session_state: #track currently selected recipe
    st.session_state["selected_recipe"] = None
if "selected_recipe_link" not in st.session_state:#store link for currently selected recipe
    st.session_state["selected_recipe_link"] = None
if "cooking_history" not in st.session_state: #keep record of cooked meals
    st.session_state["cooking_history"] = []
if "recipe_links" not in st.session_state:#track all recipe names and their links
    st.session_state["recipe_links"] = {}

#show main page if user is logged in
if st.session_state["logged_in"]:
    #add clickable sidebar
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

    #make logout button red
    if st.sidebar.button("Log Out", type="primary"):#add logout button -> "primary" so that it is more visible
        st.session_state["logged_in"] = False #logout of user
        st.session_state["username"] = None #clear name
        st.session_state["data"] = {} #clear data
        st.write("Please reload the page")  #display after logout
        st.experimental_set_query_params()  #page refresh by resetting parameters
        st.stop()  #stop execution, prevent script from running

    #function makes sure to save data automatically
    def auto_save():
        st.session_state["data"] = { #collect all relevant variables in dic. and store in st.session_state
            "flate_name": st.session_state.get("flate_name", ""), #check if key exist in session state, if so retrieve value. 
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
        save_data(st.session_state["username"], st.session_state["data"]) #save data in jsonfile

    #page logic
    if st.session_state["page"] == "overview":#checks which page the user is looling at
        st.title(f"Overview: {st.session_state['flate_name']}") #display title form overview page with flat name
        st.write("Welcome to your WG overview page!")
        auto_save()  #auto saving
    elif st.session_state["page"] == "fridge":
        fridge_page()
        auto_save()  #auto saving
    elif st.session_state["page"] == "scan":
        barcode_page()
        auto_save()  #auto saving
    elif st.session_state["page"] == "recipes":
        recipepage()
        auto_save()  #auto save
    elif st.session_state["page"] == "settings": #check if flatname is empty
        if not st.session_state["setup_finished"]:
            if st.session_state["flate_name"] == "": #guide user through setup
                setup_flat_name()
            else:
                setup_roommates()#once flatname is added guide user trough setup of roommates
        else:
            settingspage() #if setup finshed display setting page
        auto_save()  #auto saving
else:
    st.write("Please log in or register to continue.") #is displayed if user in not registered/logged in
