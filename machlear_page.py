import streamlit as st
import pandas as pd
import requests
from .waistless.config import API_KEY, SPOONACULAR_URL, CUISINES
from .waistless.utils import is_valid_recipe_title, format_recipe_link, load_cache, save_cache
from .waistless.state_management import initialize_session_state
from .waistless.ml_model import train_model, predict_recipe_score

# Initialize cache
RECIPE_CACHE = load_cache()

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
        params = {
            "ingredients": ",".join(ingredients),
            "number": 10,
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

                # Get cuisine
                cuisines = recipe_details.get("cuisines", [])
                cuisine = cuisines[0] if cuisines else "International"

                # Skip if cuisine doesn't match selection
                if st.session_state["selected_cuisine"] != "Any" and cuisine != st.session_state["selected_cuisine"]:
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

def recipe_page():
    initialize_session_state()
    
    st.title("Smart Recipe Recommendations")
    
    # Display remaining API calls
    st.sidebar.write(f"API Calls Remaining Today: {st.session_state['api_calls_remaining']}")
    
    selected_cuisine = st.selectbox(
        "Select cuisine type:",
        CUISINES,
        index=CUISINES.index(st.session_state["selected_cuisine"])
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