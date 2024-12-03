# Import required libraries for web interface, data manipulation, API requests, and machine learning
import streamlit as st
import pandas as pd
import requests
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import re

# API configuration for Spoonacular recipe service
# API_KEY is used for authentication with the Spoonacular API
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
# Base URL for the recipe search endpoint
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# List of supported cuisine types for recipe filtering
# Users can select from these options in the dropdown menu
CUISINES = ["International", "Italian", "Asian", "Mexican", "Mediterranean", "American"]

def initialize_session_state():
    """
    Initialize all required session state variables for the recipe recommendation system.
    This function sets up the initial state for user preferences, recipe data, and ML model components.
    Each variable is checked and initialized only if it doesn't already exist in the session state.
    """
    # Track whether user has set their preferences
    if "preferences_set" not in st.session_state:
        st.session_state["preferences_set"] = False
    
    # DataFrame to store recipe information including taste profiles
    if "recipe_data" not in st.session_state:
        st.session_state["recipe_data"] = pd.DataFrame(columns=[
            "Recipe", "Cuisine", "Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"
        ])
    
    # DataFrame to store user ratings for recipes
    if "user_ratings" not in st.session_state:
        st.session_state["user_ratings"] = pd.DataFrame(columns=["Recipe", "Rating", "Cuisine"])
    
    # Machine learning model for recipe recommendations
    if "ml_model" not in st.session_state:
        st.session_state["ml_model"] = None
    
    # Standard scaler for normalizing recipe features
    if "scaler" not in st.session_state:
        st.session_state["scaler"] = StandardScaler()
    
    # Dictionary to store user's taste preferences
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {
            "Spicy": 3, "Sweet": 3, "Salty": 3,
            "Sour": 3, "Bitter": 3, "Umami": 3
        }
    
    # Selected cuisine type, defaults to International
    if "selected_cuisine" not in st.session_state:
        st.session_state["selected_cuisine"] = "International"
    
    # Store user's ingredient input
    if "ingredients_input" not in st.session_state:
        st.session_state["ingredients_input"] = ""

def get_recipes(ingredients, cuisine):
    """
    Fetch and filter recipes from Spoonacular API based on ingredients and cuisine preference.
    
    Args:
        ingredients (list): List of ingredient strings provided by the user
        cuisine (str): Preferred cuisine type selected by the user
    
    Returns:
        list: Filtered list of recipe dictionaries containing recipe details and cuisine information
    """
    try:
        # Prepare API request parameters
        params = {
            "ingredients": ",".join(ingredients),
            "number": 10,  # Request 10 recipes to ensure we have enough after filtering
            "apiKey": API_KEY
        }

        # Make initial API request to get basic recipe information
        response = requests.get(SPOONACULAR_URL, params=params)
        response.raise_for_status()
        recipes = response.json()
        
        # Initialize list for storing filtered recipes
        filtered_recipes = []
        
        # Process each recipe and get detailed information
        for recipe in recipes:
            recipe_id = recipe.get("id")
            title = recipe.get("title")
            
            # Skip recipes without valid ID or title
            if not recipe_id or not title:
                continue
            
            # Get detailed recipe information from separate API endpoint
            detailed_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
            detailed_response = requests.get(detailed_url, params={"apiKey": API_KEY})
            recipe_details = detailed_response.json()
            
            # Extract cuisine information and filter based on user preference
            recipe_cuisine = recipe_details.get("cuisines", ["International"])[0]
            if cuisine != "International" and recipe_cuisine != cuisine:
                continue
            
            # Add cuisine and details to recipe dictionary
            recipe["cuisine"] = recipe_cuisine
            recipe["details"] = recipe_details
            filtered_recipes.append(recipe)
            
        return filtered_recipes

    except requests.RequestException as e:
        # Handle API request errors and display to user
        st.error(f"Error fetching recipes: {str(e)}")
        return []

def predict_recipe_score(recipe_data):
    """
    Calculate a recipe's match score based on user taste preferences.
    
    Args:
        recipe_data (dict): Dictionary containing recipe taste profiles
    
    Returns:
        float: Calculated match score between 0 and 5
    """
    # List of taste features to consider in scoring
    taste_features = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]
    
    # Calculate average similarity across all taste features
    # Formula: 1 - (absolute difference / maximum possible difference)
    taste_similarity = sum(
        1 - abs(recipe_data[taste] - st.session_state["user_preferences"][taste]) / 4
        for taste in taste_features
    ) / len(taste_features)
    
    # Convert similarity score to 5-point scale
    return taste_similarity * 5

def recipe_page():
    """
    Main function to render the recipe recommendation page.
    Handles user input, displays interface elements, and shows recipe recommendations.
    """
    # Set page title and initialize session state
    st.title("Smart Recipe Recommendations")
    initialize_session_state()
    
    # Create main container for page content
    with st.container():
        st.subheader("Recipe Preferences")
        
        # Cuisine selection dropdown
        selected_cuisine = st.selectbox(
            "Select cuisine type:",
            CUISINES,
            index=CUISINES.index(st.session_state["selected_cuisine"])
        )
        st.session_state["selected_cuisine"] = selected_cuisine
        
        # Taste preferences section
        st.subheader("Your Taste Preferences")
        
        # Create sliders for each taste preference
        preferences = {}
        for taste in ["spicy", "sweet", "salty", "sour", "bitter", "umami"]:
            value = st.slider(
                f"How much do you like {taste}?",
                1, 5,
                st.session_state["user_preferences"][taste.capitalize()],
                help=f"Rate how much you enjoy {taste} flavors"
            )
            preferences[taste.capitalize()] = value
        
        # Update user preferences in session state
        st.session_state["user_preferences"] = preferences
        
        # Ingredient input field
        ingredients = st.text_input(
            "Enter ingredients (comma-separated)",
            value=st.session_state["ingredients_input"]
        )
        st.session_state["ingredients_input"] = ingredients
        
        # Custom styling for the Check Recipes button
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
        
        # Recipe search and display section
        if st.button("Check Recipes"):
            # Validate ingredient input
            if not ingredients:
                st.warning("Please enter some ingredients first!")
                return
            
            # Process ingredients and get recipe recommendations
            ingredient_list = [i.strip() for i in ingredients.split(",")]
            recipes = get_recipes(ingredient_list, selected_cuisine)
            
            # Display recipe recommendations if found
            if recipes:
                st.subheader("Recipe Recommendations")
                cols = st.columns(3)  # Create 3-column layout
                
                # Display up to 3 recipes with their details
                for idx, (col, recipe) in enumerate(zip(cols, recipes[:3])):
                    with col:
                        title = recipe["title"]
                        cuisine = recipe["cuisine"]
                        details = recipe["details"]
                        
                        # Display recipe title and cuisine
                        st.write(f"**{title}**")
                        st.write(f"Cuisine: {cuisine}")
                        
                        # Calculate recipe's match score based on taste preferences
                        recipe_data = {
                            "Spicy": min(details.get("spiciness", 3), 5),
                            "Sweet": min(details.get("sweetness", 3), 5),
                            "Salty": min(details.get("saltiness", 3), 5),
                            "Sour": min(details.get("sourness", 3), 5),
                            "Bitter": min(details.get("bitterness", 3), 5),
                            "Umami": min(details.get("savoriness", 3), 5)
                        }
                        
                        # Calculate and display match score
                        score = predict_recipe_score(recipe_data)
                        st.write(f"Match Score: {score:.1f}/5")
                        
                        # Generate and display recipe URL
                        recipe_url = f"https://spoonacular.com/recipes/{title.lower().replace(' ', '-')}-{recipe['id']}"
                        st.write(f"[View Recipe]({recipe_url})")
            else:
                # Display message if no recipes are found
                st.warning("No recipes found for your ingredients and preferences. Try different ingredients or cuisine!")

# Entry point for running the application directly
if __name__ == "__main__":
    recipe_page()
