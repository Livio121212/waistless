import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
import os
import json

# Load or initialize user-specific data
def load_user_data(username):
    user_file = f"{username}_data.json"
    if os.path.exists(user_file):
        with open(user_file, "r") as file:
            return json.load(file)
    return {"cooking_history": [], "ml_model": None}

def save_user_data(username, data):
    user_file = f"{username}_data.json"
    with open(user_file, "w") as file:
        json.dump(data, file)

# Train a personalized machine learning model
def train_user_model(username):
    user_data = load_user_data(username)
    cooking_history = user_data.get("cooking_history", [])

    if len(cooking_history) < 3:  # Minimum data for training
        return None

    # Prepare data
    df = pd.DataFrame(cooking_history)
    X = df["Recipe"]
    y = df["Rating"]

    # Encode recipe names
    encoder = LabelEncoder()
    X_encoded = encoder.fit_transform(X).reshape(-1, 1)

    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_encoded, y)

    # Save model and encoder
    user_data["ml_model"] = {"model": model, "encoder": encoder.classes_.tolist()}
    save_user_data(username, user_data)

    return model, encoder

# Predict rating for a recipe
def predict_recipe_score(username, recipe):
    user_data = load_user_data(username)
    ml_model = user_data.get("ml_model")

    if not ml_model:
        return np.random.uniform(3, 5)  # Default random score if no model

    model = RandomForestRegressor()
    model.fit([[0]], [0])  # Dummy fit (needed to create the model object)
    model.__setstate__(ml_model["model"])  # Load saved model
    encoder = LabelEncoder()
    encoder.classes_ = np.array(ml_model["encoder"])  # Load saved encoder classes

    try:
        recipe_encoded = encoder.transform([recipe]).reshape(-1, 1)
        predicted_score = model.predict(recipe_encoded)
        return np.clip(predicted_score[0], 1, 5)  # Clip between 1 and 5
    except:
        return np.random.uniform(3, 5)

# Suggest recipes based on predictions
def suggest_recipes(username, available_recipes):
    suggestions = []
    for recipe in available_recipes:
        score = predict_recipe_score(username, recipe)
        suggestions.append((recipe, score))
    return sorted(suggestions, key=lambda x: x[1], reverse=True)[:5]

# Recipe page
def recipepage():
    st.title("Recipe Recommendations")

    if "username" not in st.session_state or not st.session_state["username"]:
        st.warning("Please log in to see personalized recommendations.")
        return

    username = st.session_state["username"]

    # Example available recipes
    available_recipes = ["Pasta Carbonara", "Veggie Bowl", "Pumpkin Soup", "Pizza Margherita", "Ratatouille"]

    # Train model (if data exists)
    train_user_model(username)

    # Get suggestions
    suggestions = suggest_recipes(username, available_recipes)

    st.subheader("Recommended Recipes")
    for recipe, score in suggestions:
        st.write(f"**{recipe}** - Predicted Rating: {score:.1f}")

    # Rating input
    st.subheader("Rate a Recipe")
    selected_recipe = st.selectbox("Choose a recipe:", ["Select"] + available_recipes)
    rating = st.slider("Rate the recipe (1-5):", 1, 5, 3)

    if st.button("Submit Rating"):
        if selected_recipe != "Select":
            cooking_history = load_user_data(username).get("cooking_history", [])
            cooking_history.append({
                "Recipe": selected_recipe,
                "Rating": rating,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            user_data = load_user_data(username)
            user_data["cooking_history"] = cooking_history
            save_user_data(username, user_data)

            st.success(f"Rated '{selected_recipe}' with {rating} stars.")
            train_user_model(username)  # Retrain model with new data
        else:
            st.warning("Please select a recipe to rate.")
