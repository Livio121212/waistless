import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import streamlit as st
import requests
# Configuration constants
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'
# Available cuisines and taste features
CUISINES = ["Random", "Italian", "Asian", "Mexican", "Mediterranean", "American", "International"]
TASTE_FEATURES = [
    {"name": "spicy", "label": "How much do you like spicy?"},
    {"name": "sweet", "label": "How much do you like sweet?"},
    {"name": "salty", "label": "How much do you like salty?"},
    {"name": "sour", "label": "How much do you like sour?"},
    {"name": "bitter", "label": "How much do you like bitter?"},
    {"name": "umami", "label": "How much do you like umami?"}
]
class RecipeRecommender:
    def __init__(self):
        """Initialize the recipe recommender with empty data structures"""
        self.ratings_file = 'recipe_ratings.csv'
        self.recipe_data_file = 'recipe_data.csv'
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.load_data()
    def load_data(self):
        """Load existing ratings and recipe data from CSV files"""
        try:
            self.ratings_df = pd.read_csv(self.ratings_file)
            self.recipe_data_df = pd.read_csv(self.recipe_data_file)
        except FileNotFoundError:
            # Create empty dataframes if files don't exist
            self.ratings_df = pd.DataFrame(columns=["Recipe", "Rating", "Cuisine"])
            self.recipe_data_df = pd.DataFrame(columns=[
                "Recipe", "Cuisine", "Spicy", "Sweet", "Salty", 
                "Sour", "Bitter", "Umami"
            ])
    def save_data(self):
        """Save ratings and recipe data to CSV files"""
        self.ratings_df.to_csv(self.ratings_file, index=False)
        self.recipe_data_df.to_csv(self.recipe_data_file, index=False)
    def train_model(self):
        """Train the recommendation model using available ratings and recipe data"""
        if len(self.ratings_df) < 2:  # Need at least 2 ratings to train
            return False
        # Merge ratings with recipe features
        training_data = self.ratings_df.merge(self.recipe_data_df, on=["Recipe", "Cuisine"])
        
        # Prepare features (taste preferences) and target (ratings)
        X = training_data[["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]]
        y = training_data["Rating"]
        
        # Scale features and train model
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        return True
    def predict_recipe_score(self, recipe_data):
        """Predict rating for a recipe based on its features"""
        features = np.array([[
            recipe_data["Spicy"],
            recipe_data["Sweet"],
            recipe_data["Salty"],
            recipe_data["Sour"],
            recipe_data["Bitter"],
            recipe_data["Umami"]
        ]])
        
        # If model is trained, use it; otherwise use simple similarity
        if len(self.ratings_df) >= 2:
            features_scaled = self.scaler.transform(features)
            return self.model.predict(features_scaled)[0]
        else:
            # Calculate average similarity to user preferences
            user_prefs = np.array([st.session_state["user_preferences"][f] for f in ["spicy", "sweet", "salty", "sour", "bitter", "umami"]])
            similarity = 1 - np.mean(np.abs(features - user_prefs) / 4)
            return similarity * 5
    def get_recipes(self, ingredients):
        """Fetch recipes from Spoonacular API based on ingredients"""
        try:
            response = requests.get(
                SPOONACULAR_URL,
                params={
                    "ingredients": ",".join(ingredients),
                    "number": 3,
                    "apiKey": API_KEY
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Error fetching recipes: {str(e)}")
            return []
def main():
    """Main function to run the Streamlit application"""
    st.title("Smart Recipe Recommendations")
    
    # Initialize recommender and session state
    recommender = RecipeRecommender()
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {
            taste["name"]: 3 for taste in TASTE_FEATURES
        }
    if "selected_cuisine" not in st.session_state:
        st.session_state["selected_cuisine"] = "Random"
    if "preferences_set" not in st.session_state:
        st.session_state["preferences_set"] = False
    
    # Cuisine selection
    st.subheader("Step 1: Select Cuisine Type")
    selected_cuisine = st.selectbox(
        "Choose your preferred cuisine:",
        CUISINES,
        index=CUISINES.index(st.session_state["selected_cuisine"])
    )
    st.session_state["selected_cuisine"] = selected_cuisine
    
    # Taste preferences
    st.subheader("Step 2: Set Your Taste Preferences")
    preferences_changed = False
    for taste in TASTE_FEATURES:
        new_value = st.slider(
            taste["label"],
            1, 5,
            st.session_state["user_preferences"][taste["name"]],
            help=f"Rate how much you enjoy {taste['name']} flavors"
        )
        if new_value != st.session_state["user_preferences"][taste["name"]]:
            preferences_changed = True
            st.session_state["user_preferences"][taste["name"]] = new_value
    
    # Confirm preferences
    if st.button("Confirm Preferences"):
        st.session_state["preferences_set"] = True
        st.success("Preferences saved! You can now get recipe recommendations.")
        st.experimental_rerun()
    
    # Only proceed if preferences are set
    if not st.session_state["preferences_set"]:
        st.warning("Please set your preferences before proceeding!")
        return
    
    # Ingredient input
    st.subheader("Step 3: Enter Your Ingredients")
    ingredients = st.text_input("Enter ingredients (comma-separated)")
    
    if ingredients and st.button("Get Recommendations"):
        ingredient_list = [i.strip() for i in ingredients.split(",")]
        recipes = recommender.get_recipes(ingredient_list)
        
        if recipes:
            st.subheader("Recipe Recommendations")
            for recipe in recipes:
                title = recipe.get("title", "")
                
                # Add recipe to data if not exists
                if title not in recommender.recipe_data_df["Recipe"].values:
                    new_recipe = {
                        "Recipe": title,
                        "Cuisine": st.session_state["selected_cuisine"],
                        **{
                            taste["name"]: st.session_state["user_preferences"][taste["name"]]
                            for taste in TASTE_FEATURES
                        }
                    }
                    recommender.recipe_data_df = pd.concat([
                        recommender.recipe_data_df,
                        pd.DataFrame([new_recipe])
                    ], ignore_index=True)
                    recommender.save_data()
                
                # Get recipe data and predict score
                recipe_data = recommender.recipe_data_df[
                    recommender.recipe_data_df["Recipe"] == title
                ].iloc[0]
                score = recommender.predict_recipe_score(recipe_data)
                
                # Display recipe with rating option
                st.write(f"**{title}**")
                st.write(f"Match Score: {score:.1f}/5")
                rating = st.slider(f"Rate {title}", 1, 5, 3)
                
                if st.button(f"Submit Rating for {title}"):
                    new_rating = pd.DataFrame([{
                        "Recipe": title,
                        "Rating": rating,
                        "Cuisine": recipe_data["Cuisine"]
                    }])
                    recommender.ratings_df = pd.concat([
                        recommender.ratings_df,
                        new_rating
                    ], ignore_index=True)
                    recommender.save_data()
                    recommender.train_model()
                    st.success("Rating submitted successfully!")
                    st.experimental_rerun()
        else:
            st.warning("No recipes found. Try different ingredients!")
if __name__ == "__main__":
    main()