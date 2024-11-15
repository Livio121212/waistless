import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# API Key und URL für Spoonacular
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# Initialisierung der Session-State-Variablen
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

# Funktion zur Eingabe von Nutzerpräferenzen
def set_user_preferences():
    st.subheader("Setzen Sie Ihre Geschmackspräferenzen")
    st.session_state["user_preferences"]["Spicy"] = st.slider("Wie sehr mögen Sie Schärfe?", 1, 5, 3)
    st.session_state["user_preferences"]["Sweet"] = st.slider("Wie sehr mögen Sie Süße?", 1, 5, 3)
    st.session_state["user_preferences"]["Salty"] = st.slider("Wie sehr mögen Sie Salzigkeit?", 1, 5, 3)
    st.session_state["user_preferences"]["Sour"] = st.slider("Wie sehr mögen Sie Säure?", 1, 5, 3)
    st.session_state["user_preferences"]["Bitter"] = st.slider("Wie sehr mögen Sie Bitterkeit?", 1, 5, 3)
    st.session_state["user_preferences"]["Umami"] = st.slider("Wie sehr mögen Sie Umami?", 1, 5, 3)

# Funktion zur Rezeptsuche und Abrufen der Geschmacksprofile
def get_recipes_from_inventory():
    ingredients = list(st.session_state["inventory"].keys())
    if not ingredients:
        st.warning("Inventar ist leer. Bitte fügen Sie Zutaten hinzu.")
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

            # Abrufen des Geschmacksprofils und der Cuisine
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

                # Speichern der Geschmacksprofile und der Cuisine
                st.session_state["recipe_taste_data"] = pd.concat([
                    st.session_state["recipe_taste_data"],
                    pd.DataFrame([[recipe['title'], spicy, sweet, salty, sour, bitter, umami, cuisine]],
                                 columns=["Recipe", "Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami", "Cuisine"])
                ], ignore_index=True)

                recipe_titles.append(recipe['title'])
                recipe_links[recipe['title']] = recipe_link

        return recipe_titles, recipe_links
    else:
        st.error("Fehler beim Abrufen der Rezepte. Bitte überprüfen Sie Ihren API-Schlüssel.")
        return [], {}

# Funktion zum Trainieren des Machine Learning-Modells
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
        st.success("Das Machine Learning-Modell wurde erfolgreich trainiert!")

# Hauptseite der App
def recipe_page():
    st.title("Rezeptempfehlungen mit Machine Learning")
    set_user_preferences()

    selected_user = st.selectbox("Wählen Sie den Benutzer aus:", st.session_state["roommates"])
    st.session_state["selected_user"] = selected_user

    recipe_titles, recipe_links = get_recipes_from_inventory()
    
    if recipe_titles:
        selected_recipe = st.selectbox("Wählen Sie ein Rezept aus:", recipe_titles)
        train_ml_model()

# App starten
recipe_page()

