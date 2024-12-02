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
def decode_barcode(image):
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
    
    st.session_state["expenses"][selected_roommate] += price # The expenses of the product are added to the respective expenses of the person
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
        for roommate in st.session_state["purchases"]:  # Äußere Schleife: Iteriert durch die Mitbewohner
            st.write(f"**{roommate}**")  # Display the name of the current roommate in fat letters
            
            purchases = st.session_state["purchases"][roommate]  # Holen der Einkäufe des aktuellen Mitbewohners
            
            if purchases:  # Überprüfen, ob Einkäufe existieren
                data = []  # Temporäre Liste für die Einkäufe
                
                for purchase in purchases:  # Innere Schleife: Iteriert durch die Einkäufe
                    # Daten jedes Einkaufs sammeln
                    data.append([purchase["Product"], purchase["Quantity"], purchase["Price"], purchase["Unit"], purchase["Date"]])
                
                # DataFrame aus den gesammelten Daten erstellen
                purchases_df = pd.DataFrame(data, columns=["Product", "Quantity", "Price", "Unit", "Date"])
                
                # DataFrame als Tabelle anzeigen
                st.table(purchases_df)
            else:
                st.write("No purchases recorded.")  # Nachricht für leere Einkaufslisten

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