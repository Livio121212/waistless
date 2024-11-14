import streamlit as st
import pandas as pd
from PIL import Image # Use for editing images
from pyzbar.pyzbar import decode # Use for decoing barcode
import requests
from datetime import datetime

# Initialization of the session status for saving values between interactions.
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {}
if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"]
if "expenses" not in st.session_state:
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}
if "purchases" not in st.session_state:
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]}

# Decoding barcodes
def decode_barcode(image):
    decoded_objects = decode(image)  # Searching the barcode
    for obj in decoded_objects:
        return obj.data.decode("utf-8") # Convert a binary number into a string
    return None

# Get product information
def get_product_info(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json" #URL refers to the Open Food Facts API
    response = requests.get(url) 
    if response.status_code == 200: # It means that the request was successful and the data is available
        data = response.json() # Converts the response data from JSON into a Python dictionary
        if data.get("status") == 1: 
            product = data["product"] # Extract product information
            return {
                "name": product.get("product_name", "Unknown Product"), # When no value available default value
                "brand": product.get("brands", "Unknown Brand")
            }
    return None

# add product to inventory
def add_product_to_inventory(food_item, quantity, unit, price, selected_roommate):
    purchase_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if food_item in st.session_state["inventory"]:  # checks if the food is already in the inventory
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

# Show total expenses
def display_total_expenses():
    with st.expander("View Total Expenses per Roommate"):
        expenses_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"]) # Generates a list of tuples and assigns column titles
        st.table(expenses_df)

# show purchases
def display_purchases():
    with st.expander("Purchases per Roommate"):
        for roommate, purchases in st.session_state["purchases"].items():
            st.write(f"**{roommate}**")
            if purchases:
                purchases_df = pd.DataFrame(purchases)
                st.table(purchases_df)
            else:
                st.write("No purchases recorded.")

# Main page function
def barcode_page():
    st.title("Upload your barcode")
    uploaded_file = st.file_uploader("Upload an image with a barcode", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None: # Checks if an image has been uploaded
        image = Image.open(uploaded_file) 
        st.write("Scanning for barcode...")
        barcode = decode_barcode(image)

        if barcode: # Check if a barcode was found
            st.write(f"Barcode found: {barcode}")
            st.write("Searching for product information...")
            product_info = get_product_info(barcode)

            if product_info: 
                # Takes product data and displays it as pre-filled entries.
                food_item = st.text_input("Product:", value=product_info['name'])
                brand = st.text_input("Brand:", value=product_info['brand']) 
            else:
                # If no data, enter information manually.
                st.write("Product not found in database.")
                food_item = st.text_input("Product:")
                brand = st.text_input("Brand:")
            
            # Correct and add information manually
            selected_roommate = st.selectbox("Who bought the product?", st.session_state["roommates"])
            quantity = st.number_input("Quantity:", min_value=0.0, step=0.1, format="%.1f")
            unit = st.selectbox("Unit:", ["Pieces", "Liters", "Grams"])
            price = st.number_input("Price (in CHF):", min_value=0.0, step=0.1, format="%.2f")

            if st.button("Add product to inventory"):
                if food_item and quantity > 0 and price >= 0:
                    add_product_to_inventory(food_item, quantity, unit, price, selected_roommate)
                else:
                    st.warning("Please fill in all fields.")
        else:
            st.write("No barcode found in the image.")

    display_total_expenses()
    display_purchases()

barcode_page()