import streamlit as st # Creates app interface
import requests # To send http requests for API
import random # Enables radom selection
import pandas as pd # Library to handle data
from datetime import datetime 

# API-Key and URL for Spoonacular
API_KEY = '7c3d0f2a157542d9a49c93cdf50653a4e3a4' # Unique key to authenticate requests to the Spoonacular API
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients' # URL to find recipes

# Initialization of session state variables and examples if nothing in session_state
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0}, # Variables for inventory
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    }

# Initialize more session state variables for roommate and recipe-related data
if "roommates" not in st.session_state: # Define examples if nothing added
    st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf der Weise"] # Example rommates
if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = None # Keeps track of which user is selected
if "recipe_suggestions" not in st.session_state:
    st.session_state["recipe_suggestions"] = [] # Stores suggested recipe titles
if "recipe_links" not in st.session_state:
    st.session_state["recipe_links"] = {} # Stores recipe links and extra data
if "selected_recipe" not in st.session_state:
    st.session_state["selected_recipe"] = None # The recipe the user decides to cook
if "selected_recipe_link" not in st.session_state:
    st.session_state["selected_recipe_link"] = None # Link to the selected recipe
if "cooking_history" not in st.session_state:
    st.session_state["cooking_history"] = [] # History of recipes cooked and their ratings

# Function to suggest recipes based on the inventory
def get_recipes_from_inventory(selected_ingredients=None): # Optionally use selected ingredients
    # Use all inventory items if no specific ingredients are selected
    ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
    if not ingredients: # Check if the inventory is empty
        st.warning("Inventory is empty. Move your lazy ass to Migros!") # Warning message
        return [], {} 
    
    # Sets up parameters for API
    params = {
        "ingredients": ",".join(ingredients),
        "number": 100, # Max number of recipes to retrieve
        "ranking": 2, # Filter recipes based on ingredient match quality
        "apiKey": API_KEY
    }
    response = requests.get(SPOONACULAR_URL, params=params) # Send the HTTP GET request to the API
    
    if response.status_code == 200: # Checks if response from API was successfull
        recipes = response.json() # Parse the API response into a Python object
        recipe_titles = [] # List to store recipe titles
        recipe_links = {} # Dictionary to store links and missing ingredients
        displayed_recipes = 0 # Counter for recipes displayed

        random.shuffle(recipes) # Shuffle recipes in a random matter to add variety 

        for recipe in recipes: # Iterate through each recipe
            missed_ingredients = recipe.get("missedIngredientCount", 0) # Number of missing ingredients
            if missed_ingredients <= 2:  # Allow up to 2 missing ingredients
                 # Create a link to the recipe on Spoonacular
                recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}" # Builds a link
                missed_ingredients_names = [item["name"] for item in recipe.get("missedIngredients", [])]
                
                # Add recipe title and link to the lists
                recipe_titles.append(recipe['title'])
                recipe_links[recipe['title']] = {
                    "link": recipe_link,
                    "missed_ingredients": missed_ingredients_names
                }
                displayed_recipes += 1 # Adds recipe until break
                
                if displayed_recipes >= 3: # Limits the display to 3 recipes
                    break
        return recipe_titles, recipe_links
    else:
        st.error("Error fetching recipes. Please check your API key and try again.") # Warning message for API key
        return [], {}

# Function to let users rate a recipe
def rate_recipe(recipe_title, recipe_link):
    st.subheader(f"Rate the recipe: {recipe_title}") # Show recipe title
    st.write(f"**{recipe_title}**: ([View Recipe]({recipe_link}))") # Provide a clickable link
    # Slider to select a rating from 1 to 5
    rating = st.slider("Rate with stars (1-5):", 1, 5, key=f"rating_{recipe_title}")
    
    if st.button("Submit rating"): # Button to submit the rating
        user = st.session_state["selected_user"] # Get the selected user
        if user:
            st.success(f"You have rated '{recipe_title}' with {rating} stars!") # Success message
            st.session_state["cooking_history"].append({ # Creates a "Cookbook" with history of rating
                "Person": user, # Choosen user - under which rating is stored
                "Recipe": recipe_title,
                "Rating": rating,
                "Link": recipe_link,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Timestamp
            })
        else:
            st.warning("Please select a user first.") # Warning message

# Main function to run the recipe page
def recipepage():
    st.title("You think you can cook! Better take a recipe!") # Funny titles on page :)
    st.subheader("Delulu is not the solulu")
    
    if st.session_state["roommates"]: # Check if there are roommates to select
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"]) # Dropdown to select a roommate
        st.session_state["selected_user"] = selected_roommate  # Save selected user to session state
        
        # Section to choose how to search for recipes
        st.subheader("Recipe search options")
        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))
        
        # Recipe selection form - custom or inventory
        with st.form("recipe_form"):
            if search_mode == "Custom (choose ingredients)": # If user chooses to select specific ingredients
                selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
            else:
                selected_ingredients = None  # Use the entire inventory
            
            search_button = st.form_submit_button("Get recipe suggestions") # Button to get recipes
            if search_button:
                # Call the function to get recipes based on the selected ingredients
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state["recipe_suggestions"] = recipe_titles # Store recipe titel
                st.session_state["recipe_links"] = recipe_links # Store recipe link

        # Display recipe suggestions with links only if they have been generated
        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make") # Subtitle
            for title in st.session_state["recipe_suggestions"]: # Loop through suggested recipes
                link = st.session_state["recipe_links"][title]["link"]
                missed_ingredients = st.session_state["recipe_links"][title]["missed_ingredients"]

                 # Display the recipe title and link
                st.write(f"- **{title}**: ([View Recipe]({link}))")
                if missed_ingredients: # Show extra ingredients needed
                    st.write(f"  *Extra ingredients needed:* {', '.join(missed_ingredients)}")

            # Let the user choose one recipe to make
            selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + st.session_state["recipe_suggestions"])
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe # Save the selected recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!") # Success message
                
    else:
        st.warning("No roommates available.") # Warning message
        return

    # Display the rating section if a recipe was selected
    if st.session_state["selected_recipe"] and st.session_state["selected_recipe_link"]:
        rate_recipe(st.session_state["selected_recipe"], st.session_state["selected_recipe_link"])

    # Display cooking history in a table
    if st.session_state["cooking_history"]:
        with st.expander("Cooking History"):
            history_data = [
                {
                    "Person": entry["Person"],
                    "Recipe": entry["Recipe"],
                    "Rating": entry["Rating"],
                    "Date": entry["Date"]
                }
                for entry in st.session_state["cooking_history"]
            ]
            st.table(pd.DataFrame(history_data)) # Display the history as a table

# Run the recipe page
recipepage()
