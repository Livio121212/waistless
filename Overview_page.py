import streamlit as st
import pandas as pd
import plotly.express as px  # Using Plotly for enhanced charting

# Initialize session state keys
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
    st.title("Flatmate Overview")

    # Chart 1: Total Expenses by Flatmate (Bar Chart)
    st.subheader("1. Total Expenses by Flatmate")
    expense_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"])
    if not expense_df.empty:
        fig1 = px.bar(expense_df, x="Roommate", y="Total Expenses (CHF)", title="Total Expenses by Flatmate")
        st.plotly_chart(fig1)
    else:
        st.write("No expense data available.")

    # Chart 2: Monthly Purchases by Flatmate (Line Chart)
    st.subheader("2. Monthly Purchases by Flatmate")

    # Step 1: Collect purchase data
    purchases_data = []
    for mate in st.session_state["roommates"]:
        purchases_data.extend([
            {
                "Roommate": mate,
                "Date": purchase.get("Date", "1900-01-01"),  # Fetch date or use default
                "Total": purchase.get("Price", 0)           # Fetch price or use 0
            }
            for purchase in st.session_state["purchases"][mate]
        ])

    # Step 2: Create DataFrame
    purchases_df = pd.DataFrame(purchases_data)

    if not purchases_df.empty:
        # Step 3: Convert Date to datetime and clean up
        purchases_df["Date"] = pd.to_datetime(purchases_df["Date"], format="%Y-%m", errors="coerce")
        purchases_df = purchases_df.dropna(subset=["Date"])  # Drop rows with invalid dates

        # Step 4: Group by Date and Roommate
        monthly_purchases = purchases_df.groupby(["Date", "Roommate"])["Total"].sum().unstack(fill_value=0)

        # Step 5: Reshape for Plotly
        monthly_purchases_long = monthly_purchases.reset_index().melt(
            id_vars=["Date"], 
            var_name="Roommate", 
            value_name="Total Purchases (CHF)"
        )

        # Step 6: Plot
        if not monthly_purchases_long.empty:
            fig2 = px.line(
                monthly_purchases_long,
                x="Date",
                y="Total Purchases (CHF)",
                color="Roommate",
                title="Monthly Purchases by Flatmate",
                labels={"Total Purchases (CHF)": "Total Purchases (CHF)", "Date": "Month"},
                markers=True,  # Add markers for better visibility
            )
            st.plotly_chart(fig2)
        else:
            st.write("No data available for the line chart.")
    else:
        st.write("No purchases data available.")

    # Chart 3: Total Consumption by Flatmate (Pie Chart)
    st.subheader("3. Total Consumption by Flatmate")
    consumption_data = {mate: sum([item["Price"] for item in st.session_state["consumed"][mate]])
                        for mate in st.session_state["roommates"]}
    consumption_df = pd.DataFrame(list(consumption_data.items()), columns=["Roommate", "Total Consumption (CHF)"])
    if not consumption_df.empty:
        fig3 = px.pie(consumption_df, names="Roommate", values="Total Consumption (CHF)",
                      title="Total Consumption by Flatmate", hole=0.3, 
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig3.update_traces(textinfo='percent+label', hoverinfo='label+percent+value')
        st.plotly_chart(fig3)
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
        fig4 = px.bar(inventory_summary.reset_index(), 
                      x="Roommate", y=inventory_summary.columns, 
                      title="Inventory Value by Roommate", 
                      labels={"value": "Price (CHF)", "variable": "Product"}, 
                      barmode="stack")
        st.plotly_chart(fig4)
    else:
        st.write("No inventory data available.")

# Call the function to render the page
overview_page()
