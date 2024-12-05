import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import random

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

def calculate_cuisine_ratings(user_preferences_df):
    """Calculate mean ratings for each cuisine type"""
    if user_preferences_df.empty:
        return {}
    return user_preferences_df.groupby("Cuisine")["Rating"].mean().to_dict()

def get_unrated_cuisines(user_preferences_df, all_cuisines):
    """Get list of cuisines that haven't been rated yet"""
    if user_preferences_df.empty:
        return all_cuisines
    rated_cuisines = set(user_preferences_df["Cuisine"].unique())
    return list(set(all_cuisines) - rated_cuisines)