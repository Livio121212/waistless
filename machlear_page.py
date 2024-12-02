import streamlit as st
import pandas as pd
import requests
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import re
import json
import os

# API configuration
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'
CACHE_FILE = 'recipe_cache.json'

# Load cache if exists
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save cache
def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

# Initialize cache
RECIPE_CACHE = load_cache()

def is_valid_recipe_title(title):
    if not title:
        return False
    question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
    title_lower = title.lower()
    return not ('?' in title or any(title_lower.startswith(word) for word in question_words))

def format_recipe_link(title, recipe_id):
    formatted_title = re.sub(r'[^\w\s-]', '', title)
    formatted_title = formatted_title.replace(' ', '-').lower()
    return f"https://spoonacular.com/recipes/{formatted_title}-{recipe_id}"

def initialize_session_state():
    if "inventory" not in st.session_state:
        st.session_state["inventory"] = {}
    if "recipe_data" not in st.session_state:
        st.session_state["recipe_data"] = pd.DataFrame(columns=[
            "Recipe", "Cuisine", "Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"
        ])
    if "user_ratings" not in st.session_state:
        st.session_state["user_ratings"] = pd.DataFrame(columns=["Recipe", "Rating", "Cuisine"])
    if "ml_model" not in st.session_state:
        st.session_state["ml_model"] = None
    if "scaler" not in st.session_state:
        st.session_state["scaler"] = StandardScaler()
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {
            "Spicy": 3, "Sweet": 3, "Salty": 3,
            "Sour": 3, "Bitter": 3, "Umami": 3
        }
    if "selected_recipe" not in st.session_state:
        st.session_state["selected_recipe"] = None
    if "selected_cuisine" not in st.session_state:
        st.session_state["selected_cuisine"] = "Any"
    if "api_calls_remaining" not in st.session_state:
        st.session_state["api_calls_remaining"] = 150  # Daily limit

def get_cached_recipe_details(recipe_id):
    return RECIPE_CACHE.get(str(recipe_id))

def cache_recipe_details(recipe_id, details):
    RECIPE_CACHE[str(recipe_id)] = details
    save_cache(RECIPE_CACHE)

def get_recipes_from_inventory():
    ingredients = list(st.session_state["inventory"].keys())
    if not ingredients:
        st.info("Add some ingredients to your inventory to get recipe recommendations!")
        return [], {}

    try:
        # First API call - get basic recipe information
        params = {
            "ingredients": ",".join(ingredients),
            "number": 10,  # Reduced number to minimize API calls
            "ranking": 2,
            "apiKey": API_KEY
        }

        response = requests.get(SPOONACULAR_URL, params=params)
        response.raise_for_status()
        recipes = response.json()
        
        recipe_titles = []
        recipe_links = {}
        recipe_scores = []
        
        for recipe in recipes:
            try:
                recipe_id = recipe.get("id")
                title = recipe.get("title")
                
                if not recipe_id or not title or not is_valid_recipe_title(title):
                    continue

                # Check cache first
                cached_details = get_cached_recipe_details(recipe_id)
                if cached_details:
                    recipe_details = cached_details
                else:
                    # Only make API call if not in cache
                    if st.session_state["api_calls_remaining"] <= 0:
                        st.error("Daily API limit reached. Please try again tomorrow.")
                        return [], {}
                    
                    detailed_recipe_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
                    detailed_params = {"apiKey": API_KEY}
                    detailed_response = requests.get(detailed_recipe_url, params=detailed_params)
                    detailed_response.raise_for_status()
                    recipe_details = detailed_response.json()
                    
                    # Cache the results
                    cache_recipe_details(recipe_id, recipe_details)
                    st.session_state["api_calls_remaining"] -= 1

                # Determine cuisine
                cuisines = recipe_details.get("cuisines", [])
                if cuisines:
                    cuisine = cuisines[0]
                else:
                    dish_types = recipe_details.get("dishTypes", [])
                    cuisine = "International"
                    for dish_type in dish_types:
                        if "italian" in dish_type:
                            cuisine = "Italian"
                            break
                        elif any(x in dish_type for x in ["asian", "chinese", "japanese"]):
                            cuisine = "Asian"
                            break
                        elif "mexican" in dish_type:
                            cuisine = "Mexican"
                            break
                        elif "mediterranean" in dish_type:
                            cuisine = "Mediterranean"
                            break
                        elif "american" in dish_type:
                            cuisine = "American"
                            break

                # Skip if cuisine doesn't match selection
                if st.session_state["selected_cuisine"] != "Any" and cuisine != st.session_state["selected_cuisine"]:
                    continue

                link = format_recipe_link(title, recipe_id)
                
                # Add or update recipe data
                if title not in st.session_state["recipe_data"]["Recipe"].values:
                    new_recipe = {
                        "Recipe": title,
                        "Cuisine": cuisine,
                        "Spicy": min(recipe_details.get("spiciness", 3), 5),
                        "Sweet": min(recipe_details.get("sweetness", 3), 5),
                        "Salty": min(recipe_details.get("saltiness", 3), 5),
                        "Sour": min(recipe_details.get("sourness", 3), 5),
                        "Bitter": min(recipe_details.get("bitterness", 3), 5),
                        "Umami": min(recipe_details.get("savoriness", 3), 5)
                    }
                    st.session_state["recipe_data"] = pd.concat([
                        st.session_state["recipe_data"],
                        pd.DataFrame([new_recipe])
                    ], ignore_index=True)

                recipe_data = st.session_state["recipe_data"][
                    st.session_state["recipe_data"]["Recipe"] == title
                ].iloc[0]
                
                score = predict_recipe_score(recipe_data)
                recipe_scores.append((title, link, score))
                
            except Exception as e:
                st.warning(f"Skipping recipe due to error: {str(e)}")
                continue
        
        if not recipe_scores:
            if st.session_state["selected_cuisine"] != "Any":
                st.warning(f"No {st.session_state['selected_cuisine']} recipes found. Try selecting a different cuisine or adding more ingredients!")
            else:
                st.warning("No valid recipes found for your ingredients. Try adding more ingredients!")
            return [], {}
            
        recipe_scores.sort(key=lambda x: x[2], reverse=True)
        recipe_titles = [title for title, _, _ in recipe_scores]
        recipe_links = {title: link for title, link, _ in recipe_scores}

        return recipe_titles, recipe_links

    except requests.RequestException as e:
        st.error(f"Unable to fetch recipes: {str(e)}")
        return [], {}

def predict_recipe_score(recipe_data):
    taste_features = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]
    taste_similarity = sum(
        1 - abs(recipe_data[taste] - st.session_state["user_preferences"][taste]) / 4
        for taste in taste_features
    ) / len(taste_features)
    
    if st.session_state["ml_model"] is not None:
        cuisine_dummies = pd.get_dummies(pd.Series([recipe_data["Cuisine"]]), prefix="Cuisine")
        X = pd.DataFrame([recipe_data[taste_features].values], columns=taste_features)
        X = pd.concat([X, cuisine_dummies], axis=1)
        X_scaled = st.session_state["scaler"].transform(X)
        predicted_rating = st.session_state["ml_model"].predict(X_scaled)[0]
        return (predicted_rating + taste_similarity * 5) / 2
    return taste_similarity * 5

def train_model():
    if len(st.session_state["user_ratings"]) < 2:
        return None
    
    training_data = st.session_state["user_ratings"].merge(
        st.session_state["recipe_data"],
        on=["Recipe", "Cuisine"]
    )
    
    if len(training_data) < 2:
        return None
    
    taste_features = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]
    cuisine_dummies = pd.get_dummies(training_data["Cuisine"], prefix="Cuisine")
    
    X = pd.concat([training_data[taste_features], cuisine_dummies], axis=1)
    y = training_data["Rating"]
    
    X_scaled = st.session_state["scaler"].fit_transform(X)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    
    return model

def recipe_page():
    initialize_session_state()
    
    st.title("Smart Recipe Recommendations")
    
    # Display remaining API calls
    st.sidebar.write(f"API Calls Remaining Today: {st.session_state['api_calls_remaining']}")
    
    cuisines = ["Any", "Italian", "Asian", "Mexican", "Mediterranean", "American", "International"]
    selected_cuisine = st.selectbox(
        "Select cuisine type:",
        cuisines,
        index=cuisines.index(st.session_state["selected_cuisine"])
    )
    st.session_state["selected_cuisine"] = selected_cuisine
    
    st.subheader("Your Taste Preferences")
    for taste, value in st.session_state["user_preferences"].items():
        new_value = st.slider(
            f"How much do you like {taste.lower()}?",
            1, 5, value,
            help=f"Rate how much you enjoy {taste.lower()} flavors"
        )
        st.session_state["user_preferences"][taste] = new_value
    
    st.session_state["ml_model"] = train_model()
    
    recipe_titles, recipe_links = get_recipes_from_inventory()
    
    if recipe_titles:
        st.subheader("Recipe Recommendations")
        displayed_recipes = recipe_titles[:3]
        cols = st.columns(3)
        
        for idx, (col, title) in enumerate(zip(cols, displayed_recipes)):
            with col:
                recipe_data = st.session_state["recipe_data"][
                    st.session_state["recipe_data"]["Recipe"] == title
                ].iloc[0]
                
                st.write(f"**{title}**")
                st.write(f"Cuisine: {recipe_data['Cuisine']}")
                st.write(f"[View Recipe]({recipe_links[title]})")
                
                if st.session_state["ml_model"] is not None:
                    score = predict_recipe_score(recipe_data)
                    st.write(f"Match Score: {score:.1f}/5")
                
                if st.button(f"Select Recipe #{idx + 1}"):
                    st.session_state["selected_recipe"] = title
        
        st.subheader("Rate a Recipe")
        recipe_to_rate = st.radio(
            "Select recipe to rate:",
            displayed_recipes,
            index=displayed_recipes.index(st.session_state["selected_recipe"]) if st.session_state["selected_recipe"] in displayed_recipes else 0
        )
        
        rating = st.slider("Rating", 1, 5, 3)
        
        if st.button("Submit Rating"):
            try:
                recipe_data = st.session_state["recipe_data"][
                    st.session_state["recipe_data"]["Recipe"] == recipe_to_rate
                ].iloc[0]
                
                new_rating = pd.DataFrame([{
                    "Recipe": recipe_to_rate,
                    "Rating": rating,
                    "Cuisine": recipe_data["Cuisine"]
                }])
                
                st.session_state["user_ratings"] = pd.concat([
                    st.session_state["user_ratings"],
                    new_rating
                ], ignore_index=True)
                
                st.success("Rating submitted successfully!")
                st.session_state["selected_recipe"] = None
                st.session_state["ml_model"] = train_model()
                
            except Exception as e:
                st.error(f"Unable to submit rating: {str(e)}")
        
        if not st.session_state["user_ratings"].empty:
            st.subheader("Your Previous Ratings")
            st.dataframe(st.session_state["user_ratings"][["Recipe", "Rating", "Cuisine"]])

if __name__ == "__main__":
    recipe_page()
    