import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# API Key and URL for Spoonacular
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# Initialize session state variables
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {
        "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
        "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
        "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
        "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
        "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
    }

if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf"]
if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = None
if "recipe_taste_data" not in st.session_state:
    st.session_state["recipe_taste_data"] = pd.DataFrame(columns=["Recipe", "Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami", "Cuisine"])
if "user_ratings_data" not in st.session_state:
    st.session_state["user_ratings_data"] = pd.DataFrame(columns=["Person", "Recipe", "Cuisine", "Rating"])
if "ml_model" not in st.session_state:
    st.session_state["ml_model"] = None
if "label_encoder" not in st.session_state:
    st.session_state["label_encoder"] = LabelEncoder()
if "user_preferences" not in st.session_state:
    st.session_state["user_preferences"] = {
        "Spicy": 3,
        "Sweet": 3,
        "Salty": 3,
        "Sour": 3,
        "Bitter": 3,
        "Umami": 3
    }

# Function to input user preferences
def set_user_preferences():
    st.subheader("Set your taste preferences")
    st.session_state["user_preferences"]["Spicy"] = st.slider("How much do you like spiciness?", 1, 5, 3)
    st.session_state["user_preferences"]["Sweet"] = st.slider("How much do you like sweetness?", 1, 5, 3)
    st.session_state["user_preferences"]["Salty"] = st.slider("How much do you like saltiness?", 1, 5, 3)
    st.session_state["user_preferences"]["Sour"] = st.slider("How much do you like sourness?", 1, 5, 3)
    st.session_state["user_preferences"]["Bitter"] = st.slider("How much do you like bitterness?", 1, 5, 3)
    st.session_state["user_preferences"]["Umami"] = st.slider("How much do you like umami?", 1, 5, 3)

# Function to search recipes and retrieve taste profiles
def get_recipes_from_inventory():
    ingredients = list(st.session_state["inventory"].keys())
    if not ingredients:
        st.warning("The inventory is empty. Please add ingredients.")
        return [], {}
    
    params = {
        "ingredients": ",".join(ingredients),
        "number": 10,
        "ranking": 2,
        "apiKey": API_KEY
    }
    response = requests.get(SPOONACULAR_URL, params=params)
    
    if response.status_code == 200:
        recipes = response.json()
        recipe_titles = []
        recipe_links = {}

        for recipe in recipes:
            recipe_id = recipe['id']
            recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe_id}"

            # Retrieve taste profile and cuisine
            info_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
            info_params = {"apiKey": API_KEY}
            info_response = requests.get(info_url, params=info_params)
            
            if info_response.status_code == 200:
                info_data = info_response.json()
                cuisine = info_data.get("cuisines", ["Unknown"])[0]
                taste_profile = info_data.get("taste", {})
                spicy = taste_profile.get("spicy", 0.0)
                sweet = taste_profile.get("sweet", 0.0)
                salty = taste_profile.get("salty", 0.0)
                sour = taste_profile.get("sour", 0.0)
                bitter = taste_profile.get("bitter", 0.0)
                umami = taste_profile.get("umami", 0.0)

                # Save taste profiles and cuisine
                st.session_state["recipe_taste_data"] = pd.concat([
                    st.session_state["recipe_taste_data"],
                    pd.DataFrame([[recipe['title'], spicy, sweet, salty, sour, bitter, umami, cuisine]],
                                 columns=["Recipe", "Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami", "Cuisine"])
                ], ignore_index=True)

                recipe_titles.append(recipe['title'])
                recipe_links[recipe['title']] = recipe_link

        return recipe_titles, recipe_links
    else:
        st.error("Error fetching recipes. Please check your API key.")
        return [], {}

# Function to train the machine learning model
def train_ml_model():
    df = st.session_state["user_ratings_data"].merge(
        st.session_state["recipe_taste_data"], on="Recipe", how="left"
    )
    if len(df) > 1:
        cuisine_features = pd.get_dummies(df["Cuisine"])
        df = pd.concat([df, cuisine_features], axis=1)
        X = pd.get_dummies(df[["Person", "Recipe", "Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"] + list(cuisine_features.columns)])
        y = st.session_state["label_encoder"].fit_transform(df["Cuisine"])

        model = RandomForestClassifier()
        model.fit(X, y)
        st.session_state["ml_model"] = model
        st.success("The machine learning model was successfully trained!")

# Main page of the app
def recipe_page():
    st.title("Recipe Recommendations with Machine Learning")
    set_user_preferences()

    selected_user = st.selectbox("Select a user:", st.session_state["roommates"])
    st.session_state["selected_user"] = selected_user

    recipe_titles, recipe_links = get_recipes_from_inventory()
    
    if recipe_titles:
        selected_recipe = st.selectbox("Select a recipe:", recipe_titles)
        train_ml_model()

# Start the app
recipe_page()
