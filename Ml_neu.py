import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import os
import json

# Funktion, um Benutzerdaten aus einer JSON-Datei zu laden
def load_user_data(username):
    """Lädt die JSON-Daten eines Benutzers."""
    user_file = f"{username}_data.json"
    if os.path.exists(user_file):
        with open(user_file, "r") as file:
            return json.load(file)
    return {"cooking_history": [], "ml_models": {}}

# Funktion, um Benutzerdaten in einer JSON-Datei zu speichern
def save_user_data(username, data):
    """Speichert Benutzerdaten in einer JSON-Datei."""
    user_file = f"{username}_data.json"
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
