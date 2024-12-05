import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import streamlit as st

# Available cuisines and taste features
CUISINES = ["International", "Italian", "Asian", "Mexican", "Mediterranean", "American"]
TASTE_FEATURES = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]

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

def predict_recipe_score(recipe_cuisine, user):
    """Predict score for a recipe based on user's preferences"""
    if user not in st.session_state["ml_models"] or st.session_state["ml_models"][user] is None:
        return random.uniform(3, 5)  # Return random score if no model exists

    # Create feature vector for prediction
    cuisine_features = pd.get_dummies([recipe_cuisine], columns=CUISINES)
    return st.session_state["ml_models"][user].predict(cuisine_features)[0]

def calculate_cuisine_ratings(user):
    """Calculate mean ratings for each cuisine type for a user"""
    if user not in st.session_state["user_preferences"]:
        return {}
    
    user_data = st.session_state["user_preferences"][user]
    if len(user_data) == 0:
        return {}
    
    cuisine_ratings = user_data.groupby("Cuisine")["Rating"].mean().to_dict()
    return cuisine_ratings

def get_unrated_cuisines(user):
    """Get list of cuisines that haven't been rated by the user"""
    rated_cuisines = set(st.session_state["user_preferences"].get(user, pd.DataFrame())["Cuisine"].unique())
    return [cuisine for cuisine in CUISINES if cuisine not in rated_cuisines]