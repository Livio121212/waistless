import streamlit as st
import json
import os
import pandas as pd
from PIL import Image
from datetime import datetime
from settings_page import setup_flat_name, setup_roommates, settingspage
from fridge_page import fridge_page
from barcode_page import barcode_page
from recipe_page import recipepage
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import streamlit as st
import os
import json

# Funktion, um Benutzerdaten aus einer JSON-Datei zu laden
def load_user_data(username):
    """Lädt die JSON-Daten eines Benutzers."""
    user_file = f"{username}.json"
    if os.path.exists(user_file):
        with open(user_file, "r") as file:
            return json.load(file)
    return {"cooking_history": [], "ml_models": {}}

# Funktion, um Benutzerdaten in einer JSON-Datei zu speichern
def save_user_data(username, data):
    """Speichert Benutzerdaten in einer JSON-Datei."""
    user_file = f"{username}.json"
    with open(user_file, "w") as file:
        json.dump(data, file)

# Funktion zum Trainieren eines benutzerdefinierten Modells
def train_user_model(user):
    """
    Trainiert ein Machine-Learning-Modell für den angegebenen Benutzer basierend auf seiner Kochhistorie.
    """
    user_data = load_user_data(user)
    cooking_history = user_data.get("cooking_history", [])

    if len(cooking_history) < 3:  # Mindestens 3 Bewertungen erforderlich
        return None, None

    # Daten vorbereiten
    user_df = pd.DataFrame(cooking_history)
    X = user_df["Recipe"]
    y = user_df["Rating"]

    # LabelEncoder für Rezeptnamen
    encoder = LabelEncoder()
    X_encoded = encoder.fit_transform(X).reshape(-1, 1)

    # Modelltraining
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_encoded, y)

    # Modelle und Encoder speichern
    user_data["ml_models"] = {"model": model, "encoder": encoder}
    save_user_data(user, user_data)

    return model, encoder

# Funktion, um Rezeptbewertungen vorherzusagen
def predict_recipe_score(user, recipe):
    """
    Gibt eine vorhergesagte Bewertung für ein Rezept zurück, basierend auf dem Modell des Benutzers.
    """
    user_data = load_user_data(user)
    ml_models = user_data.get("ml_models", {})
    
    model = ml_models.get("model")
    encoder = ml_models.get("encoder")

    if not model or not encoder:
        return np.random.uniform(3, 5)  # Zufällige Bewertung, wenn kein Modell verfügbar ist

    # Rezept codieren und Vorhersage treffen
    try:
        recipe_encoded = encoder.transform([recipe]).reshape(-1, 1)
        predicted_score = model.predict(recipe_encoded)
        return np.clip(predicted_score[0], 1, 5)  # Bewertung auf Bereich 1-5 begrenzen
    except:
        return np.random.uniform(3, 5)  # Zufallsbewertung bei unbekanntem Rezept

# Funktion, um Rezeptvorschläge zu erstellen
def suggest_recipes(user, available_recipes):
    """
    Empfiehlt die besten Rezepte basierend auf vorhergesagten Bewertungen.
    """
    suggestions = []
    for recipe in available_recipes:
        score = predict_recipe_score(user, recipe)
        suggestions.append((recipe, score))
    suggestions.sort(key=lambda x: x[1], reverse=True)  # Nach Bewertung sortieren
    return suggestions[:5]  # Top-5-Vorschläge

# Integration mit der Rezeptseite
def recipepage():
    st.title("Rezeptvorschläge")

    # Sicherstellen, dass ein Benutzer angemeldet ist
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        user = st.session_state["username"]

        # Lade vorhandene Benutzerdaten
        user_data = load_user_data(user)
        st.session_state["cooking_history"] = user_data.get("cooking_history", [])

        # Beispielrezepte (normalerweise aus der Spoonacular-API geladen)
        available_recipes = ["Pasta Carbonara", "Vegane Bowl", "Kürbissuppe", "Pizza Margherita", "Ratatouille"]

        # Vorschläge generieren
        suggestions = suggest_recipes(user, available_recipes)

        st.subheader("Empfohlene Rezepte:")
        for recipe, score in suggestions:
            st.write(f"**{recipe}**: Vorhergesagte Bewertung {score:.1f} Sterne")

        # Rezeptbewertung
        st.subheader("Bewerte ein Rezept:")
        selected_recipe = st.selectbox("Wähle ein Rezept aus:", ["Bitte wählen..."] + available_recipes)
        rating = st.slider("Bewertung (1-5):", 1, 5, 3)
        
        if st.button("Bewertung speichern"):
            if selected_recipe != "Bitte wählen...":
                # Kochhistorie aktualisieren
                st.session_state["cooking_history"].append({
                    "Recipe": selected_recipe,
                    "Rating": rating
                })
                user_data["cooking_history"] = st.session_state["cooking_history"]
                save_user_data(user, user_data)
                st.success(f"Rezept '{selected_recipe}' mit {rating} Sternen bewertet!")
                # Modell neu trainieren
                train_user_model(user)
            else:
                st.warning("Bitte wähle ein Rezept aus.")
    else:
        st.warning("Bitte melde dich an, um Vorschläge zu erhalten.")

# Rezeptseite aufrufen
if st.session_state.get("logged_in", False):
    recipepage()
