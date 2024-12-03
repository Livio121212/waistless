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

# Available cuisines and taste features
CUISINES = ["International", "Italian", "Asian", "Mexican", "Mediterranean", "American"]
TASTE_FEATURES = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]

def train_ml_model():
    """Train the ML model using existing ratings and recipe data"""
    if len(st.session_state["user_ratings"]) < 2:
        return None, None

    # Merge ratings with recipe features
    training_data = st.session_state["user_ratings"].merge(
        st.session_state["recipe_data"],
        on=["Recipe", "Cuisine"]
    )
    
    if len(training_data) < 2:
        return None, None
    
    # Prepare features and target
    X = training_data[TASTE_FEATURES]
    y = training_data["Rating"]
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    
    return model, scaler

def initialize_session_state():
    """Initialize all required session state variables"""
    if "preferences_set" not in st.session_state:
        st.session_state["preferences_set"] = False
    if "recipe_data" not in st.session_state:
        st.session_state["recipe_data"] = pd.DataFrame(columns=[
            "Recipe", "Cuisine"] + TASTE_FEATURES
        )
    if "user_ratings" not in st.session_state:
        st.session_state["user_ratings"] = pd.DataFrame(columns=["Recipe", "Rating", "Cuisine"])
    if "ml_model" not in st.session_state:
        st.session_state["ml_model"] = None
    if "scaler" not in st.session_state:
        st.session_state["scaler"] = None
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {
            taste: 3 for taste in TASTE_FEATURES
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
            detailed_response.raise_for_status()
            recipe_details = detailed_response.json()
            
            recipe_cuisine = recipe_details.get("cuisines", ["International"])[0] if recipe_details.get("cuisines") else "International"
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
    """Calculate recipe score using ML model if available, otherwise use similarity"""
    # Convert recipe data to feature array
    features = np.array([[
        recipe_data[taste] for taste in TASTE_FEATURES
    ]])
    
    # If we have a trained model, use it
    if st.session_state["ml_model"] is not None and st.session_state["scaler"] is not None:
        features_scaled = st.session_state["scaler"].transform(features)
        return st.session_state["ml_model"].predict(features_scaled)[0]
    
    # Fallback to similarity-based scoring
    taste_similarity = sum(
        1 - abs(recipe_data[taste] - st.session_state["user_preferences"][taste]) / 4
        for taste in TASTE_FEATURES
    ) / len(TASTE_FEATURES)
    
    return taste_similarity * 5

def add_recipe_rating(title, cuisine, rating, recipe_data):
    """Add or update a recipe rating and retrain the model"""
    # Add rating to user_ratings
    new_rating = pd.DataFrame([{
        "Recipe": title,
        "Rating": rating,
        "Cuisine": cuisine
    }])
    
    # Remove existing rating if present
    st.session_state["user_ratings"] = st.session_state["user_ratings"][
        st.session_state["user_ratings"]["Recipe"] != title
    ]
    
    # Add new rating
    st.session_state["user_ratings"] = pd.concat([
        st.session_state["user_ratings"],
        new_rating
    ], ignore_index=True)
    
    # Add recipe data if not present
    if title not in st.session_state["recipe_data"]["Recipe"].values:
        new_recipe = {
            "Recipe": title,
            "Cuisine": cuisine,
            **{taste: recipe_data[taste] for taste in TASTE_FEATURES}
        }
        st.session_state["recipe_data"] = pd.concat([
            st.session_state["recipe_data"],
            pd.DataFrame([new_recipe])
        ], ignore_index=True)
    
    # Retrain model
    model, scaler = train_ml_model()
    if model is not None:
        st.session_state["ml_model"] = model
        st.session_state["scaler"] = scaler

def recipepage():
    """Main recipe recommendation page"""
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
        for taste in [t.lower() for t in TASTE_FEATURES]:
            value = st.slider(
                f"How much do you like {taste}?",
                1, 5,
                st.session_state["user_preferences"][taste.capitalize()],
                help=f"Rate how much you enjoy {taste} flavors"
            )
            preferences[taste.capitalize()] = value
        
        # Update preferences in session state
        st.session_state["user_preferences"] = preferences
        st.session_state["preferences_set"] = True
        
        # Display number of rated recipes
        n_ratings = len(st.session_state["user_ratings"])
        if n_ratings > 0:
            st.info(f"You have rated {n_ratings} recipes. The AI model will use these ratings to improve recommendations.")
        
        # Ingredients input
        ingredients = st.text_input(
            "Enter ingredients (comma-separated)",
            value=st.session_state["ingredients_input"]
        )
        st.session_state["ingredients_input"] = ingredients
        
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
                        
                        # Add rating input
                        rating = st.slider(
                            "Rate this recipe",
                            1, 5, 3,
                            key=f"rating_{idx}"
                        )
                        
                        if st.button("Submit Rating", key=f"rate_{idx}"):
                            add_recipe_rating(title, cuisine, rating, recipe_data)
                            st.success("Rating submitted! The AI model will use this to improve future recommendations.")
                        
                        recipe_url = f"https://spoonacular.com/recipes/{title.lower().replace(' ', '-')}-{recipe['id']}"
                        st.write(f"[View Recipe]({recipe_url})")
            else:
                st.warning("No recipes found for your ingredients and preferences. Try different ingredients or cuisine!")

if __name__ == "__main__":
    recipepage()