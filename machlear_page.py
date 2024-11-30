mport streamlit as st
import pandas as pd
import requests
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# API configuration
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

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

def get_recipes_from_inventory():
    """Fetch recipes based on available ingredients"""
    ingredients = list(st.session_state["inventory"].keys())
    if not ingredients:
        st.info("Add some ingredients to your inventory to get recipe recommendations!")
        return [], {}

    params = {
        "ingredients": ",".join(ingredients),
        "number": 10,
        "ranking": 2,
        "apiKey": API_KEY
    }

    try:
        response = requests.get(SPOONACULAR_URL, params=params)
        response.raise_for_status()
        recipes = response.json()
        
        recipe_titles = []
        recipe_links = {}
        cuisines = ["Italian", "Asian", "Mexican", "Mediterranean", "American"]
        
        for recipe in recipes:
            recipe_id = recipe["id"]
            title = recipe["title"]
            link = f"https://spoonacular.com/recipes/{title.replace(' ', '-')}-{recipe_id}"
            
            if title not in st.session_state["recipe_data"]["Recipe"].values:
                new_recipe = {
                    "Recipe": title,
                    "Cuisine": np.random.choice(cuisines),
                    "Spicy": np.random.randint(1, 6),
                    "Sweet": np.random.randint(1, 6),
                    "Salty": np.random.randint(1, 6),
                    "Sour": np.random.randint(1, 6),
                    "Bitter": np.random.randint(1, 6),
                    "Umami": np.random.randint(1, 6)
                }
                st.session_state["recipe_data"] = pd.concat([
                    st.session_state["recipe_data"],
                    pd.DataFrame([new_recipe])
                ], ignore_index=True)
            
            recipe_titles.append(title)
            recipe_links[title] = link

        return recipe_titles, recipe_links

    except requests.RequestException:
        st.info("Unable to fetch recipes at the moment. Please try again later.")
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
    # Initialize all session state variables first
    initialize_session_state()
    
    st.title("Smart Recipe Recommendations")
    
    # Get user preferences
    st.subheader("Your Taste Preferences")
    for taste, value in st.session_state["user_preferences"].items():
        st.session_state["user_preferences"][taste] = st.slider(
            f"How much do you like {taste.lower()}?",
            1, 5, value,
            help=f"Rate how much you enjoy {taste.lower()} flavors"
        )
    
    # Get and display recipes
    recipe_titles, recipe_links = get_recipes_from_inventory()
    
    if recipe_titles:
        st.subheader("Recipe Recommendations")
        
        # Train model if enough ratings
        if len(st.session_state["user_ratings"]) >= 2:
            st.session_state["ml_model"] = train_model()
            
            if st.session_state["ml_model"]:
                for title in recipe_titles[:3]:
                    recipe_data = st.session_state["recipe_data"][
                        st.session_state["recipe_data"]["Recipe"] == title
                    ]
                    if len(recipe_data) > 0:
                        st.write(f"**{title}**")
                        st.write(f"[View Recipe]({recipe_links[title]})")
        else:
            selected_recipe = np.random.choice(recipe_titles)
            st.write(f"**{selected_recipe}**")
            st.write(f"[View Recipe]({recipe_links[selected_recipe]})")
        
        # Rating system
        st.subheader("Rate a Recipe")
        recipe_to_rate = st.selectbox("Select recipe:", recipe_titles)
        rating = st.slider("Rating", 1, 5, 3)
        
        if st.button("Submit Rating"):
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
            st.experimental_rerun()
    
    # Display ratings history
    if not st.session_state["user_ratings"].empty:
        st.subheader("Your Previous Ratings")
        st.dataframe(st.session_state["user_ratings"][["Recipe", "Rating", "Cuisine"]])

if __name__ == "__main__":
    recipe_page()