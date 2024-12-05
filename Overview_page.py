import streamlit as st # Import Streamlit for creating the web interface
import pandas as pd # Import pandas for data manipulation
import plotly.express as px  # Using Plotly for enhanced charting
from datetime import datetime # Import datetime module to handle date and time

# Initialize session state keys
if "roommates" not in st.session_state:
    # If "roommates" doesn't exist in session state, initialize it with a default list of roommates
    st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"]  # Example data for roommates
if "expenses" not in st.session_state:
    # If "expenses" doesn't exist, create an empty dictionary with a roommate as the key and 0.0 as initial value
    st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}
if "purchases" not in st.session_state:
     # If "purchases" doesn't exist, create an empty list for each roommate to store purchases
    st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]}
if "consumed" not in st.session_state:
     # If "consumed" doesn't exist, create an empty list for each roommate to store consumed items
    st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]}


# Overview page function that generates the main content for the page
def overview_page():
    st.title("Flatmate Overview") # Set the title of the page in Streamlit

    # Chart 1: Total Expenses by Flatmate (Bar Chart)
    st.subheader("1. Total Expenses by Flatmate")
    # Convert the "expenses" dictionary into a DataFrame for plotting
    expense_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"])
    if not expense_df.empty:
        # If there's expense data, create a bar chart to show total expenses per roommate
        fig1 = px.bar(expense_df, x="Roommate", y="Total Expenses (CHF)", title="Total Expenses by Flatmate")
        # Display the plot in the Streamlit app
        st.plotly_chart(fig1)
    else:
        st.write("No expense data available.") # Warning message


    # Chart 2: Monthly Purchases by Flatmate (Line Chart)
    st.subheader("2. Monthly Purchases by Flatmate")

    # Step 1: Collect purchase data
    purchases_data = [] # Initialize an empty list to store purchases data
    for mate in st.session_state["roommates"]: # Loop through each roommate
        purchases_data.extend([ # Add each purchase data to the list
            {
                "Roommate": mate,
                "Date": purchase.get("Date", "1900-01-01"),  # Fetch date or use default
                "Total": purchase.get("Price", 0)           # Fetch price or use 0
            }
            for purchase in st.session_state["purchases"][mate] # Loop through each roommate's purchases
        ])

    # Step 2: Create DataFrame
    purchases_df = pd.DataFrame(purchases_data) # Convert the purchases data into a DataFrame

    if not purchases_df.empty: # Check if the DataFrame is not empty 
        # Step 3: Convert Date to datetime
        purchases_df["Date"] = pd.to_datetime(purchases_df["Date"], errors="coerce")  # Coerce invalid dates to NaT 

        # Step 4: Filter for the current month and year
        current_month = datetime.now().month # Get the current month from the system date
        current_year = datetime.now().year # Get the current year from the system date
        purchases_df = purchases_df[ # Filter only purchases from the current month and year
            (purchases_df["Date"].dt.month == current_month) & 
            (purchases_df["Date"].dt.year == current_year)
        ]

        # Step 5: Group by Day (Date) and Roommate
        daily_purchases = purchases_df.groupby([purchases_df["Date"].dt.date, "Roommate"])["Total"].sum().unstack(fill_value=0)

        # Step 6: Reshape for Plotly 
        daily_purchases_long = daily_purchases.reset_index().melt( # Convert data into long format for Plotly
            id_vars=["Date"], 
            var_name="Roommate", 
            value_name="Total Purchases (CHF)"
        )

        # Step 7: Plot
        if not daily_purchases_long.empty:
            fig2 = px.line( # Create a line chart using Plotly
                daily_purchases_long,
                x="Date",
                y="Total Purchases (CHF)",
                color="Roommate",
                title=f"Daily Purchases by Flatmate - {datetime.now().strftime('%B %Y')}",
                markers=True,  # Add markers for better visibility
            )
            st.plotly_chart(fig2) # Display the plot in the Streamlit app
        else:
            st.write("No data available for the current month.") # Warning message
    else:
        st.write("No purchases data available.") # Warning message




    # Chart 3: Total Consumption by Flatmate (Pie Chart)
    st.subheader("3. Total Consumption by Flatmate")
    # Calculate total consumption for each roommate by summing the prices of consumed items
    consumption_data = {mate: sum([item["Price"] for item in st.session_state["consumed"][mate]])
                        for mate in st.session_state["roommates"]}
    consumption_df = pd.DataFrame(list(consumption_data.items()), columns=["Roommate", "Total Consumption (CHF)"])
    if not consumption_df.empty: # If there's consumption data available
        fig3 = px.pie(consumption_df, names="Roommate", values="Total Consumption (CHF)",
                      title="Total Consumption by Flatmate", hole=0.3, # Create a pie chart with a hole in the center
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig3.update_traces(textinfo='percent+label', hoverinfo='label+percent+value') # Update hover text to show percentage and value
        st.plotly_chart(fig3) # Display the pie chart in the Streamlit app
    else:
        st.write("No consumption data available.") # Warning message

    # Chart 4: Inventory Summary (Stacked Bar Chart)
    st.subheader("4. Inventory Value by Roommate")
    inventory_data = [] # Initialize an empty list to store inventory data
    for mate in st.session_state["roommates"]: # Loop through each roommate
        for purchase in st.session_state["purchases"][mate]: # Loop through each of their purchases
            inventory_data.append({"Roommate": mate, "Product": purchase["Product"], "Price": purchase["Price"]})
    inventory_df = pd.DataFrame(inventory_data) # Convert the inventory data into a DataFrame
    if not inventory_df.empty: # If the inventory DataFrame is not empty
        inventory_summary = inventory_df.groupby(["Roommate", "Product"])["Price"].sum().unstack(fill_value=0)
        # Group inventory data by roommate and product, summing the prices for each product
        fig4 = px.bar(inventory_summary.reset_index(), # Create a stacked bar chart
                      x="Roommate", y=inventory_summary.columns, 
                      title="Inventory Value by Roommate", 
                      labels={"value": "Price (CHF)", "variable": "Product"}, 
                      barmode="stack") # Use stacked bars to show product values
        st.plotly_chart(fig4) # Display the bar chart in the Streamlit app
    else:
        st.write("No inventory data available.") # Warning message

# Call the function to render the page
overview_page()
