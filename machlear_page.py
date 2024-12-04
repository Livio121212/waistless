import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime

# API configuration
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'
CUISINES = ["International", "Italian", "Asian", "Mexican", "Mediterranean", "American"]
COURSE_TYPES = ["starter", "main course", "dessert"]

def initialize_session_state():
    """Initialize all required session state variables"""
    if "inventory" not in st.session_state:
        st.session_state["inventory"] = {
            "Tomato": {"Quantity": 5, "Unit": "gram", "Price": 3.0},
            "Banana": {"Quantity": 3, "Unit": "gram", "Price": 5.0},
            "Onion": {"Quantity": 2, "Unit": "piece", "Price": 1.5},
            "Garlic": {"Quantity": 3, "Unit": "clove", "Price": 0.5},
            "Olive Oil": {"Quantity": 1, "Unit": "liter", "Price": 8.0},
        }
    if "roommates" not in st.session_state:
        st.session_state["roommates"] = ["Bilbo", "Frodo", "Gandalf der Weise"]
    if "selected_user" not in st.session_state:
        st.session_state["selected_user"] = None
    if "recipe_suggestions" not in st.session_state:
        st.session_state["recipe_suggestions"] = []
    if "recipe_links" not in st.session_state:
        st.session_state["recipe_links"] = {}
    if "selected_recipe" not in st.session_state:
        st.session_state["selected_recipe"] = None
    if "selected_recipe_link" not in st.session_state:
        st.session_state["selected_recipe_link"] = None
    if "cooking_history" not in st.session_state:
        st.session_state["cooking_history"] = []
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = {}
    if "ml_models" not in st.session_state:
        st.session_state["ml_models"] = {}
    if "user_low_rated_recipes" not in st.session_state:
        st.session_state["user_low_rated_recipes"] = {}

def get_recipe_details(recipe_id):
    """Get detailed recipe information from Spoonacular API"""
    try:
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        response = requests.get(url, params={"apiKey": API_KEY})
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

def get_recipe_course_type(recipe_id):
    """Get course type for a recipe"""
    details = get_recipe_details(recipe_id)
    if details:
        dish_types = details.get("dishTypes", [])
        if "appetizer" in dish_types or "starter" in dish_types:
            return "starter"
        elif "dessert" in dish_types:
            return "dessert"
        else:
            return "main course"
    return "main course"

def get_recipe_cuisine(recipe_id):
    """Get cuisine type for a recipe"""
    details = get_recipe_details(recipe_id)
    if details:
        cuisines = details.get("cuisines", [])
        return cuisines[0] if cuisines else "International"
    return "International"

def predict_recipe_score(cuisine, user):
    """Predict score for a recipe based on user's preferences"""
    if user not in st.session_state["ml_models"] or st.session_state["ml_models"][user] is None:
        return random.uniform(3, 5)  # Return random score if no model exists

    # Create feature vector for prediction
    cuisine_features = pd.get_dummies([cuisine], columns=CUISINES)
    return st.session_state["ml_models"][user].predict(cuisine_features)[0]

def get_recipes_from_inventory(selected_ingredients=None, user=None, course_type=None):
    """Fetch and filter recipes from Spoonacular API"""
    ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
    if not ingredients:
        st.warning("Inventory is empty!")
        return [], {}
    
    params = {
        "ingredients": ",".join(ingredients),
        "number": 100,
        "ranking": 2,
        "apiKey": API_KEY
    }
    
    try:
        response = requests.get(SPOONACULAR_URL, params=params)
        if response.status_code == 200:
            recipes = response.json()
            recipe_scores = []
            
            # Get user's low-rated recipes
            user_low_rated = st.session_state["user_low_rated_recipes"].get(user, set())
            
            for recipe in recipes:
                # Skip recipes that were rated 2 or lower by this user
                if recipe['title'] in user_low_rated:
                    continue
                    
                # Filter by course type if specified
                if course_type:
                    recipe_course = get_recipe_course_type(recipe['id'])
                    if recipe_course != course_type:
                        continue
                
                cuisine = get_recipe_cuisine(recipe['id'])
                score = predict_recipe_score(cuisine, user)
                recipe_scores.append((recipe, score))
            
            # Sort recipes by predicted score
            recipe_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 3 recipes
            top_recipes = recipe_scores[:3]
            recipe_titles = []
            recipe_links = {}
            
            for recipe, score in top_recipes:
                recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}"
                missed_ingredients = [item["name"] for item in recipe.get("missedIngredients", [])]
                
                recipe_titles.append(recipe['title'])
                recipe_links[recipe['title']] = {
                    "link": recipe_link,
                    "missed_ingredients": missed_ingredients,
                    "cuisine": get_recipe_cuisine(recipe['id'])
                }
            
            return recipe_titles, recipe_links
    except Exception as e:
        st.error(f"Error fetching recipes: {str(e)}")
    return [], {}

def rate_recipe(recipe_title, recipe_link, cuisine):
    """Allow user to rate a recipe and update ML model"""
    st.write("---")
    st.subheader("Rate this recipe")
    
    rating = st.slider("How would you rate this recipe?", 1, 5, 3)
    
    if st.button("Submit Rating"):
        # Add to cooking history
        history_entry = {
            "Person": st.session_state["selected_user"],
            "Recipe": recipe_title,
            "Rating": rating,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state["cooking_history"].append(history_entry)
        
        # Update user preferences
        if st.session_state["selected_user"] not in st.session_state["user_preferences"]:
            st.session_state["user_preferences"][st.session_state["selected_user"]] = pd.DataFrame(
                columns=["Recipe", "Cuisine", "Rating"]
            )
        
        # Add rating to user preferences
        new_rating = pd.DataFrame([{
            "Recipe": recipe_title,
            "Cuisine": cuisine,
            "Rating": rating
        }])
        
        st.session_state["user_preferences"][st.session_state["selected_user"]] = pd.concat([
            st.session_state["user_preferences"][st.session_state["selected_user"]],
            new_rating
        ], ignore_index=True)
        
        # Track low-rated recipes
        if rating <= 2:
            if st.session_state["selected_user"] not in st.session_state["user_low_rated_recipes"]:
                st.session_state["user_low_rated_recipes"][st.session_state["selected_user"]] = set()
            st.session_state["user_low_rated_recipes"][st.session_state["selected_user"]].add(recipe_title)
        
        # Retrain ML model
        user_data = st.session_state["user_preferences"][st.session_state["selected_user"]]
        if len(user_data) >= 2:  # Need at least 2 ratings to train
            X = pd.get_dummies(user_data["Cuisine"])
            y = user_data["Rating"]
            
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            st.session_state["ml_models"][st.session_state["selected_user"]] = model
        
        st.success("Rating submitted successfully!")
        st.session_state["selected_recipe"] = None
        st.session_state["selected_recipe_link"] = None
        st.experimental_rerun()

def recipepage():
    """Main recipe recommendation page"""
    st.title("You think you can cook! Better take a recipe!")
    st.subheader("Delulu is not the solulu")
    
    initialize_session_state()
    
    if st.session_state["roommates"]:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate
        
        st.subheader("Recipe search options")
        
        # Course type selection
        course_type = st.selectbox(
            "What type of dish would you like?",
            COURSE_TYPES,
            key="course_type_selector"
        )
        
        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))
        
        with st.form("recipe_form"):
            if search_mode == "Custom (choose ingredients)":
                selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
            else:
                selected_ingredients = None
            
            search_button = st.form_submit_button("Get recipe suggestions")
            if search_button:
                recipe_titles, recipe_links = get_recipes_from_inventory(
                    selected_ingredients, 
                    selected_roommate,
                    course_type
                )
                st.session_state["recipe_suggestions"] = recipe_titles
                st.session_state["recipe_links"] = recipe_links

        if st.session_state["recipe_suggestions"]:
            st.subheader("Choose a recipe to make")
            for title in st.session_state["recipe_suggestions"]:
                link = st.session_state["recipe_links"][title]["link"]
                missed_ingredients = st.session_state["recipe_links"][title]["missed_ingredients"]
                cuisine = st.session_state["recipe_links"][title]["cuisine"]

                st.write(f"- **{title}** ({cuisine}): ([View Recipe]({link}))")
                if missed_ingredients:
                    st.write(f"  *Extra ingredients needed:* {', '.join(missed_ingredients)}")

            selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + st.session_state["recipe_suggestions"])
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!")
                
    else:
        st.warning("No roommates available.")
        return

    if st.session_state["selected_recipe"] and st.session_state["selected_recipe_link"]:
        cuisine = st.session_state["recipe_links"][st.session_state["selected_recipe"]]["cuisine"]
        rate_recipe(
            st.session_state["selected_recipe"],
            st.session_state["selected_recipe_link"],
            cuisine
        )

    if st.session_state["cooking_history"]:
        with st.expander("Cooking History"):
            history_data = [
                {
                    "Person": entry["Person"],
                    "Recipe": entry["Recipe"],
                    "Rating": entry["Rating"],
                    "Date": entry["Date"]
                }
                for entry in st.session_state["cooking_history"]
            ]
            st.table(pd.DataFrame(history_data))

if __name__ == "__main__":
    recipepage()