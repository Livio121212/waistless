import streamlit as st 
import pandas as pd # Use to display data in table
from PIL import Image # Use for editing images
from pyzbar.pyzbar import decode # Use for decoing barcode
import requests # Use to request data from API
from datetime import datetime  # use to record the date and time

# Initialization of the session status for saving values between interactions
# The following part is unnecessary because it is only used to run and test this page
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {}
if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"]
if "expenses" not in st.session_state:
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}
if "purchases" not in st.session_state:
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]}

# Function to recognize and decode barcode in picture
def barcode_decode(image):
    decoded_objects = decode(image)  # Searching the barcode and save the list of barcodes in the variable
    for obj in decoded_objects:
        return obj.data.decode("utf-8") # Convert a binary number into a string
    return None # Returns non if no barcode was found

# Function to get product information
def get_product_info(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json" # URL refers to the Open Food Facts API
    response = requests.get(url) # Connects to the Open Food Facts API and sends a request
    if response.status_code == 200: # It means that the request was successful and the data is available
        data = response.json() # Converts the response data from JSON into a Python dictionary
        if data.get("status") == 1:  # If status one: Barcode exists in the database, if status 0: Barcode does not exist in the database
            product = data["product"] # Extract product information and return name and brand
            return {
                "name": product.get("product_name", "Unknown Product"), # When no value available default value
                "brand": product.get("brands", "Unknown Brand")
            }
    return None # return None, if barcode does not exist in the database

# Function to add product to inventory
def add_product_to_inventory(food_item, quantity, unit, price, selected_roommate): 
    purchase_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Save the time at which a product is added to the inventory
    if food_item in st.session_state["inventory"]:  # checks if the food is already in the inventory to ensure that no product appears twice by name in the Invenory
        st.session_state["inventory"][food_item]["Quantity"] += quantity # Add the quantity to the existing quantity
        st.session_state["inventory"][food_item]["Price"] += price # Add the price to the existing price
    else:
        st.session_state["inventory"][food_item] = {"Quantity": quantity, "Unit": unit, "Price": price} # If the product is not currently in the inventory, it will be added as a new one and the quantity, unit and price will be adopted
    
    st.session_state["expenses"][selected_roommate] += price # The cost of the product is added to the total expenses of the person
    st.session_state["purchases"][selected_roommate].append({ # the entire purchase is saved in the history
        "Product": food_item,
        "Quantity": quantity,
        "Price": price,
        "Unit": unit,
        "Date": purchase_time
    })
    st.success(f"'{food_item}' has been added to the inventory, and {selected_roommate}'s expenses were updated.") # Displays to the user that the product has been successfully added to the inventory

# Function to show total expenses in a table
def display_total_expenses():
    with st.expander("View Total Expenses per Roommate"): # Function that allows the user to expand or hide the information about expenses
        expenses_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"]) # Generates a list of tuples and assigns column titles
        st.table(expenses_df)  # Show the table

# Function to show purchases per roommate
def display_purchases():
    with st.expander("Purchases per Roommate"):  # Function that allows the user to expand or hide the information about purchases
        for roommate in st.session_state["purchases"]:
            st.write(f"**{roommate}**")  # Display the name of the current roommate in fat letters
            
            purchases = st.session_state["purchases"][roommate]  # Access the list of purchases of the current roommate and save the list in the variable
            
            if purchases:  # Checks if the roommate has already made purchases
                data = []  # Create an empty list to collect the purchases. Required to create a DataFrame later
                
                for purchase in purchases:  # Process each purchase from the roommate individually and extract the data from it
                    data.append([purchase["Product"], purchase["Quantity"], purchase["Price"], purchase["Unit"], purchase["Date"]]) # Extract details of purchase and add them to the data list
                
                purchases_df = pd.DataFrame(data, columns=["Product", "Quantity", "Price", "Unit", "Date"]) # Change the data into a table format and define the columntitle
                st.table(purchases_df) # Display the table
            else:
                st.write("No purchases recorded.")  # Message if there are no purchases

# Main page function
def barcode_page():
    st.title("Upload your barcode") # Define the title of the side
    uploaded_file = st.file_uploader("Upload an image with a barcode", type=["jpg", "jpeg", "png"]) # Function that people can upload files

    if uploaded_file is not None: # Checks if an image has been uploaded
        image = Image.open(uploaded_file)  # Use pillow library to open the image
        st.write("Scanning for barcode...")
        barcode = barcode_decode(image) # Activates the barcode function to scan the image for a barcode

        if barcode: # Check if a barcode was found
            st.write(f"Barcode found: {barcode}")
            st.write("Searching for product information...")
            product_info = get_product_info(barcode) # Calls the previous defined function to get information about the product

            if product_info: # Checks if the search for product information was successful
                
                # Takes product data and displays it as pre-filled entries
                food_item = st.text_input("Product:", value=product_info['name'])
                brand = st.text_input("Brand:", value=product_info['brand']) 
            else:
                # If no data, enter information manually
                st.write("Product not found in database.")
                food_item = st.text_input("Product:")
                brand = st.text_input("Brand:")
            
            # Correct and add information manually
            selected_roommate = st.selectbox("Who bought the product?", st.session_state["roommates"])
            quantity = st.number_input("Quantity:", min_value=0.0, step=0.1, format="%.1f")
            unit = st.selectbox("Unit:", ["Pieces", "Liters", "Grams"])
            price = st.number_input("Price (in CHF):", min_value=0.0, step=0.1, format="%.2f")

            if st.button("Add product to inventory"):
                if food_item and quantity > 0 and price >= 0: # Make sure that all fields have been filled in
                    add_product_to_inventory(food_item, quantity, unit, price, selected_roommate) # Add product to the inventory
                else:
                    st.warning("Please fill in all fields.")
        else:
            st.write("No barcode found in the image.") # Return that no barcode was found on the picture

    display_total_expenses() # Calls previous define function to display the expenses
    display_purchases() # Calls previous define function to display the purchases

# The following part is unnecessary because it is only used to run and test this page
# Run page
barcode_page()