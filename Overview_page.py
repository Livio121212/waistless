import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import plotly.express as px

# Ensure session state keys are initialized
def ensure_roommate_entries():
    if "roommates" not in st.session_state:
        st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"]  # Example data
    if "expenses" not in st.session_state:
        st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}
    if "purchases" not in st.session_state:
        st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]}
    if "consumed" not in st.session_state:
        st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]}

# Overview page function
def overview_page():
    # Ensure all session state keys exist
    ensure_roommate_entries()

    # Title
    st.title("Flatmate Overview")

    # Chart 1: Total Expenses by Flatmate (Bar Chart)
    st.subheader("1. Total Expenses by Flatmate")
    expense_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"])
    st.bar_chart(expense_df.set_index("Roommate"))

    # Chart 2: Monthly Purchases by Flatmate (Line Chart)
    st.subheader("2. Monthly Purchases by Flatmate")
    purchases_data = []
    for mate in st.session_state["roommates"]:
        purchases_data.extend([
            {"Roommate": mate, "Date": pd.to_datetime(purchase["Date"]).strftime('%Y-%m'), "Total": purchase["Price"]}
            for purchase in st.session_state["purchases"][mate]
        ])
    purchases_df = pd.DataFrame(purchases_data)
    if not purchases_df.empty:
        monthly_purchases = purchases_df.groupby(["Date", "Roommate"])["Total"].sum().unstack(fill_value=0)
        st.line_chart(monthly_purchases)
    else:
        st.write("No purchases data available.")

    # Chart 3: Total Consumption by Flatmate
    st.subheader("3. Total Consumption by Flatmate")
    consumption_data = {mate: sum([item["Price"] for item in st.session_state["consumed"][mate]])
                        for mate in st.session_state["roommates"]}
    consumption_df = pd.DataFrame(list(consumption_data.items()), columns=["Roommate", "Total Consumption (CHF)"])

    if not consumption_df.empty:
        # Use Plotly to create a pie chart
        fig = px.pie(consumption_df, names="Roommate", values="Total Consumption (CHF)",
                    title="Total Consumption by Flatmate", hole=0.3)
        st.plotly_chart(fig)
    else:
        st.write("No consumption data available.")

    # Chart 4: Inventory Summary (Stacked Bar Chart)
    st.subheader("4. Inventory Value by Roommate")
    inventory_data = []
    for mate in st.session_state["roommates"]:
        for purchase in st.session_state["purchases"][mate]:
            inventory_data.append({"Roommate": mate, "Product": purchase["Product"], "Price": purchase["Price"]})
    inventory_df = pd.DataFrame(inventory_data)
    if not inventory_df.empty:
        inventory_summary = inventory_df.groupby(["Roommate", "Product"])["Price"].sum().unstack(fill_value=0)
        st.bar_chart(inventory_summary)
    else:
        st.write("No inventory data available.")

# Call the function to render the page
overview_page()