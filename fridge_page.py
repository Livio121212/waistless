import streamlit as st
import pandas as pd # Library to handle data
from datetime import datetime

# Initialization of the session status for saving values between interactions
if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"] # use for testing code
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {}
if "expenses" not in st.session_state:
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}
if "purchases" not in st.session_state:
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]}
if "consumed" not in st.session_state:
    st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]}

# Ensure that entries in expenses, purchases and consumption are initialized when adding or removing roommates
def ensure_roommate_entries():
    for mate in st.session_state["roommates"]:
        if mate not in st.session_state["expenses"]:
            st.session_state["expenses"][mate] = 0.0
        if mate not in st.session_state["purchases"]:
            st.session_state["purchases"][mate] = []
        if mate not in st.session_state["consumed"]:
            st.session_state["consumed"][mate] = []

# Function to remove product from inventory
def delete_product_from_inventory(food_item, quantity, unit, selected_roommate):
    ensure_roommate_entries()
    delete_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Records the current time
    if food_item and quantity > 0 and selected_roommate:
        if food_item in st.session_state["inventory"]: # Checks if the ingredient is in the inventory
            current_quantity = st.session_state["inventory"][food_item]["Quantity"]
            current_price = st.session_state["inventory"][food_item]["Price"]
            if quantity <= current_quantity:
                # Calculate the price
                price_per_unit = current_price / current_quantity if current_quantity > 0 else 0
                amount_to_deduct = price_per_unit * quantity
                # Update inventory
                st.session_state["inventory"][food_item]["Quantity"] -= quantity
                st.session_state["inventory"][food_item]["Price"] -= amount_to_deduct
                st.session_state["expenses"][selected_roommate] -= amount_to_deduct
                st.success(f"'{quantity}' of '{food_item}' has been removed.")
                # Report the ingredients in consumed
                st.session_state["consumed"][selected_roommate].append({
                    "Product": food_item,
                    "Quantity": quantity,
                    "Price": amount_to_deduct,
                    "Unit": unit,
                    "Date": delete_time
                })
                # Remove item if quantity reaches zero
                if st.session_state["inventory"][food_item]["Quantity"] <= 0:
                    del st.session_state["inventory"][food_item]
            else:
                st.warning("The quantity to remove exceeds the available quantity.")
        else:
            st.warning("This item is not in the inventory.")
    else:
        st.warning("Please fill in all fields.")

# Function to add product to inventory
def add_product_to_inventory(food_item, quantity, unit, price, selected_roommate):
    ensure_roommate_entries()
    purchase_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if food_item in st.session_state["inventory"]: # Checks if the ingredient is already in the inventory
        st.session_state["inventory"][food_item]["Quantity"] += quantity
        st.session_state["inventory"][food_item]["Price"] += price
    else:
        st.session_state["inventory"][food_item] = {"Quantity": quantity, "Unit": unit, "Price": price}
    
    st.session_state["expenses"][selected_roommate] += price
    st.session_state["purchases"][selected_roommate].append({
        "Product": food_item,
        "Quantity": quantity,
        "Price": price,
        "Unit": unit,
        "Date": purchase_time
    })
    st.success(f"'{food_item}' has been added to the inventory, and {selected_roommate}'s expenses were updated.")

# Main page function
def fridge_page():
    ensure_roommate_entries()
    st.title("Inventory")

    # Roommate selection
    if st.session_state["roommates"]:
        selected_roommate = st.selectbox("Select the roommate:", st.session_state["roommates"])
    else:
        st.warning("No roommates available.")
        return

    # Selection: Add or remove item from inventory
    action = st.selectbox("Would you like to add or remove an item?", ["Add", "Remove"])

    if action == "Add":
        # Input fields for food item, quantity, unit, and price
        food_item = st.text_input("Enter a food item to add:")
        quantity = st.number_input("Quantity:", min_value=0.0)
        unit = st.selectbox("Unit:", ["Pieces", "Liters", "Grams"])
        price = st.number_input("Price (in CHF):", min_value=0.0)
        
        if st.button("Add item"):
            if food_item and quantity > 0 and price >= 0 and selected_roommate:
                add_product_to_inventory(food_item, quantity, unit, price, selected_roommate)
            else:
                st.warning("Please fill in all fields.")
    
    elif action == "Remove":
        if st.session_state["inventory"]:
            # Selection of the food and quantity to be removed
            food_item = st.selectbox("Select a food item to remove:", list(st.session_state["inventory"].keys()))
            quantity = st.number_input("Quantity to remove:", min_value=1.0, step=1.0)
            unit = st.session_state["inventory"][food_item]["Unit"]
            if st.button("Remove item"):
                delete_product_from_inventory(food_item, quantity, unit, selected_roommate)
        else:
            st.warning("The inventory is empty.")

    # Display current inventory
    if st.session_state["inventory"]:
        st.write("Current Inventory:")
        inventory_df = pd.DataFrame.from_dict(st.session_state["inventory"], orient='index') # Creates a DataFrame and sets food items as row labels
        inventory_df = inventory_df.reset_index().rename(columns={'index': 'Food Item'}) # Move food item to the second column and rename the column title
        st.table(inventory_df)
    else:
        st.write("The inventory is empty.")

    # Display total expenses per roommate
    st.write("Total expenses per roommate:")
    expenses_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"]) #Generates a list of tuples and assigns column titles
    st.table(expenses_df)

    # Display purchases and consumed items per roommate
    st.write("Purchases and Consumptions per roommate:")
    for mate in st.session_state["roommates"]:
        st.write(f"{mate}'s Purchases:")
        purchases_df = pd.DataFrame(st.session_state["purchases"][mate])
        st.table(purchases_df)
        
        st.write(f"{mate}'s Consumptions:")
        consumed_df = pd.DataFrame(st.session_state["consumed"][mate])
        st.table(consumed_df)

# Call the function to display the fridge page
fridge_page()
