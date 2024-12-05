import streamlit as st # Creates app interface
import requests # To send http requests for API
import random # Enables radom selection
import pandas as pd # Library to handle data
from datetime import datetime 

# API-Key and URL for Spoonacular
API_KEY = '7c3d0f2a157542d9a49c93cdf50653a4'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# Initialization of session state variables and examples if nothing in session_state
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    }

if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf der Weise"]
if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = None
if "recipe_suggestions" not in st.session_state:
    st.session_state["recipe_suggestions"] = []
if "recipe_links" not in st.session_state:
    st.session_state["recipe_links"] = {}
if "selected_recipe" not in st.session_state:
    st.session_state["selected_recipe"] = None
if "selected_recipe_link" not in st.session_state:
    st.session_state["selected_recipe_link"] = None
if "cooking_history" not in st.session_state:
    st.session_state["cooking_history"] = []

# Recipe suggestion function
def get_recipes_from_inventory(selected_ingredients=None):
    ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
    if not ingredients:
        st.warning("Inventory is empty. Move your lazy ass to Migros!") # Warning message
        return [], {}
    
    # Sets up parameters for API
    params = {
        "ingredients": ",".join(ingredients),
        "number": 100,
        "ranking": 2,
        "apiKey": API_KEY
    }
    response = requests.get(SPOONACULAR_URL, params=params) # Get request for parameters
    
    if response.status_code == 200: # Checks if response from API was successfull
        recipes = response.json() # Processes JSON data ("our friend :)")
        recipe_titles = []
        recipe_links = {}
        displayed_recipes = 0

        random.shuffle(recipes)

        for recipe in recipes:
            missed_ingredients = recipe.get("missedIngredientCount", 0)
            if missed_ingredients <= 2:  # Allow up to 2 missing ingredients
                recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}" # Builds a link
                missed_ingredients_names = [item["name"] for item in recipe.get("missedIngredients", [])]
                
                # Store both link and missed ingredients for each recipe
                recipe_titles.append(recipe['title'])
                recipe_links[recipe['title']] = {
                    "link": recipe_link,
                    "missed_ingredients": missed_ingredients_names
                }
                displayed_recipes += 1
                
                if displayed_recipes >= 3: # Limits the display to 3 recipes
                    break
        return recipe_titles, recipe_links
    else:
        st.error("Error fetching recipes. Please check your API key and try again.")
        return [], {}

# Rating function - set up of interface and "star" rating
def rate_recipe(recipe_title, recipe_link):
    st.subheader(f"Rate the recipe: {recipe_title}")
    st.write(f"**{recipe_title}**: ([View Recipe]({recipe_link}))")
    rating = st.slider("Rate with stars (1-5):", 1, 5, key=f"rating_{recipe_title}")
    
    if st.button("Submit rating"): # Checks if button is clicked
        user = st.session_state["selected_user"]
        if user:
            st.success(f"You have rated '{recipe_title}' with {rating} stars!")
            st.session_state["cooking_history"].append({
                "Person": user,
                "Recipe": recipe_title,
                "Rating": rating,
                "Link": recipe_link,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            st.warning("Please select a user first.")

# Main application flow
def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    st.subheader("Delulu is not the solulu")
    
    if st.session_state["roommates"]: # Select one roommate
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate  # Save selected user to session state
        
        # Recipe Search Options
        st.subheader("Recipe search options")
        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))
        
        # Recipe selection form - custom or inventory
        with st.form("recipe_form"):
            if search_mode == "Custom (choose ingredients)":
                selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
            else:
                selected_ingredients = None  # Use the entire inventory
            
            search_button = st.form_submit_button("Get recipe suggestions")
            if search_button:
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state["recipe_suggestions"] = recipe_titles
                st.session_state["recipe_links"] = recipe_links

        # Display recipe suggestions with links only if they have been generated
        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make")
            for title in st.session_state["recipe_suggestions"]:
                link = st.session_state["recipe_links"][title]["link"]
                missed_ingredients = st.session_state["recipe_links"][title]["missed_ingredients"]

                st.write(f"- **{title}**: ([View Recipe]({link}))")
                if missed_ingredients:
                    st.write(f"  *Extra ingredients needed:* {', '.join(missed_ingredients)}")

            # Let the user choose one recipe to make
            selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + st.session_state["recipe_suggestions"])
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!")
                
    else:
        st.warning("No roommates available.")
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
            st.table(pd.DataFrame(history_data))

# Run the recipe page
recipepage()
