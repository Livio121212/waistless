import streamlit as st
import requests
import random
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

API_KEY = '7c3d0f2a157542d9a49c93cdf50653a4'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# Session state initialization
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
if "cooking_history" not in st.session_state:
    st.session_state["cooking_history"] = []
if "user_preferences" not in st.session_state:
    st.session_state["user_preferences"] = {}

# Recipe suggestion function
def get_recipes_from_inventory(selected_ingredients=None):
    ingredients = selected_ingredients if selected_ingredients else list(st.session_state["inventory"].keys())
    if not ingredients:
        st.warning("Inventory is empty. Move your lazy ass to Migros!")
        return [], {}

    params = {
        "ingredients": ",".join(ingredients),
        "number": 100,
        "ranking": 2,
        "apiKey": API_KEY
    }
    response = requests.get(SPOONACULAR_URL, params=params)

    if response.status_code == 200:
        recipes = response.json()
        recipe_titles = []
        recipe_links = {}
        random.shuffle(recipes)

        for recipe in recipes:
            missed_ingredients = recipe.get("missedIngredientCount", 0)
            if missed_ingredients <= 2:
                recipe_link = f"https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-')}-{recipe['id']}"
                missed_ingredients_names = [item["name"] for item in recipe.get("missedIngredients", [])]
                recipe_titles.append(recipe['title'])
                recipe_links[recipe['title']] = {
                    "link": recipe_link,
                    "missed_ingredients": missed_ingredients_names
                }
                if len(recipe_titles) >= 3:
                    break
        return recipe_titles, recipe_links
    else:
        st.error("Error fetching recipes. Please check your API key and try again.")
        return [], {}

# Machine Learning Recommendation System
def recommend_recipes(user, all_recipes):
    user_data = st.session_state["user_preferences"].get(user, [])
    if not user_data:
        return random.sample(all_recipes, min(3, len(all_recipes)))

    # Create a simple content-based model using recipe names
    vectorizer = CountVectorizer()
    recipe_matrix = vectorizer.fit_transform([r["Recipe"] for r in user_data] + all_recipes)
    similarity = cosine_similarity(recipe_matrix)

    # Recommend recipes similar to the user's rated recipes
    user_recipe_indices = list(range(len(user_data)))
    similarity_scores = similarity[user_recipe_indices, len(user_data):]
    avg_similarity = similarity_scores.mean(axis=0)
    recommended_indices = avg_similarity.argsort()[::-1][:3]

    return [all_recipes[i] for i in recommended_indices]

# Rating function
def rate_recipe(recipe_title, recipe_link):
    st.subheader(f"Rate the recipe: {recipe_title}")
    st.write(f"**{recipe_title}**: ([View Recipe]({recipe_link}))")
    rating = st.slider("Rate with stars (1-5):", 1, 5, key=f"rating_{recipe_title}")

    if st.button("Submit rating"):
        user = st.session_state["selected_user"]
        if user:
            st.success(f"You have rated '{recipe_title}' with {rating} stars!")
            st.session_state["cooking_history"].append({
                "Person": user,
                "Recipe": recipe_title,
                "Rating": rating,
                "Link": recipe_link,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            if user not in st.session_state["user_preferences"]:
                st.session_state["user_preferences"][user] = []
            st.session_state["user_preferences"][user].append({
                "Recipe": recipe_title,
                "Rating": rating
            })
        else:
            st.warning("Please select a user first.")

# Main application flow
def recipepage():
    st.title("You think you can cook! Better take a recipe!")
    st.subheader("Delulu is not the solulu")
    
    if st.session_state["roommates"]:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_roommate

        st.subheader("Recipe search options")
        search_mode = st.radio("Choose a search mode:", ("Automatic (use all inventory)", "Custom (choose ingredients)"))

        with st.form("recipe_form"):
            if search_mode == "Custom (choose ingredients)":
                selected_ingredients = st.multiselect("Select ingredients from inventory:", st.session_state["inventory"].keys())
            else:
                selected_ingredients = None
            
            search_button = st.form_submit_button("Get recipe suggestions")
            if search_button:
                recipe_titles, recipe_links = get_recipes_from_inventory(selected_ingredients)
                st.session_state["recipe_suggestions"] = recipe_titles
                st.session_state["recipe_links"] = recipe_links

        if st.session_state["recipe_suggestions"]:
            user = st.session_state["selected_user"]
            recommended_recipes = recommend_recipes(user, st.session_state["recipe_suggestions"])

            st.subheader("Choose a recipe to make")
            for title in recommended_recipes:
                link = st.session_state["recipe_links"][title]["link"]
                missed_ingredients = st.session_state["recipe_links"][title]["missed_ingredients"]
                st.write(f"- **{title}**: ([View Recipe]({link}))")
                if missed_ingredients:
                    st.write(f"  *Extra ingredients needed:* {', '.join(missed_ingredients)}")

            selected_recipe = st.selectbox("Select a recipe to cook", ["Please choose..."] + recommended_recipes)
            if selected_recipe != "Please choose...":
                st.session_state["selected_recipe"] = selected_recipe
                st.session_state["selected_recipe_link"] = st.session_state["recipe_links"][selected_recipe]["link"]
                st.success(f"You have chosen to make '{selected_recipe}'!")
    else:
        st.warning("No roommates available.")
        return

    if st.session_state["selected_recipe"] and st.session_state["selected_recipe_link"]:
        rate_recipe(st.session_state["selected_recipe"], st.session_state["selected_recipe_link"])

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

# Run the recipe page
recipepage()
