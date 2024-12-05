# Importing necessary libraries and custom modules
import streamlit as st # Create interactive web applications
# Importing subpages and functions
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridgepage
from barcode_page import barcode_page
from machlear_page import recipepage
from store_externally import authentication, auto_save, delete_account
from Overview_page import overview_page

# Initialization of session state variables
# Flat related variables
if "flate_name" not in st.session_state: # Store the flat's name
    st.session_state["flate_name"] = "" # Initialize as an empty string
if "roommates" not in st.session_state: # Store the list of roommates
    st.session_state["roommates"] = [] # Initialize as an empty list
if "setup_finished" not in st.session_state: # Track whether the setup is complete
    st.session_state["setup_finished"] = False # Default is not finished

# Site status: first time setting page
if "page" not in st.session_state: # Store the current page
    st.session_state["page"] = "settings" # Start with the settings page

# Inventory and financial data
if "inventory" not in st.session_state: # Store inventory items
    st.session_state["inventory"] = {} # Initialize as an empty dictionary
if "expenses" not in st.session_state: # Store expenses by roommate
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]} # Default to 0.0 for each roommate
if "purchases" not in st.session_state: # Store purchase history for each roommate
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]} # Default to empty lists
if "consumed" not in st.session_state:# Store consumed items for each roommate
    st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]} # Default to empty lists

# Recipe related variables
if "recipe_suggestions" not in st.session_state: # Store recipe suggestions
    st.session_state["recipe_suggestions"] = [] # Initialize as an empty list
if "selected_recipe" not in st.session_state: # Track the selected recipe
    st.session_state["selected_recipe"] = None # Default is none
if "recipe_links" not in st.session_state: # Store recipe links
    st.session_state["recipe_links"] = {} # Initialize as an empty dictionary
if "selected_recipe_link" not in st.session_state: # Store the link to the selected recipe
    st.session_state["selected_recipe_link"] = None # Default is none
if "cooking_history" not in st.session_state: # Store the history of cooked recipes
    st.session_state["cooking_history"] = [] # Initialize as an empty list

# Login-related variables
if "logged_in" not in st.session_state: # Track login status
    st.session_state["logged_in"] = False # Default is logged out
if "username" not in st.session_state: # Store the username of the logged-in user
    st.session_state["username"] = None # Default is none
if "data" not in st.session_state: # Store user-related data
    st.session_state["data"] = {} # Initialize as an empty dictionary   

 

# Function to change pages
def change_page(new_page):
    st.session_state["page"] = new_page # Update the session state


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
st.sidebar.markdown(circular_image_css, unsafe_allow_html=True) # Apply the CSS
st.sidebar.markdown(f'<img src="{logo_url}" class="circular-logo">', unsafe_allow_html=True) # Display the logo in the sidebar

# Display of the main page
if st.session_state["logged_in"]: # Check if the user is logged in

    # Sidebar navigation without account selection
    st.sidebar.title("Navigation") # Title for the navigation menu
    if st.sidebar.button("Overview"): # Navigate to the overview page
        change_page("overview")
    if st.sidebar.button("Inventory"): # Navigate to the inventory page
        change_page("inventory")
    if st.sidebar.button("Scan"): # Navigate to the barcode scanning page
        change_page("scan")
    if st.sidebar.button("Recipes"): # Navigate to the recipes page
        change_page("recipes")
    if st.sidebar.button("Settings"): # Navigate to the settings page
        change_page("settings")
    if st.sidebar.button("Log Out", type="primary"): # Log out the user
        st.session_state["logged_in"] = False # Update login status
        st.session_state["username"] = None # Clear username
        st.session_state["data"] = {} # Clear user data


    # Page display logic for the selected page
    if st.session_state["page"] == "overview": # If the overview page is selected:
        overview_page() # Display the overview page
        auto_save() # Automatically save data
    elif st.session_state["page"] == "inventory": # If the inventory page is selected
        fridge_page() # Display the inventory page
        auto_save() # Automatically save data
    elif st.session_state["page"] == "scan": # If the scan page is selected:
        barcode_page() # Display the barcode scanning page
        auto_save() # Automaticaly save data
    elif st.session_state["page"] == "recipes": # If the recipes page is selected:
        recipepage() # Display the recipe page
        auto_save() # Automatically save data
    elif st.session_state["page"] == "settings": # If the settings page is selected:
        if not st.session_state["setup_finished"]: # If the setup is incomplete:
            if st.session_state["flate_name"] == "": # If the flat's name is not set:
                setup_flat_name() # Prompt to set the flat's name
            else:
                setup_roommates() # Prompt to set up roommates
        else:
            settingspage() # Display the settings page
            delete_account() # Option to delete the account
        auto_save() # Automatically save data
else:
    # Sidebar with account selection
    st.title("Wasteless") # Display the app's name
    st.write("Please log in or register to continue.") # Prompt the user to log in or register
    authentication() # Call the authentication function to handle login/registration