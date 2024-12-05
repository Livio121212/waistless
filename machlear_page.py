import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from .ml_model import train_user_model, predict_recipe_score, calculate_cuisine_ratings, get_unrated_cuisines

# API configuration
API_KEY = '7c3d0f2a157542d9a49c93cdf50653a4'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

def initialize_session_state():
    """Initialize all required session state variables"""
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
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {}
    if "ml_models" not in st.session_state:
        st.session_state["ml_models"] = {}
    if "user_low_rated_recipes" not in st.session_state:
        st.session_state["user_low_rated_recipes"] = {}

def get_recipe_cuisine(recipe_id):
    """Get cuisine type for a recipe from Spoonacular API"""
    try:
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        response = requests.get(url, params={"apiKey": API_KEY})
        if response.status_code == 200:
            data = response.json()
            cuisines = data.get("cuisines", [])
            return cuisines[0] if cuisines else "International"
    except:
        return "International"
    return "International"

def get_recipes_from_inventory(selected_ingredients=None, user=None):
    """Fetch recipes based on inventory and user preferences"""
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
    
    try:
        response = requests.get(SPOONACULAR_URL, params=params)
        if response.status_code == 200:
            recipes = response.json()
            recipe_scores = []
            
            # Get user's low-rated recipes
            user_low_rated = st.session_state["user_low_rated_recipes"].get(user, set())
            
            # Get user's cuisine preferences
            cuisine_ratings = calculate_cuisine_ratings(user) if user else {}
            unrated_cuisines = get_unrated_cuisines(user) if user else []
            
            for recipe in recipes:
                # Skip recipes that were rated 2 or lower by this user
                if recipe['title'] in user_low_rated:
                    continue
                    
                cuisine = get_recipe_cuisine(recipe['id'])
                
                # Calculate score based on ML model or cuisine ratings
                if user and cuisine_ratings:
                    score = predict_recipe_score(cuisine, user)
                else:
                    score = random.uniform(3, 5)
                
                recipe_scores.append((recipe, score, cuisine))
            
            # Sort recipes by predicted score
            recipe_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Select recipes based on preferences and random selection
            selected_recipes = []
            
            # Add one recipe from unrated cuisine if available
            if unrated_cuisines:
                unrated_recipes = [r for r in recipe_scores if r[2] in unrated_cuisines]
                if unrated_recipes:
                    selected_recipes.append(random.choice(unrated_recipes))
            
            # Add remaining recipes based on highest scores
            remaining_recipes = [r for r in recipe_scores if r not in selected_recipes]
            selected_recipes.extend(remaining_recipes[:2])
            
            # Format results
            recipe_titles = []
            recipe_links = {}
            
            for recipe, _, cuisine in selected_recipes:
                recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}"
                missed_ingredients = [item["name"] for item in recipe.get("missedIngredients", [])]
                
                recipe_titles.append(recipe['title'])
                recipe_links[recipe['title']] = {
                    "link": recipe_link,
                    "missed_ingredients": missed_ingredients,
                    "cuisine": cuisine
                }
            
            return recipe_titles, recipe_links
            
    except Exception as e:
        st.error(f"Error fetching recipes: {str(e)}")
        return [], {}

def rate_recipe(recipe_title, recipe_link, cuisine):
    """Handle recipe rating and update ML model"""
    st.subheader(f"Rate the recipe: {recipe_title}")
    st.write(f"**{recipe_title}**: ([View Recipe]({recipe_link}))")
    rating = st.slider("Rate with stars (1-5):", 1, 5, key=f"rating_{recipe_title}")
    
    if st.button("Submit rating"):
        user = st.session_state["selected_user"]
        if user:
            # Track low-rated recipes
            if rating <= 2:
                if user not in st.session_state["user_low_rated_recipes"]:
                    st.session_state["user_low_rated_recipes"][user] = set()
                st.session_state["user_low_rated_recipes"][user].add(recipe_title)
            
            # Add to cooking history
            st.session_state["cooking_history"].append({
                "Person": user,
                "Recipe": recipe_title,
                "Rating": rating,
                "Link": recipe_link,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Cuisine": cuisine
            })
            
            # Update user preferences for ML
            if user not in st.session_state["user_preferences"]:
                st.session_state["user_preferences"][user] = pd.DataFrame(columns=["Recipe", "Cuisine", "Rating"])
            
            new_rating = pd.DataFrame([{
                "Recipe": recipe_title,
                "Cuisine": cuisine,
                "Rating": rating
            }])
            
            st.session_state["user_preferences"][user] = pd.concat([
                st.session_state["user_preferences"][user],
                new_rating
            ], ignore_index=True)
            
            # Retrain model
            st.session_state["ml_models"][user] = train_user_model(user)
            
            st.success(f"You have rated '{recipe_title}' with {rating} stars!")
        else:
            st.warning("Please select a user first.")

def recipepage():
    """Main recipe page function"""
    st.title("You think you can cook! Better take a recipe!")
    st.subheader("Delulu is not the solulu")
    
    initialize_session_state()
    
    if st.session_state["roommates"]:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate
        
        # Display cuisine preferences if available
        if selected_roommate:
            cuisine_ratings = calculate_cuisine_ratings(selected_roommate)
            if cuisine_ratings:
                st.subheader("Your Cuisine Preferences")
                for cuisine, rating in cuisine_ratings.items():
                    st.write(f"{cuisine}: {rating:.1f}/5")
        
        st.subheader("Recipe search options")
        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))
        
        with st.form("recipe_form"):
            if search_mode == "Custom (choose ingredients)":
                selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
            else:
                selected_ingredients = None
            
            search_button = st.form_submit_button("Get recipe suggestions")
            if search_button:
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients, selected_roommate)
                st.session_state["recipe_suggestions"] = recipe_titles
                st.session_state["recipe_links"] = recipe_links

        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make")
            for title in st.session_state["recipe_suggestions"]:
                link = st.session_state["recipe_links"][title]["link"]
                missed_ingredients = st.session_state["recipe_links"][title]["missed_ingredients"]
                cuisine = st.session_state["recipe_links"][title]["cuisine"]

                st.write(f"- **{title}** ({cuisine}): ([View Recipe]({link}))")
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
        cuisine = st.session_state["recipe_links"][st.session_state["selected_recipe"]]["cuisine"]
        rate_recipe(
            st.session_state["selected_recipe"],
            st.session_state["selected_recipe_link"],
            cuisine
        )

    if st.session_state["cooking_history"]:
        with st.expander("Cooking History"):
            history_data = [
                {
                    "Person": entry["Person"],
                    "Recipe": entry["Recipe"],
                    "Rating": entry["Rating"],
                    "Date": entry["Date"],
                    "Cuisine": entry.get("Cuisine", "Unknown")
                }
                for entry in st.session_state["cooking_history"]
            ]
            st.table(pd.DataFrame(history_data))

if __name__ == "__main__":
    recipepage()