import streamlit as st
import pandas as pd
import requests
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import re

# API configuration
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# Available cuisines
CUISINES = ["International", "Italian", "Asian", "Mexican", "Mediterranean", "American"]

def initialize_session_state():
    """Initialize all required session state variables"""
    if "preferences_set" not in st.session_state:
        st.session_state["preferences_set"] = False
    if "recipe_data" not in st.session_state:
        st.session_state["recipe_data"] = pd.DataFrame(columns=[
            "Recipe", "Cuisine", "Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"
        ])
    if "user_ratings" not in st.session_state:
        st.session_state["user_ratings"] = pd.DataFrame(columns=["Recipe", "Rating", "Cuisine"])
    if "ml_model" not in st.session_state:
        st.session_state["ml_model"] = None
    if "scaler" not in st.session_state:
        st.session_state["scaler"] = StandardScaler()
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {
            "Spicy": 3, "Sweet": 3, "Salty": 3,
            "Sour": 3, "Bitter": 3, "Umami": 3
        }
    if "selected_cuisine" not in st.session_state:
        st.session_state["selected_cuisine"] = "International"
    if "ingredients_input" not in st.session_state:
        st.session_state["ingredients_input"] = ""

def get_recipes(ingredients, cuisine):
    """Fetch recipes based on ingredients and cuisine"""
    try:
        params = {
            "ingredients": ",".join(ingredients),
            "number": 10,
            "apiKey": API_KEY
        }

        response = requests.get(SPOONACULAR_URL, params=params)
        response.raise_for_status()
        recipes = response.json()
        
        filtered_recipes = []
        for recipe in recipes:
            recipe_id = recipe.get("id")
            title = recipe.get("title")
            
            if not recipe_id or not title:
                continue
                
            detailed_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
            detailed_response = requests.get(detailed_url, params={"apiKey": API_KEY})
            recipe_details = detailed_response.json()
            
            recipe_cuisine = recipe_details.get("cuisines", ["International"])[0]
            if cuisine != "International" and recipe_cuisine != cuisine:
                continue
                
            recipe["cuisine"] = recipe_cuisine
            recipe["details"] = recipe_details
            filtered_recipes.append(recipe)
            
        return filtered_recipes

    except requests.RequestException as e:
        st.error(f"Error fetching recipes: {str(e)}")
        return []

def predict_recipe_score(recipe_data):
    """Calculate recipe score based on user preferences"""
    taste_features = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]
    
    taste_similarity = sum(
        1 - abs(recipe_data[taste] - st.session_state["user_preferences"][taste]) / 4
        for taste in taste_features
    ) / len(taste_features)
    
    return taste_similarity * 5

def main():
    """Main function to run the recipe recommendation application"""
    st.title("Smart Recipe Recommendations")
    initialize_session_state()
    
    with st.container():
        st.subheader("Recipe Preferences")
        
        # Cuisine selection
        selected_cuisine = st.selectbox(
            "Select cuisine type:",
            CUISINES,
            index=CUISINES.index(st.session_state["selected_cuisine"])
        )
        st.session_state["selected_cuisine"] = selected_cuisine
        
        # Taste preferences
        st.subheader("Your Taste Preferences")
        
        # Sliders for taste preferences
        preferences = {}
        for taste in ["spicy", "sweet", "salty", "sour", "bitter", "umami"]:
            value = st.slider(
                f"How much do you like {taste}?",
                1, 5,
                st.session_state["user_preferences"][taste.capitalize()],
                help=f"Rate how much you enjoy {taste} flavors"
            )
            preferences[taste.capitalize()] = value
        
        # Update preferences in session state
        st.session_state["user_preferences"] = preferences
        
        # Ingredients input
        ingredients = st.text_input(
            "Enter ingredients (comma-separated)",
            value=st.session_state["ingredients_input"]
        )
        st.session_state["ingredients_input"] = ingredients
        
        # Add the Check Recipes button styling
        st.markdown(
            """
            <style>
            div.stButton > button {
                width: 100%;
                background-color: #4A5BF6;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                border: none;
                font-size: 1.1rem;
                margin-top: 1rem;
            }
            div.stButton > button:hover {
                background-color: #3A4BF6;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("Check Recipes"):
            if not ingredients:
                st.warning("Please enter some ingredients first!")
                return
                
            ingredient_list = [i.strip() for i in ingredients.split(",")]
            recipes = get_recipes(ingredient_list, selected_cuisine)
            
            if recipes:
                st.subheader("Recipe Recommendations")
                cols = st.columns(3)
                
                for idx, (col, recipe) in enumerate(zip(cols, recipes[:3])):
                    with col:
                        title = recipe["title"]
                        cuisine = recipe["cuisine"]
                        details = recipe["details"]
                        
                        st.write(f"**{title}**")
                        st.write(f"Cuisine: {cuisine}")
                        
                        # Calculate and display match score
                        recipe_data = {
                            "Spicy": min(details.get("spiciness", 3), 5),
                            "Sweet": min(details.get("sweetness", 3), 5),
                            "Salty": min(details.get("saltiness", 3), 5),
                            "Sour": min(details.get("sourness", 3), 5),
                            "Bitter": min(details.get("bitterness", 3), 5),
                            "Umami": min(details.get("savoriness", 3), 5)
                        }
                        
                        score = predict_recipe_score(recipe_data)
                        st.write(f"Match Score: {score:.1f}/5")
                        
                        recipe_url = f"https://spoonacular.com/recipes/{title.lower().replace(' ', '-')}-{recipe['id']}"
                        st.write(f"[View Recipe]({recipe_url})")
            else:
                st.warning("No recipes found for your ingredients and preferences. Try different ingredients or cuisine!")

if __name__ == "__main__":
    main()
