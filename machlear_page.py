import streamlit as st
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import random

# Spoonacular API configuration
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

# Function to set user taste preferences
def set_user_preferences():
    st.subheader("Set your taste preferences")
    st.session_state["user_preferences"]["Spicy"] = st.slider(
        "How much do you like spiciness?", 1, 5, st.session_state["user_preferences"]["Spicy"]
    )
    st.session_state["user_preferences"]["Sweet"] = st.slider(
        "How much do you like sweetness?", 1, 5, st.session_state["user_preferences"]["Sweet"]
    )
    st.session_state["user_preferences"]["Salty"] = st.slider(
        "How much do you like saltiness?", 1, 5, st.session_state["user_preferences"]["Salty"]
    )
    st.session_state["user_preferences"]["Sour"] = st.slider(
        "How much do you like sourness?", 1, 5, st.session_state["user_preferences"]["Sour"]
    )
    st.session_state["user_preferences"]["Bitter"] = st.slider(
        "How much do you like bitterness?", 1, 5, st.session_state["user_preferences"]["Bitter"]
    )
    st.session_state["user_preferences"]["Umami"] = st.slider(
        "How much do you like umami?", 1, 5, st.session_state["user_preferences"]["Umami"]
    )

# Function to fetch recipes based on inventory
def get_recipes_from_inventory():
    ingredients = list(st.session_state["inventory"].keys())
    if not ingredients:
        st.warning("Your inventory is empty. Add some ingredients!")
        return [], {}

    params = {
        "ingredients": ",".join(ingredients),
        "number": 10,
        "ranking": 2,
        "apiKey": API_KEY
    }

    response = requests.get(SPOONACULAR_URL, params=params)
    if response.status_code != 200:
        st.error("Failed to fetch recipes. Check your API key or try again later.")
        return [], {}

    recipes = response.json()
    recipe_titles = []
    recipe_links = {}

    for recipe in recipes:
        recipe_id = recipe["id"]
        recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe_id}"

        recipe_titles.append(recipe["title"])
        recipe_links[recipe["title"]] = recipe_link

    return recipe_titles, recipe_links

# Function to suggest recipes based on user preferences
def suggest_recipes():
    recipe_titles, recipe_links = get_recipes_from_inventory()
    if not recipe_titles:
        return None, None

    suggested_recipe = random.choice(recipe_titles)
    st.write(f"Suggested Recipe: **{suggested_recipe}**")
    return suggested_recipe, recipe_links.get(suggested_recipe, "#")

# Function to train the machine learning model
def train_ml_model():
    df = st.session_state["user_ratings_data"].merge(
        st.session_state["recipe_taste_data"], on="Recipe", how="inner"
    )
    if len(df) < 2:
        st.warning("Not enough data to train the model!")
        return

    cuisine_features = pd.get_dummies(df["Cuisine"], prefix="Cuisine")
    df = pd.concat([df, cuisine_features], axis=1)

    feature_columns = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"] + list(cuisine_features.columns)
    X = df[feature_columns]
    y = st.session_state["label_encoder"].fit_transform(df["Cuisine"])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    st.session_state["ml_model"] = model

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    st.success(f"Model trained successfully! Accuracy: {accuracy:.2f}")

# Main app logic
def recipe_page():
    st.title("Recipe Recommendations with Machine Learning")
    set_user_preferences()

    suggested_recipe, recipe_link = suggest_recipes()

    if suggested_recipe:
        st.write(f"Learn more about the recipe [here]({recipe_link})")

        rating = st.slider(f"Rate {suggested_recipe} (1-5):", 1, 5, 3)
        if st.button("Submit Rating"):
            new_row = {
                "Person": "User",
                "Recipe": suggested_recipe,
                "Cuisine": "Unknown",  # Add dynamic cuisine if available
                "Rating": rating
            }
            st.session_state["user_ratings_data"] = pd.concat(
                [st.session_state["user_ratings_data"], pd.DataFrame([new_row])],
                ignore_index=True
            )
            st.success("Thank you for your feedback!")

        if st.button("Train Model"):
            train_ml_model()

# Start the app
recipe_page()

