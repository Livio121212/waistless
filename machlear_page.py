import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import streamlit as st
import requests
import re
from sklearn.preprocessing import StandardScaler

# Configuration
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'
RATINGS_FILE = 'recipe_ratings.csv'
RECIPE_DATA_FILE = 'recipe_data.csv'
CUISINES = ["Random", "Italian", "Asian", "Mexican", "Mediterranean", "American", "International"]
TASTE_FEATURES = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]

class RecipeRecommender(nn.Module):
    def __init__(self, n_users, n_recipes, n_cuisines, embedding_dim=32):
        super().__init__()
        
        # User tower (collaborative filtering part)
        self.user_embedding = nn.Embedding(n_users, embedding_dim)
        self.recipe_embedding = nn.Embedding(n_recipes, embedding_dim)
        
        # Content tower (content-based filtering part)
        self.content_network = nn.Sequential(
            nn.Linear(6 + n_cuisines, 64),  # 6 taste features + cuisine one-hot
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, embedding_dim),
            nn.ReLU()
        )
        
        # Combination layer
        self.combine_layers = nn.Sequential(
            nn.Linear(embedding_dim * 2, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, user_idx, recipe_idx, recipe_features):
        # Collaborative filtering path
        user_emb = self.user_embedding(user_idx)
        recipe_emb = self.recipe_embedding(recipe_idx)
        cf_vector = user_emb * recipe_emb
        
        # Content-based path
        content_vector = self.content_network(recipe_features)
        
        # Combine both paths
        combined = torch.cat([cf_vector, content_vector], dim=1)
        rating = self.combine_layers(combined)
        return rating * 5  # Scale to 1-5 range

def is_valid_recipe_title(title):
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
    formatted_title = re.sub(r'[^\w\s-]', '', title)
    formatted_title = formatted_title.replace(' ', '-').lower()
    return f"https://spoonacular.com/recipes/{formatted_title}-{recipe_id}"

def initialize_session_state():
    if "inventory" not in st.session_state:
        st.session_state["inventory"] = {}
    if "recipe_data" not in st.session_state:
        st.session_state["recipe_data"] = pd.DataFrame(columns=[
            "Recipe", "Cuisine"] + TASTE_FEATURES
        )
    if "user_ratings" not in st.session_state:
        st.session_state["user_ratings"] = pd.DataFrame(columns=["User", "Recipe", "Rating", "Cuisine"])
    if "hybrid_model" not in st.session_state:
        st.session_state["hybrid_model"] = None
    if "model_mappings" not in st.session_state:
        st.session_state["model_mappings"] = None
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {
            taste: 3 for taste in TASTE_FEATURES
        }
    if "selected_recipe" not in st.session_state:
        st.session_state["selected_recipe"] = None
    if "selected_cuisine" not in st.session_state:
        st.session_state["selected_cuisine"] = "Random"
    if "preferences_set" not in st.session_state:
        st.session_state["preferences_set"] = False

def train_hybrid_model():
    if len(st.session_state["user_ratings"]) < 2:
        return None, None, None, None
    
    # Create user and recipe mappings
    unique_users = pd.Series(range(len(st.session_state["user_ratings"]['User'].unique())))
    unique_recipes = pd.Series(range(len(st.session_state["recipe_data"]['Recipe'].unique())))
    
    user_mapping = dict(zip(st.session_state["user_ratings"]['User'].unique(), unique_users))
    recipe_mapping = dict(zip(st.session_state["recipe_data"]['Recipe'].unique(), unique_recipes))
    cuisine_mapping = {cuisine: idx for idx, cuisine in enumerate(CUISINES)}
    
    # Prepare training data
    X_users = torch.tensor([user_mapping[u] for u in st.session_state["user_ratings"]['User']])
    X_recipes = torch.tensor([recipe_mapping[r] for r in st.session_state["user_ratings"]['Recipe']])
    
    # Prepare recipe features
    recipe_features = []
    for _, row in st.session_state["user_ratings"].iterrows():
        recipe_row = st.session_state["recipe_data"][
            st.session_state["recipe_data"]['Recipe'] == row['Recipe']
        ].iloc[0]
        
        # Taste features
        taste_vals = torch.tensor([recipe_row[feat] for feat in TASTE_FEATURES], dtype=torch.float32)
        
        # Cuisine one-hot
        cuisine_one_hot = torch.zeros(len(cuisine_mapping))
        cuisine_one_hot[cuisine_mapping[recipe_row['Cuisine']]] = 1
        
        # Combine features
        features = torch.cat([taste_vals, cuisine_one_hot])
        recipe_features.append(features)
    
    X_features = torch.stack(recipe_features)
    y = torch.tensor(st.session_state["user_ratings"]['Rating'].values, dtype=torch.float32)
    
    # Initialize and train model
    model = RecipeRecommender(
        n_users=len(user_mapping),
        n_recipes=len(recipe_mapping),
        n_cuisines=len(cuisine_mapping)
    )
    
    optimizer = optim.Adam(model.parameters())
    criterion = nn.MSELoss()
    
    model.train()
    for epoch in range(100):  # Number of epochs
        optimizer.zero_grad()
        predictions = model(X_users, X_recipes, X_features)
        loss = criterion(predictions.squeeze(), y)
        loss.backward()
        optimizer.step()
    
    return model, user_mapping, recipe_mapping, cuisine_mapping

def predict_recipe_score(recipe_data):
    if st.session_state["hybrid_model"] is None:
        # Fallback to taste similarity if no model is available
        taste_similarity = sum(
            1 - abs(recipe_data[taste] - st.session_state["user_preferences"][taste]) / 4
            for taste in TASTE_FEATURES
        ) / len(TASTE_FEATURES)
        return taste_similarity * 5
    
    model = st.session_state["hybrid_model"]
    _, recipe_mapping, cuisine_mapping, _ = st.session_state["model_mappings"]
    
    # Prepare recipe features
    taste_vals = torch.tensor([recipe_data[feat] for feat in TASTE_FEATURES], dtype=torch.float32)
    cuisine_one_hot = torch.zeros(len(cuisine_mapping))
    cuisine_one_hot[cuisine_mapping[recipe_data['Cuisine']]] = 1
    recipe_features = torch.cat([taste_vals, cuisine_one_hot]).unsqueeze(0)
    
    # Get recipe index
    recipe_idx = torch.tensor([recipe_mapping[recipe_data['Recipe']]])
    user_idx = torch.tensor([0])  # Single user system for now
    
    # Make prediction
    model.eval()
    with torch.no_grad():
        prediction = model(user_idx, recipe_idx, recipe_features)
    
    return prediction.item()

def get_recipes_from_inventory():
    if not st.session_state["preferences_set"]:
        st.warning("Please set your cuisine preference and taste preferences first!")
        return [], {}

    ingredients = list(st.session_state["inventory"].keys())
    if not ingredients:
        st.info("Add some ingredients to your inventory to get recipe recommendations!")
        return [], {}

    try:
        params = {
            "ingredients": ",".join(ingredients),
            "number": 15,
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
                    
                detailed_recipe_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
                detailed_params = {"apiKey": API_KEY}
                detailed_response = requests.get(detailed_recipe_url, params=detailed_params)
                detailed_response.raise_for_status()
                recipe_details = detailed_response.json()
                
                cuisines = recipe_details.get("cuisines", [])
                if cuisines:
                    cuisine = cuisines[0]
                else:
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
                
                if st.session_state["selected_cuisine"] != "Random" and cuisine != st.session_state["selected_cuisine"]:
                    continue

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
                
                recipe_data = st.session_state["recipe_data"][
                    st.session_state["recipe_data"]["Recipe"] == title
                ].iloc[0]
                
                score = predict_recipe_score(recipe_data)
                recipe_scores.append((title, link, score))
                
            except (KeyError, IndexError, requests.RequestException) as e:
                continue
        
        if not recipe_scores:
            if st.session_state["selected_cuisine"] != "Random":
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

def recipe_page():
    initialize_session_state()
    
    st.title("Smart Recipe Recommendations")
    
    # First step: Select cuisine
    st.subheader("Step 1: Select Cuisine Type")
    selected_cuisine = st.selectbox(
        "Choose your preferred cuisine:",
        CUISINES,
        index=CUISINES.index(st.session_state["selected_cuisine"])
    )
    st.session_state["selected_cuisine"] = selected_cuisine
    
    # Second step: Set taste preferences
    st.subheader("Step 2: Set Your Taste Preferences")
    preferences_changed = False
    for taste in TASTE_FEATURES:
        new_value = st.slider(
            f"How much do you like {taste.lower()}?",
            1, 5,
            st.session_state["user_preferences"][taste],
            help=f"Rate how much you enjoy {taste.lower()} flavors"
        )
        if new_value != st.session_state["user_preferences"][taste]:
            preferences_changed = True
            st.session_state["user_preferences"][taste] = new_value
    
    # Button to confirm preferences
    if st.button("Confirm Preferences"):
        st.session_state["preferences_set"] = True
        st.success("Preferences saved! You can now get recipe recommendations.")
        st.experimental_rerun()
    
    # Only proceed with recipe fetching if preferences are set
    if st.session_state["preferences_set"]:
        # Train/update hybrid model
        model, user_mapping, recipe_mapping, cuisine_mapping = train_hybrid_model()
        if model is not None:
            st.session_state["hybrid_model"] = model
            st.session_state["model_mappings"] = (user_mapping, recipe_mapping, cuisine_mapping)
        
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
                    
                    score = predict_recipe_score(recipe_data)
                    st.write(f"Match Score: {score:.1f}/5")
                    
                    if st.button(f"Select Recipe #{idx + 1}"):
                        st.session_state["selected_recipe"] = title
            
            # Rating system
            st.subheader("Rate a Recipe")
            recipe_to_rate = st.radio(
                "Select recipe to rate:",
                displayed_recipes,
                index=displayed_recipes.index(st.session_state["selected_recipe"]) 
                if st.session_state["selected_recipe"] in displayed_recipes else 0
            )
            
            rating = st.slider("Rating", 1, 5, 3)
            
            if st.button("Submit Rating"):
                try:
                    recipe_data = st.session_state["recipe_data"][
                        st.session_state["recipe_data"]["Recipe"] == recipe_to_rate
                    ].iloc[0]
                    
                    new_rating = pd.DataFrame([{
                        "User": 0,  # Single user system for now
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
                    
                    # Save ratings to CSV
                    st.session_state["user_ratings"].to_csv(RATINGS_FILE, index=False)
                    st.session_state["recipe_data"].to_csv(RECIPE_DATA_FILE, index=False)
                    
                    # Retrain model with new rating
                    model, user_mapping, recipe_mapping, cuisine_mapping = train_hybrid_model()
                    if model is not None:
                        st.session_state["hybrid_model"] = model
                        st.session_state["model_mappings"] = (user_mapping, recipe_mapping, cuisine_mapping)
                    
                    st.experimental_rerun()
                    
                except Exception as e:
                    st.error(f"Unable to submit rating. Please try again. Error: {str(e)}")
            
            # Display ratings history
            if not st.session_state["user_ratings"].empty:
                st.subheader("Your Previous Ratings")
                st.dataframe(st.session_state["user_ratings"][["Recipe", "Rating", "Cuisine"]])

if __name__ == "__main__":
    recipe_page()