import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime

# API Configuration
API_KEY = '7c3d0f2a157542d9a49c93cdf50653a4'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'
CUISINE_CLASSIFIER_URL = 'https://api.spoonacular.com/recipes/cuisine'

# Session state initialization
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

def get_cuisine_type(recipe_title, ingredients_list=""):
    """Function to classify the cuisine type of a recipe with improved accuracy"""
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Create a more detailed ingredient list for better classification
    data = {
        'apiKey': API_KEY,
        'title': recipe_title,
        'ingredientList': ingredients_list or recipe_title
    }
    
    cuisines = [
        'Italian', 'Asian', 'Mexican', 'American', 'Mediterranean', 
        'Indian', 'Chinese', 'Japanese', 'Thai', 'French', 'Greek',
        'Spanish', 'Korean', 'Vietnamese', 'Middle Eastern'
    ]
    
    try:
        response = requests.post(CUISINE_CLASSIFIER_URL, headers=headers, data=data)
        if response.status_code == 200:
            cuisine_data = response.json()
            cuisine = cuisine_data.get('cuisine', '')
            confidence = cuisine_data.get('confidence', 0)
            
            # If the API returns a valid cuisine with good confidence, use it
            if cuisine and cuisine != 'Unknown' and confidence > 0.5:
                return cuisine
            
            # If we have ingredients in the title, try to guess the cuisine
            title_lower = recipe_title.lower()
            for keyword, cuisine in [
                (['pasta', 'pizza', 'risotto'], 'Italian'),
                (['curry', 'masala', 'tikka'], 'Indian'),
                (['taco', 'burrito', 'enchilada'], 'Mexican'),
                (['sushi', 'ramen', 'udon'], 'Japanese'),
                (['pad thai', 'curry'], 'Thai'),
                (['burger', 'bbq', 'mac and cheese'], 'American'),
                (['gyro', 'souvlaki', 'moussaka'], 'Greek'),
                (['paella', 'gazpacho'], 'Spanish'),
                (['pho', 'banh mi'], 'Vietnamese'),
                (['kimchi', 'bulgogi'], 'Korean'),
                (['hummus', 'falafel', 'shawarma'], 'Middle Eastern')
            ]:
                if any(k in title_lower for k in keyword):
                    return cuisine
            
            # If we still don't have a cuisine, pick a random one but exclude previously used ones
            used_cuisines = [
                recipe.get('cuisine', '') 
                for recipe in st.session_state.get("recipe_links", {}).values()
            ]
            available_cuisines = [c for c in cuisines if c not in used_cuisines]
            
            if available_cuisines:
                return random.choice(available_cuisines)
            else:
                return random.choice(cuisines)
    except:
        # If API fails, try to guess from title or return a random cuisine
        return random.choice(cuisines)

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
                
                # Create ingredient list for better cuisine classification
                all_ingredients = [item["name"] for item in recipe.get("usedIngredients", [])]
                all_ingredients.extend(missed_ingredients_names)
                ingredients_list = ", ".join(all_ingredients)
                
                # Get cuisine type with improved accuracy
                cuisine_type = get_cuisine_type(recipe['title'], ingredients_list)
                
                # Only add recipe if we haven't seen this cuisine type yet or we need more recipes
                if cuisine_type not in used_cuisines or len(used_cuisines) >= 3:
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
                cuisine = st.session_state["recipe_links"][title].get("cuisine", "Unknown")

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

recipepage()