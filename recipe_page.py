import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime

# API Configuration
API_KEY = '7c3d0f2a157542d9a49c93cdf50653a4'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# Supported cuisines
SUPPORTED_CUISINES = ['Italian', 'Asian', 'Mexican', 'Mediterranean', 'Indian', 'American']

def determine_cuisine_type(recipe_title):
    """Determine cuisine type based on recipe title"""
    title_lower = recipe_title.lower()
    
    if any(word in title_lower for word in ['pasta', 'pizza', 'risotto', 'italian']):
        return 'Italian'
    if any(word in title_lower for word in ['curry', 'masala', 'tikka', 'indian']):
        return 'Indian'
    if any(word in title_lower for word in ['taco', 'burrito', 'enchilada', 'mexican']):
        return 'Mexican'
    if any(word in title_lower for word in ['stir fry', 'sushi', 'ramen', 'asian']):
        return 'Asian'
    if any(word in title_lower for word in ['burger', 'bbq', 'grill', 'american']):
        return 'American'
    if any(word in title_lower for word in ['mediterranean', 'greek', 'hummus']):
        return 'Mediterranean'
    
    return random.choice(SUPPORTED_CUISINES)

# Initialize session state
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

def get_recipes_from_inventory(selected_ingredients=None):
    ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
    if not ingredients:
        st.warning("Inventory is empty. Move your lazy ass to Migros!")
        return [], {}
    
    params = {
        "ingredients": ",".join(ingredients),
        "number": 100,
        "ranking": 2,
        "apiKey": API_KEY
    }
    response = requests.get(SPOONACULAR_URL, params=params)
    
    if response.status_code == 200:
        recipes = response.json()
        recipe_titles = []
        recipe_links = {}
        displayed_recipes = 0
        used_cuisines = set()

        random.shuffle(recipes)

        for recipe in recipes:
            if displayed_recipes >= 3:
                break
                
            missed_ingredients = recipe.get("missedIngredientCount", 0)
            if missed_ingredients <= 2:
                recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}"
                missed_ingredients_names = [item["name"] for item in recipe.get("missedIngredients", [])]
                cuisine_type = determine_cuisine_type(recipe['title'])
                
                if cuisine_type not in used_cuisines or len(recipe_titles) < 3:
                    recipe_titles.append(recipe['title'])
                    recipe_links[recipe['title']] = {
                        "link": recipe_link,
                        "missed_ingredients": missed_ingredients_names,
                        "cuisine": cuisine_type
                    }
                    used_cuisines.add(cuisine_type)
                    displayed_recipes += 1
                
        return recipe_titles, recipe_links
    else:
        st.error("Error fetching recipes. Please check your API key and try again.")
        return [], {}

def rate_recipe(recipe_title, recipe_link):
    st.subheader(f"Rate the recipe: {recipe_title}")
    st.write(f"**{recipe_title}**: ([View Recipe]({recipe_link}))")
    rating = st.slider("Rate with stars (1-5):", 1, 5, key=f"rating_{recipe_title}")
    
    if st.button("Submit rating"):
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

def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    st.subheader("Delulu is not the solulu")
    
    if st.session_state["roommates"]:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate
        
        st.subheader("Recipe search options")
        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))
        
        with st.form("recipe_form"):
            if search_mode == "Custom (choose ingredients)":
                selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
            else:
                selected_ingredients = None
            
            search_button = st.form_submit_button("Get recipe suggestions")
            if search_button:
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state["recipe_suggestions"] = recipe_titles
                st.session_state["recipe_links"] = recipe_links

        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make")
            for title in st.session_state["recipe_suggestions"]:
                link = st.session_state["recipe_links"][title]["link"]
                missed_ingredients = st.session_state["recipe_links"][title]["missed_ingredients"]
                cuisine = st.session_state["recipe_links"][title]["cuisine"]

                st.write(f"- **{title}** ({cuisine} cuisine): ([View Recipe]({link}))")
                if missed_ingredients:
                    st.write(f"  *Extra ingredients needed:* {', '.join(missed_ingredients)}")

            selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + st.session_state["recipe_suggestions"])
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!")
                
    else:
        st.warning("No roommates available.")
        return

    if st.session_state["selected_recipe"] and st.session_state["selected_recipe_link"]:
        rate_recipe(st.session_state["selected_recipe"], st.session_state["selected_recipe_link"])

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

if __name__ == "__main__":
    recipepage()