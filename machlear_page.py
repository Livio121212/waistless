import streamlit as st
import pandas as pd
import requests
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import re

# API configuration
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

def is_valid_recipe_title(title):
    """Check if a recipe title is valid (not a question, not empty, etc.)"""
    if not title:
        return False
    
    question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
    title_lower = title.lower()
    
    if '?' in title:
        return False
        
    if any(title_lower.startswith(word) for word in question_words):
        return False
        
    return True

def format_recipe_link(title, recipe_id):
    """Format the recipe link properly"""
    formatted_title = re.sub(r'[^\w\s-]', '', title)
    formatted_title = formatted_title.replace(' ', '-').lower()
    return f"https://spoonacular.com/recipes/{formatted_title}-{recipe_id}"

def initialize_session_state():
    """Initialize all required session state variables"""
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

def predict_recipe_score(recipe_data):
    """Predict recipe score based on user preferences and ML model"""
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
        final_score = (predicted_rating + taste_similarity * 5) / 2
    else:
        final_score = taste_similarity * 5
    
    return final_score

def get_recipes_from_inventory():
    """Fetch recipes based on available ingredients"""
    ingredients = list(st.session_state["inventory"].keys())
    if not ingredients:
        st.info("Add some ingredients to your inventory to get recipe recommendations!")
        return [], {}

    try:
        params = {
            "ingredients": ",".join(ingredients),
            "number": 30,  # Increased to ensure we get enough valid recipes after filtering
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
                    
                # Get detailed recipe information including cuisine
                detailed_recipe_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
                detailed_params = {"apiKey": API_KEY}
                detailed_response = requests.get(detailed_recipe_url, params=detailed_params)
                detailed_response.raise_for_status()
                recipe_details = detailed_response.json()
                
                # Get cuisine from API or default to a general category
                cuisines = recipe_details.get("cuisines", [])
                if cuisines:
                    cuisine = cuisines[0]  # Take the first cuisine if multiple are provided
                else:
                    # Try to determine cuisine from dish type or default to "International"
                    dish_types = recipe_details.get("dishTypes", [])
                    if "italian" in dish_types:
                        cuisine = "Italian"
                    elif "asian" in dish_types or "chinese" in dish_types or "japanese" in dish_types:
                        cuisine = "Asian"
                    elif "mexican" in dish_types:
                        cuisine = "Mexican"
                    elif "mediterranean" in dish_types:
                        cuisine = "Mediterranean"
                    elif "american" in dish_types:
                        cuisine = "American"
                    else:
                        cuisine = "International"
                
                link = format_recipe_link(title, recipe_id)
                
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
                
                # Get recipe data and calculate score
                recipe_data = st.session_state["recipe_data"][
                    st.session_state["recipe_data"]["Recipe"] == title
                ].iloc[0]
                
                # Filter by cuisine if selected
                if st.session_state["selected_cuisine"] != "Any" and recipe_data["Cuisine"] != st.session_state["selected_cuisine"]:
                    continue
                
                score = predict_recipe_score(recipe_data)
                recipe_scores.append((title, link, score))
                
            except (KeyError, IndexError, requests.RequestException) as e:
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
        st.error(f"Unable to fetch recipes at the moment. Please try again later. Error: {str(e)}")
        return [], {}

def train_model():
    """Train the recommendation model based on user ratings"""
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
    """Main recipe page function"""
    initialize_session_state()
    
    st.title("Smart Recipe Recommendations")
    
    # Add cuisine selection
    cuisines = ["Any", "Italian", "Asian", "Mexican", "Mediterranean", "American", "International"]
    selected_cuisine = st.selectbox(
        "Select cuisine type:",
        cuisines,
        index=cuisines.index(st.session_state["selected_cuisine"])
    )
    st.session_state["selected_cuisine"] = selected_cuisine
    
    # Get user preferences
    st.subheader("Your Taste Preferences")
    preferences_changed = False
    for taste, value in st.session_state["user_preferences"].items():
        new_value = st.slider(
            f"How much do you like {taste.lower()}?",
            1, 5, value,
            help=f"Rate how much you enjoy {taste.lower()} flavors"
        )
        if new_value != value:
            preferences_changed = True
            st.session_state["user_preferences"][taste] = new_value
    
    # Train/update model with existing ratings
    st.session_state["ml_model"] = train_model()
    
    # Get and display recipes
    recipe_titles, recipe_links = get_recipes_from_inventory()
    
    if recipe_titles:
        st.subheader("Recipe Recommendations")
        
        # Get top 3 recommendations
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
        
        # Rating system
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
                
                # Retrain model with new rating
                st.session_state["ml_model"] = train_model()
                
            except Exception as e:
                st.error(f"Unable to submit rating. Please try again. Error: {str(e)}")
        
        # Display ratings history
        if not st.session_state["user_ratings"].empty:
            st.subheader("Your Previous Ratings")
            st.dataframe(st.session_state["user_ratings"][["Recipe", "Rating", "Cuisine"]])

if __name__ == "__main__":
    recipe_page()