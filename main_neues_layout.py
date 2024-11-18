import streamlit as st
import pandas as pd
from PIL import Image
import requests
from datetime import datetime
from settings_page import setup_flat_name, setup_roommates, add_roommate, display_roommates, settingspage, change_flat_name, manage_roommates, remove_roommate
from fridge_page import delete_product_from_inventory, add_product_to_inventory, fridge_page, ensure_roommate_entries
from barcode_page import decode_barcode, get_product_info, display_total_expenses, display_purchases, barcode_page
from recipe_page import recipepage
from store_externally import register_user, login_user, save_data, load_data, authentication, auto_save, delete_account, delete_data


# Initialization of session state variables
# Flat related variables
if "flate_name" not in st.session_state:
    st.session_state["flate_name"] = ""
if "roommates" not in st.session_state:
    st.session_state["roommates"] = []
if "setup_finished" not in st.session_state:
    st.session_state["setup_finished"] = False

# Site status: first time setting page
if "page" not in st.session_state:
    st.session_state["page"] = "settings"

# Inventory and financial data
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {}
if "expenses" not in st.session_state:
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}
if "purchases" not in st.session_state:
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]}
if "consumed" not in st.session_state:
    st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]}

# Recipe related variables
if "recipe_suggestions" not in st.session_state:
    st.session_state["recipe_suggestions"] = []
if "selected_recipe" not in st.session_state:
    st.session_state["selected_recipe"] = None
if "recipe_links" not in st.session_state:
    st.session_state["recipe_links"] = {}
if "selected_recipe_link" not in st.session_state:
    st.session_state["selected_recipe_link"] = None
if "cooking_history" not in st.session_state:
    st.session_state["cooking_history"] = []

# Login-related variables
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "data" not in st.session_state:
    st.session_state["data"] = {}    

# Only temporarly: in progress
def overview_page():
    title = f"Overview: {st.session_state['flate_name']}" if st.session_state["flate_name"] else "Overview"
    st.title(title)
    st.write("In progress!!!")
 

# Function to change pages
def change_page(new_page):
    st.session_state["page"] = new_page

logo = "/Users/livioreding/Desktop/streamlit/Eco_Wasteless_Logo_Cropped.png"  # Pfad zu deinem Logo-Bild
st.sidebar.image(logo, use_column_width=True)


# Display of the main page
if st.session_state["logged_in"]:

    # Sidebar navigation without account selection
    st.sidebar.title("Navigation")
    if st.sidebar.button("Overview"):
        change_page("overview")
    if st.sidebar.button("Inventory"):
        change_page("inventory")
    if st.sidebar.button("Scan"):
        change_page("scan")
    if st.sidebar.button("Recipes"):
        change_page("recipes")
    if st.sidebar.button("Settings"):
        change_page("settings")
    if st.sidebar.button("Log Out", type="primary"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["data"] = {}


    # Page display logic for the selected page
    if st.session_state["page"] == "overview":
        overview_page()
        auto_save()
    elif st.session_state["page"] == "inventory":
        fridge_page()
        auto_save()
    elif st.session_state["page"] == "scan":
        barcode_page()
        auto_save()
    elif st.session_state["page"] == "recipes":
        recipepage()
        auto_save()
    elif st.session_state["page"] == "settings":
        if not st.session_state["setup_finished"]:
            if st.session_state["flate_name"] == "":
                setup_flat_name()
            else:
                setup_roommates()
        else:
            settingspage()
            delete_account()
        auto_save()
else:
    # Sidebar with account selection
    st.title("Wasteless")
    st.write("Please log in or register to continue.")
    authentication()