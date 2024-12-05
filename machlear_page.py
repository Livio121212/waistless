import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


# API configuration
API_KEY = '7c3d0f2a157542d9a49c93cdf50653a4'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# Available cuisines for classification
CUISINES = ["Italian", "Asian", "Mexican", "Mediterranean", "American", "International"]

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
    # New ML-related session state variables
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {}
    if "ml_models" not in st.session_state:
        st.session_state["ml_models"] = {}
    if "recipe_features" not in st.session_state:
        st.session_state["recipe_features"] = pd.DataFrame()
    # Add new session state variable for storing low-rated recipes
    if "user_low_rated_recipes" not in st.session_state:
        st.session_state["user_low_rated_recipes"] = {}

def train_user_model(user):
    """Train ML model for a specific user based on their ratings"""
    if user not in st.session_state["user_preferences"]:
        st.session_state["user_preferences"][user] = pd.DataFrame(columns=["Recipe", "Cuisine", "Rating"])
        return None

    user_data = st.session_state["user_preferences"][user]
    if len(user_data) < 2:  # Need at least 2 ratings to train
        return None

    # Prepare features for training
    X = pd.get_dummies(user_data["Cuisine"])
    y = user_data["Rating"]

    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model

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

def predict_recipe_score(recipe_cuisine, user):
    """Predict score for a recipe based on user's preferences"""
    if user not in st.session_state["ml_models"] or st.session_state["ml_models"][user] is None:
        return np.random.uniform(3, 5)  # Return random score if no model exists

    # Create feature vector for prediction
    cuisine_features = pd.get_dummies([recipe_cuisine], columns=CUISINES)
    return st.session_state["ml_models"][user].predict(cuisine_features)[0]

def get_recipes_from_inventory(selected_ingredients=None, user=None):
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
            
            for recipe in recipes:
                # Skip recipes that were rated 2 or lower by this user
                if recipe['title'] in user_low_rated:
                    continue
                    
                cuisine = get_recipe_cuisine(recipe['id'])
                if user:
                    score = predict_recipe_score(cuisine, user)
                else:
                    score = np.random.uniform(3, 5)
                recipe_scores.append((recipe, score))
            
            # Sort recipes by predicted score
            recipe_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 3 recipes
            top_recipes = recipe_scores[:3]
            recipe_titles = []
            recipe_links = {}
            
            for recipe, score in top_recipes:
                recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}"
                missed_ingredients = [item["name"] for item in recipe.get("missedIngredients", [])]
                
                recipe_titles.append(recipe['title'])
                recipe_links[recipe['title']] = {
                    "link": recipe_link,
                    "missed_ingredients": missed_ingredients,
                    "cuisine": get_recipe_cuisine(recipe['id'])
                }
            
            return recipe_titles, recipe_links
    except Exception as e:
        st.error(f"Error fetching recipes: {str(e)}")
    return [], {}

def rate_recipe(recipe_title, recipe_link, cuisine):
    st.subheader(f"Rate the recipe: {recipe_title}")
    st.write(f"**{recipe_title}**: ([View Recipe]({recipe_link}))")
    rating = st.slider("Rate with stars (1-5):", 1, 5, key=f"rating_{recipe_title}")
    

    
    if st.button("Submit rating"):
        user = st.session_state["selected_user"]
        if user:
            # Initialize user's low-rated recipes set if it doesn't exist
            if user not in st.session_state["user_low_rated_recipes"]:
                st.session_state["user_low_rated_recipes"][user] = set()
            
            # Add to low-rated recipes if rating is 2 or lower
            if rating <= 2:
                st.session_state["user_low_rated_recipes"][user].add(recipe_title)
            elif recipe_title in st.session_state["user_low_rated_recipes"].get(user, set()):
                # Remove from low-rated if the rating is improved above 2
                st.session_state["user_low_rated_recipes"][user].remove(recipe_title)
            
            # Add rating to cooking history
            st.session_state["cooking_history"].append({
                "Person": user,
                "Recipe": recipe_title,
                "Rating": rating,
                "Link": recipe_link,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            
            # Retrain model for user
            st.session_state["ml_models"][user] = train_user_model(user)
            
            st.success(f"You have rated '{recipe_title}' with {rating} stars!")
        else:
            st.warning("Please select a user first.")

def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    st.subheader("Delulu is not the solulu")
    
    initialize_session_state()
    
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
                    "Date": entry["Date"]
                }
                for entry in st.session_state["cooking_history"]
            ]
            st.table(pd.DataFrame(history_data))

if __name__ == "__main__":
    recipepage()