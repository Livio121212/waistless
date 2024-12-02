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
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}
if "purchases" not in st.session_state:
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]}
if "consumed" not in st.session_state:
    st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]}

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

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "data" not in st.session_state:
    st.session_state["data"] = {}    


def overview_page():
    title = f"Overview: {st.session_state['flate_name']}" if st.session_state["flate_name"] else "Overview"
    st.title(title)
    st.write("In progress!!!")


def change_page(new_page):
    st.session_state["page"] = new_page


# CSS for circular image and sidebar navigation styling
custom_css = """
<style>
.circular-logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 180px;
    height: 180px;
    border-radius: 50%;
    background-color: black;
    margin: 20px auto;
}

.circular-logo {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    object-fit: cover;
}

.sidebar-box {
    padding: 20px;
    margin: 10px;
    border: 2px solid #ddd;
    border-radius: 10px;
    background-color: #f9f9f9;
    color: black;
}

.sidebar-box h3 {
    margin-top: 0;
    font-weight: bold;
}

.sidebar-box button {
    width: 100%;
    margin: 5px 0;
    padding: 10px;
    background-color: #007BFF;
    color: white;
    border: none;
    border-radius: 5px;
    text-align: left;
    cursor: pointer;
}

.sidebar-box button:hover {
    background-color: #0056b3;
}
</style>
"""

# Apply the CSS
st.sidebar.markdown(custom_css, unsafe_allow_html=True)

# Logo URL
logo_url = "https://raw.githubusercontent.com/Livio121212/waistless/main/Eco_Wasteless_Logo_Cropped.png"

# Sidebar Logo
st.sidebar.markdown(f"""
<div class="circular-logo-container">
    <img src="{logo_url}" class="circular-logo">
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
st.sidebar.markdown('<h3>Navigation</h3>', unsafe_allow_html=True)

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

st.sidebar.markdown('</div>', unsafe_allow_html=True)


# Main Page Display
if st.session_state["logged_in"]:
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
    st.title("Wasteless")
    st.write("Please log in or register to continue.")
    authentication()
