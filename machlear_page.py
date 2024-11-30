import streamlit as st
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
    if "selected_recipe" not in st.session_state:
        st.session_state["selected_recipe"] = None

def get_recipes_from_inventory():
    """Fetch recipes based on available ingredients"""
    # ... keep existing code (get_recipes_from_inventory function implementation)

def train_model():
    """Train the recommendation model based on user ratings"""
    # ... keep existing code (train_model function implementation)

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
                # Display top 3 recommendations
                displayed_recipes = recipe_titles[:3]
                for idx, title in enumerate(displayed_recipes, 1):
                    recipe_data = st.session_state["recipe_data"][
                        st.session_state["recipe_data"]["Recipe"] == title
                    ]
                    if len(recipe_data) > 0:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**{idx}. {title}**")
                            st.write(f"[View Recipe]({recipe_links[title]})")
                        with col2:
                            if st.button(f"Select #{idx}", key=f"select_{idx}"):
                                st.session_state["selected_recipe"] = title
        else:
            # Display random 3 recipes when not enough ratings
            displayed_recipes = np.random.choice(recipe_titles, size=min(3, len(recipe_titles)), replace=False)
            for idx, title in enumerate(displayed_recipes, 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{idx}. {title}**")
                    st.write(f"[View Recipe]({recipe_links[title]})")
                with col2:
                    if st.button(f"Select #{idx}", key=f"select_{idx}"):
                        st.session_state["selected_recipe"] = title
        
        # Rating system
        if st.session_state["selected_recipe"]:
            st.subheader("Rate Recipe")
            st.write(f"Rating for: **{st.session_state['selected_recipe']}**")
            rating = st.slider("Rating", 1, 5, 3)
            
            if st.button("Submit Rating"):
                recipe_data = st.session_state["recipe_data"][
                    st.session_state["recipe_data"]["Recipe"] == st.session_state["selected_recipe"]
                ].iloc[0]
                
                new_rating = pd.DataFrame([{
                    "Recipe": st.session_state["selected_recipe"],
                    "Rating": rating,
                    "Cuisine": recipe_data["Cuisine"]
                }])
                
                st.session_state["user_ratings"] = pd.concat([
                    st.session_state["user_ratings"],
                    new_rating
                ], ignore_index=True)
                
                st.success("Rating submitted successfully!")
                # Clear the selected recipe after rating
                st.session_state["selected_recipe"] = None
                st.experimental_rerun()
    
    # Display ratings history
    if not st.session_state["user_ratings"].empty:
        st.subheader("Your Previous Ratings")
        st.dataframe(st.session_state["user_ratings"][["Recipe", "Rating", "Cuisine"]])

if __name__ == "__main__":
    recipe_page()