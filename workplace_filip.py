import streamlit as st
import pandas as pd  # Use for data manipulation and creating tables
import requests  # Use to send API requests
import numpy as np  # Use for numerical operations
from sklearn.ensemble import RandomForestRegressor  # Use to train a machine learning model
from sklearn.preprocessing import StandardScaler  # Use to scale features for ML model
import re  # Use for regular expressions

# API key and endpoint URL for Spoonacular API
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'  # Authentication for API access
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'  # URL to fetch recipes based on ingredients

# Available cuisines and taste features for filtering and scoring recipes
CUISINES = ["International", "Italian", "Asian", "Mexican", "Mediterranean", "American"]  # Supported cuisine types
TASTE_FEATURES = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]  # Flavor profiles used for scoring

def train_ml_model():
    """Train the machine learning model using user ratings and recipe data"""
    if len(st.session_state["user_ratings"]) < 2:  # Ensure enough data exists for training
        return None, None  # Return None if insufficient data

    # Merge user ratings with recipe data for training
    training_data = st.session_state["user_ratings"].merge(
        st.session_state["recipe_data"],
        on=["Recipe", "Cuisine"]  # Join on recipe name and cuisine type
    )
    
    if len(training_data) < 2:  # Ensure sufficient training data after merging
        return None, None
    
    # Prepare input features (X) and target variable (y)
    X = training_data[TASTE_FEATURES]  # Use taste features for training
    y = training_data["Rating"]  # Target variable is the user rating
    
    # Scale input features for better model performance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train a Random Forest Regressor
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)  # Fit the model on scaled features and target ratings
    
    return model, scaler  # Return trained model and scaler for prediction

def initialize_session_state():
    """Initialize all required session state variables"""
    if "preferences_set" not in st.session_state:
        st.session_state["preferences_set"] = False  # Track if preferences are set
    if "recipe_data" not in st.session_state:
        st.session_state["recipe_data"] = pd.DataFrame(columns=[
            "Recipe", "Cuisine"] + TASTE_FEATURES  # Columns for storing recipe data
        )
    if "user_ratings" not in st.session_state:
        st.session_state["user_ratings"] = pd.DataFrame(columns=["Recipe", "Rating", "Cuisine"])  # Store user ratings
    if "ml_model" not in st.session_state:
        st.session_state["ml_model"] = None  # Placeholder for trained model
    if "scaler" not in st.session_state:
        st.session_state["scaler"] = None  # Placeholder for scaler
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {taste: 3 for taste in TASTE_FEATURES}  # Default taste preferences
    if "selected_cuisine" not in st.session_state:
        st.session_state["selected_cuisine"] = "International"  # Default cuisine selection
    if "ingredients_input" not in st.session_state:
        st.session_state["ingredients_input"] = ""  # Placeholder for user-entered ingredients

def get_recipes(ingredients, cuisine):
    """Fetch recipes from the API based on given ingredients and selected cuisine"""
    try:
        # Set query parameters for API request
        params = {
            "ingredients": ",".join(ingredients),  # Combine ingredients into a comma-separated string
            "number": 10,  # Number of recipes to fetch
            "apiKey": API_KEY  # API key for authentication
        }
        response = requests.get(SPOONACULAR_URL, params=params)  # Send API request
        response.raise_for_status()  # Raise exception for HTTP errors
        recipes = response.json()  # Parse response as JSON
        
        filtered_recipes = []
        for recipe in recipes:  # Iterate over returned recipes
            recipe_id = recipe.get("id")  # Extract recipe ID
            title = recipe.get("title")  # Extract recipe title
            
            if not recipe_id or not title:  # Skip recipes with missing information
                continue
                
            # Fetch detailed recipe information
            detailed_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
            detailed_response = requests.get(detailed_url, params={"apiKey": API_KEY})  # Send API request
            detailed_response.raise_for_status()  # Raise exception for HTTP errors
            recipe_details = detailed_response.json()  # Parse response as JSON
            
            # Extract and filter by cuisine if specified
            recipe_cuisine = recipe_details.get("cuisines", ["International"])[0] if recipe_details.get("cuisines") else "International"
            if cuisine != "International" and recipe_cuisine != cuisine:
                continue
                
            # Append detailed recipe data
            recipe["cuisine"] = recipe_cuisine
            recipe["details"] = recipe_details
            filtered_recipes.append(recipe)
            
        return filtered_recipes  # Return the list of filtered recipes
    except requests.RequestException as e:  # Handle API request errors
        st.error(f"Error fetching recipes: {str(e)}")  # Display error message
        return []

def predict_recipe_score(recipe_data):
    """Calculate a recipe score using the trained ML model or fallback to taste similarity"""
    features = np.array([[
        recipe_data[taste] for taste in TASTE_FEATURES  # Extract feature values for prediction
    ]])
    
    # Use the trained model if available
    if st.session_state["ml_model"] is not None and st.session_state["scaler"] is not None:
        features_scaled = st.session_state["scaler"].transform(features)  # Scale features
        return st.session_state["ml_model"].predict(features_scaled)[0]  # Predict and return score
    
    # Fallback to similarity-based scoring
    taste_similarity = sum(
        1 - abs(recipe_data[taste] - st.session_state["user_preferences"][taste]) / 4
        for taste in TASTE_FEATURES
    ) / len(TASTE_FEATURES)  # Calculate similarity score
    
    return taste_similarity * 5  # Scale score to range of 1-5

def add_recipe_rating(title, cuisine, rating, recipe_data):
    """Add or update a recipe rating and retrain the model"""
    new_rating = pd.DataFrame([{
        "Recipe": title,  # Recipe name
        "Rating": rating,  # User rating
        "Cuisine": cuisine  # Recipe cuisine type
    }])
    
    # Remove existing rating if already present
    st.session_state["user_ratings"] = st.session_state["user_ratings"][
        st.session_state["user_ratings"]["Recipe"] != title
    ]
    
    # Add new rating
    st.session_state["user_ratings"] = pd.concat([
        st.session_state["user_ratings"],
        new_rating
    ], ignore_index=True)
    
    # Add recipe data if not already stored
    if title not in st.session_state["recipe_data"]["Recipe"].values:
        new_recipe = {
            "Recipe": title,
            "Cuisine": cuisine,
            **{taste: recipe_data[taste] for taste in TASTE_FEATURES}  # Include taste features
        }
        st.session_state["recipe_data"] = pd.concat([
            st.session_state["recipe_data"],
            pd.DataFrame([new_recipe])
        ], ignore_index=True)
    
    # Retrain the ML model with updated ratings
    model, scaler = train_ml_model()
    if model is not None:  # Update model and scaler if training succeeded
        st.session_state["ml_model"] = model
        st.session_state["scaler"] = scaler

def recipepage():
    """Main recipe recommendation page"""
    st.title("Smart Recipe Recommendations")  # Page title
    initialize_session_state()  # Initialize session state variables
    
    with st.container():
        st.subheader("Recipe Preferences")  # Section heading for preferences
        
        # Dropdown to select cuisine type
        selected_cuisine = st.selectbox(
            "Select cuisine type:",
            CUISINES,
            index=CUISINES.index(st.session_state["selected_cuisine"])  # Default selection
        )
        st.session_state["selected_cuisine"] = selected_cuisine  # Save selected cuisine
        
        # Sliders for taste preferences
        st.subheader("Your Taste Preferences")  # Section heading for taste preferences
        preferences = {}
        for taste in [t.lower() for t in TASTE_FEATURES]:
            value = st.slider(
                f"How much do you like {taste}?",  # Slider label
                1, 5,  # Range for slider
                st.session_state["user_preferences"][taste.capitalize()],  # Default value
                help=f"Rate how much you enjoy {taste} flavors"
            )
            preferences[taste.capitalize()] = value  # Save preference
        
        # Update taste preferences in session state
        st.session_state["user_preferences"] = preferences
        st.session_state["preferences_set"] = True  # Mark preferences as set
        
        # Display count of rated recipes
        n_ratings = len(st.session_state["user_ratings"])
        if n_ratings > 0:  # Show info if ratings exist
            st.info(f"You have rated {n_ratings} recipes. The AI model will use these ratings to improve recommendations.")
        
        # Text input for ingredients
        ingredients = st.text_input(
            "Enter ingredients (comma-separated):",  # Input label
            value=st.session_state["ingredients_input"]  # Default value
        )
        st.session_state["ingredients_input"] = ingredients  # Save input
        
        if st.button("Check Recipes"):  # Button to fetch recipes
            if not ingredients:  # Ensure ingredients are provided
                st.warning("Please enter some ingredients first!")  # Show warning if empty
                return
                
            ingredient_list = [i.strip() for i in ingredients.split(",")]  # Parse ingredients into list
            recipes = get_recipes(ingredient_list, selected_cuisine)  # Fetch recipes
            
            if recipes:  # Check if recipes were found
                st.subheader("Recipe Recommendations")  # Section heading for recommendations
                cols = st.columns(3)  # Create three columns to display recipes
                
                for idx, (col, recipe) in enumerate(zip(cols, recipes[:3])):  # Display up to 3 recipes
                    with col:
                        title = recipe["title"]  # Recipe title
                        cuisine = recipe["cuisine"]  # Recipe cuisine
                        details = recipe["details"]  # Detailed recipe info
                        
                        st.write(f"**{title}**")  # Display recipe title
                        st.write(f"Cuisine: {cuisine}")  # Display recipe cuisine
                        
                        # Calculate match score for the recipe
                        recipe_data = {
                            "Spicy": min(details.get("spiciness", 3), 5),
                            "Sweet": min(details.get("sweetness", 3), 5),
                            "Salty": min(details.get("saltiness", 3), 5),
                            "Sour": min(details.get("sourness", 3), 5),
                            "Bitter": min(details.get("bitterness", 3), 5),
                            "Umami": min(details.get("savoriness", 3), 5)
                        }
                        score = predict_recipe_score(recipe_data)  # Predict score
                        st.write(f"Match Score: {score:.1f}/5")  # Display match score
                        
                        # Rating slider
                        rating = st.slider(
                            "Rate this recipe:",  # Slider label
                            1, 5,  # Range for slider
                            3,  # Default value
                            key=f"rating_{idx}"  # Unique key for slider
                        )
                        
                        if st.button("Submit Rating", key=f"rate_{idx}"):  # Button to submit rating
                            add_recipe_rating(title, cuisine, rating, recipe_data)  # Add/update rating
                            st.success("Rating submitted! The AI model will use this to improve future recommendations.")  # Success message
                        
                        # Link to recipe
                        recipe_url = f"https://spoonacular.com/recipes/{title.lower().replace(' ', '-')}-{recipe['id']}"
                        st.write(f"[View Recipe]({recipe_url})")  # Display recipe link
            else:
                st.warning("No recipes found for your ingredients and preferences. Try different ingredients or cuisine.")  # Show warning if no recipes found

if __name__ == "__main__":
    recipepage()  # Run the main page function
