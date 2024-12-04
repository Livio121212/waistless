import streamlit as st
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridge_page
from barcode_page import barcode_page
from recipe_page import recipepage
from store_externally import authentication, auto_save, delete_account
from Overview_page import Overview_page

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

 

# Function to change pages
def change_page(new_page):
    st.session_state["page"] = new_page


# CSS for circular image
circular_image_css = """
<style>
.circular-logo {
    display: block;
    margin: 0 auto;
    width: 150px;
    height: 150px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #ddd;
}
</style>
"""

# Logo URL
logo_url = "https://raw.githubusercontent.com/Livio121212/waistless/main/Eco_Wasteless_Logo_Cropped.png"

# Apply CSS and display the logo
st.sidebar.markdown(circular_image_css, unsafe_allow_html=True)
st.sidebar.markdown(f'<img src="{logo_url}" class="circular-logo">', unsafe_allow_html=True)

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