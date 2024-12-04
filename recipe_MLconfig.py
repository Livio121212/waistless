# API configuration
API_KEY = 'a79012e4b3e1431e812d8b17bee3a4d7'
SPOONACULAR_URL = 'https://api.spoonacular.com/recipes/findByIngredients'

# Available cuisines
CUISINES = ["Italian", "Asian", "Mexican", "Mediterranean", "American", "International"]

# Taste features
TASTE_FEATURES = ["Spicy", "Sweet", "Salty", "Sour", "Bitter", "Umami"]

# Cache duration in hours
CACHE_DURATION = 24

# Backup recipes for when API is unavailable
BACKUP_RECIPES = {
    "Simple Pasta": {
        "id": 1,
        "title": "Simple Pasta",
        "link": "https://example.com/simple-pasta",
        "cuisine": "Italian",
        "missed_ingredients": ["pasta", "tomato sauce"],
        "instructions": "Cook pasta, add sauce"
    },
    "Basic Stir Fry": {
        "id": 2,
        "title": "Basic Stir Fry",
        "link": "https://example.com/stir-fry",
        "cuisine": "Asian",
        "missed_ingredients": ["vegetables", "soy sauce"],
        "instructions": "Stir fry vegetables with sauce"
    },
    "Quick Salad": {
        "id": 3,
        "title": "Quick Salad",
        "link": "https://example.com/salad",
        "cuisine": "International",
        "missed_ingredients": ["lettuce", "dressing"],
        "instructions": "Mix ingredients, add dressing"
    },
    "Spaghetti Carbonara": {
        "id": 4,
        "title": "Spaghetti Carbonara",
        "link": "https://example.com/carbonara",
        "cuisine": "Italian",
        "missed_ingredients": ["spaghetti", "eggs", "pecorino cheese", "guanciale"],
        "instructions": "Cook pasta, mix with egg and cheese sauce"
    },
    "Chicken Curry": {
        "id": 5,
        "title": "Chicken Curry",
        "link": "https://example.com/curry",
        "cuisine": "Asian",
        "missed_ingredients": ["chicken", "curry paste", "coconut milk"],
        "instructions": "Cook chicken with curry paste and coconut milk"
    },
    "Beef Tacos": {
        "id": 6,
        "title": "Beef Tacos",
        "link": "https://example.com/tacos",
        "cuisine": "Mexican",
        "missed_ingredients": ["ground beef", "taco shells", "lettuce", "cheese"],
        "instructions": "Cook beef, assemble tacos"
    },
    "Greek Salad": {
        "id": 7,
        "title": "Greek Salad",
        "link": "https://example.com/greek-salad",
        "cuisine": "Mediterranean",
        "missed_ingredients": ["feta cheese", "olives", "cucumber", "tomatoes"],
        "instructions": "Chop vegetables, mix with olive oil"
    },
    "Hamburger": {
        "id": 8,
        "title": "Hamburger",
        "link": "https://example.com/hamburger",
        "cuisine": "American",
        "missed_ingredients": ["ground beef", "buns", "lettuce", "tomato"],
        "instructions": "Form patties, grill, assemble burger"
    },
    "Pizza Margherita": {
        "id": 9,
        "title": "Pizza Margherita",
        "link": "https://example.com/pizza",
        "cuisine": "Italian",
        "missed_ingredients": ["pizza dough", "mozzarella", "tomato sauce", "basil"],
        "instructions": "Roll dough, add toppings, bake"
    },
    "Pad Thai": {
        "id": 10,
        "title": "Pad Thai",
        "link": "https://example.com/pad-thai",
        "cuisine": "Asian",
        "missed_ingredients": ["rice noodles", "tofu", "peanuts", "bean sprouts"],
        "instructions": "Stir-fry noodles with sauce and ingredients"
    },
    "Chicken Fajitas": {
        "id": 11,
        "title": "Chicken Fajitas",
        "link": "https://example.com/fajitas",
        "cuisine": "Mexican",
        "missed_ingredients": ["chicken", "bell peppers", "tortillas", "onions"],
        "instructions": "Grill chicken and vegetables, serve with tortillas"
    },
    "Hummus": {
        "id": 12,
        "title": "Hummus",
        "link": "https://example.com/hummus",
        "cuisine": "Mediterranean",
        "missed_ingredients": ["chickpeas", "tahini", "lemon", "garlic"],
        "instructions": "Blend all ingredients until smooth"
    },
    "Mac and Cheese": {
        "id": 13,
        "title": "Mac and Cheese",
        "link": "https://example.com/mac-cheese",
        "cuisine": "American",
        "missed_ingredients": ["macaroni", "cheddar cheese", "milk", "butter"],
        "instructions": "Cook pasta, make cheese sauce, combine"
    },
    "Risotto": {
        "id": 14,
        "title": "Risotto",
        "link": "https://example.com/risotto",
        "cuisine": "Italian",
        "missed_ingredients": ["arborio rice", "parmesan", "white wine", "stock"],
        "instructions": "Gradually add stock to rice, stir until creamy"
    },
    "Sushi Roll": {
        "id": 15,
        "title": "Sushi Roll",
        "link": "https://example.com/sushi",
        "cuisine": "Asian",
        "missed_ingredients": ["sushi rice", "nori", "fish", "cucumber"],
        "instructions": "Roll ingredients in nori sheet"
    },
    "Enchiladas": {
        "id": 16,
        "title": "Enchiladas",
        "link": "https://example.com/enchiladas",
        "cuisine": "Mexican",
        "missed_ingredients": ["tortillas", "chicken", "enchilada sauce", "cheese"],
        "instructions": "Fill tortillas, cover with sauce and cheese, bake"
    },
    "Falafel": {
        "id": 17,
        "title": "Falafel",
        "link": "https://example.com/falafel",
        "cuisine": "Mediterranean",
        "missed_ingredients": ["chickpeas", "herbs", "spices", "oil"],
        "instructions": "Form chickpea mixture into balls, fry"
    },
    "BBQ Ribs": {
        "id": 18,
        "title": "BBQ Ribs",
        "link": "https://example.com/ribs",
        "cuisine": "American",
        "missed_ingredients": ["pork ribs", "BBQ sauce", "spices"],
        "instructions": "Season ribs, slow cook, brush with sauce"
    },
    "Lasagna": {
        "id": 19,
        "title": "Lasagna",
        "link": "https://example.com/lasagna",
        "cuisine": "Italian",
        "missed_ingredients": ["lasagna noodles", "ground beef", "ricotta", "tomato sauce"],
        "instructions": "Layer noodles with sauce and cheese, bake"
    },
    "Fried Rice": {
        "id": 20,
        "title": "Fried Rice",
        "link": "https://example.com/fried-rice",
        "cuisine": "Asian",
        "missed_ingredients": ["rice", "eggs", "vegetables", "soy sauce"],
        "instructions": "Stir-fry rice with vegetables and eggs"
    },
    "Quesadillas": {
        "id": 21,
        "title": "Quesadillas",
        "link": "https://example.com/quesadillas",
        "cuisine": "Mexican",
        "missed_ingredients": ["tortillas", "cheese", "chicken", "vegetables"],
        "instructions": "Fill tortillas with ingredients, grill until crispy"
    },
    "Tabbouleh": {
        "id": 22,
        "title": "Tabbouleh",
        "link": "https://example.com/tabbouleh",
        "cuisine": "Mediterranean",
        "missed_ingredients": ["bulgur", "parsley", "tomatoes", "lemon"],
        "instructions": "Mix bulgur with chopped herbs and vegetables"
    },
    "Chicken Wings": {
        "id": 23,
        "title": "Chicken Wings",
        "link": "https://example.com/wings",
        "cuisine": "American",
        "missed_ingredients": ["chicken wings", "hot sauce", "butter"],
        "instructions": "Bake wings, toss in sauce"
    },
    "Pesto Pasta": {
        "id": 24,
        "title": "Pesto Pasta",
        "link": "https://example.com/pesto-pasta",
        "cuisine": "Italian",
        "missed_ingredients": ["pasta", "basil", "pine nuts", "parmesan"],
        "instructions": "Make pesto, mix with cooked pasta"
    },
    "Spring Rolls": {
        "id": 25,
        "title": "Spring Rolls",
        "link": "https://example.com/spring-rolls",
        "cuisine": "Asian",
        "missed_ingredients": ["rice paper", "vegetables", "shrimp", "herbs"],
        "instructions": "Fill and roll rice paper with ingredients"
    },
    "Guacamole": {
        "id": 26,
        "title": "Guacamole",
        "link": "https://example.com/guacamole",
        "cuisine": "Mexican",
        "missed_ingredients": ["avocados", "lime", "tomato", "onion"],
        "instructions": "Mash avocados, mix with ingredients"
    },
    "Shakshuka": {
        "id": 27,
        "title": "Shakshuka",
        "link": "https://example.com/shakshuka",
        "cuisine": "Mediterranean",
        "missed_ingredients": ["eggs", "tomatoes", "peppers", "spices"],
        "instructions": "Cook eggs in spiced tomato sauce"
    },
    "Clam Chowder": {
        "id": 28,
        "title": "Clam Chowder",
        "link": "https://example.com/chowder",
        "cuisine": "American",
        "missed_ingredients": ["clams", "potatoes", "cream", "bacon"],
        "instructions": "Make creamy soup with clams and vegetables"
    },
    "Minestrone Soup": {
        "id": 29,
        "title": "Minestrone Soup",
        "link": "https://example.com/minestrone",
        "cuisine": "Italian",
        "missed_ingredients": ["vegetables", "pasta", "beans", "broth"],
        "instructions": "Simmer vegetables and pasta in broth"
    },
    "Ramen": {
        "id": 30,
        "title": "Ramen",
        "link": "https://example.com/ramen",
        "cuisine": "Asian",
        "missed_ingredients": ["noodles", "broth", "egg", "pork"],
        "instructions": "Prepare broth, cook noodles, add toppings"
    },
    "Chicken Mole": {
        "id": 31,
        "title": "Chicken Mole",
        "link": "https://example.com/mole",
        "cuisine": "Mexican",
        "missed_ingredients": ["chicken", "mole sauce", "chocolate", "spices"],
        "instructions": "Cook chicken in rich mole sauce"
    },
    "Moussaka": {
        "id": 32,
        "title": "Moussaka",
        "link": "https://example.com/moussaka",
        "cuisine": "Mediterranean",
        "missed_ingredients": ["eggplant", "ground lamb", "bechamel", "tomatoes"],
        "instructions": "Layer eggplant with meat and sauce, bake"
    },
    "Meatloaf": {
        "id": 33,
        "title": "Meatloaf",
        "link": "https://example.com/meatloaf",
        "cuisine": "American",
        "missed_ingredients": ["ground beef", "breadcrumbs", "onion", "ketchup"],
        "instructions": "Mix ingredients, form loaf, bake"
    },
    "Gnocchi": {
        "id": 34,
        "title": "Gnocchi",
        "link": "https://example.com/gnocchi",
        "cuisine": "Italian",
        "missed_ingredients": ["potatoes", "flour", "egg", "sauce"],
        "instructions": "Make potato dumplings, cook in sauce"
    },
    "Beef and Broccoli": {
        "id": 35,
        "title": "Beef and Broccoli",
        "link": "https://example.com/beef-broccoli",
        "cuisine": "Asian",
        "missed_ingredients": ["beef", "broccoli", "soy sauce", "garlic"],
        "instructions": "Stir-fry beef and broccoli with sauce"
    },
    "Chiles Rellenos": {
        "id": 36,
        "title": "Chiles Rellenos",
        "link": "https://example.com/chiles-rellenos",
        "cuisine": "Mexican",
        "missed_ingredients": ["poblano peppers", "cheese", "eggs", "sauce"],
        "instructions": "Stuff peppers with cheese, batter and fry"
    },
    "Spanakopita": {
        "id": 37,
        "title": "Spanakopita",
        "link": "https://example.com/spanakopita",
        "cuisine": "Mediterranean",
        "missed_ingredients": ["spinach", "feta", "phyllo dough", "herbs"],
        "instructions": "Layer phyllo with spinach-feta mixture"
    },
    "Chicken Pot Pie": {
        "id": 38,
        "title": "Chicken Pot Pie",
        "link": "https://example.com/pot-pie",
        "cuisine": "American",
        "missed_ingredients": ["chicken", "vegetables", "pie crust", "cream"],
        "instructions": "Make filling, cover with crust, bake"
    },
    "Tiramisu": {
        "id": 39,
        "title": "Tiramisu",
        "link": "https://example.com/tiramisu",
        "cuisine": "Italian",
        "missed_ingredients": ["ladyfingers", "mascarpone", "coffee", "cocoa"],
        "instructions": "Layer coffee-dipped cookies with cream"
    },
    "Dumplings": {
        "id": 40,
        "title": "Dumplings",
        "link": "https://example.com/dumplings",
        "cuisine": "Asian",
        "missed_ingredients": ["wonton wrappers", "ground pork", "cabbage", "ginger"],
        "instructions": "Fill wrappers with mixture, steam or fry"
    },
    "Fish Tacos": {
        "id": 41,
        "title": "Fish Tacos",
        "link": "https://example.com/fish-tacos",
        "cuisine": "Mexican",
        "missed_ingredients": ["white fish", "tortillas", "slaw", "lime"],
        "instructions": "Cook fish, assemble tacos with toppings"
    },
    "Baklava": {
        "id": 42,
        "title": "Baklava",
        "link": "https://example.com/baklava",
        "cuisine": "Mediterranean",
        "missed_ingredients": ["phyllo dough", "nuts", "honey", "spices"],
        "instructions": "Layer phyllo with nuts, bake, add syrup"
    },
    "Apple Pie": {
        "id": 43,
        "title": "Apple Pie",
        "link": "https://example.com/apple-pie",
        "cuisine": "American",
        "missed_ingredients": ["apples", "pie crust", "cinnamon", "sugar"],
        "instructions": "Make filling, assemble pie, bake"
    }
}