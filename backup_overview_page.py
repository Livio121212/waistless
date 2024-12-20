import streamlit as st
import pandas as pd
import plotly.express as px

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
    purchases_data = []
    for mate in st.session_state["roommates"]:
        purchases_data.extend([
            {"Roommate": mate, 
             "Date": pd.to_datetime(purchase.get("Date", "1900-01-01")).strftime('%Y-%m'), 
             "Total": purchase.get("Price", 0)}
            for purchase in st.session_state["purchases"][mate]
            if "Date" in purchase and "Price" in purchase
        ])

    purchases_df = pd.DataFrame(purchases_data)

    if not purchases_df.empty:
        purchases_df["Date"] = pd.to_datetime(purchases_df["Date"], format='%Y-%m', errors="coerce")
        purchases_df = purchases_df.sort_values("Date")

        # Group by Date and Roommate, summing prices
        monthly_purchases = purchases_df.groupby(["Date", "Roommate"])["Total"].sum().unstack(fill_value=0)

        # Check if there's any data to plot
        if not monthly_purchases.empty:
            monthly_purchases.reset_index(inplace=True)
            monthly_purchases.set_index('Date', inplace=True)
            fig2 = px.line(monthly_purchases, x=monthly_purchases.index, y=monthly_purchases.columns,
                           title="Monthly Purchases by Flatmate")
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

if __name__ == "__main__":
    # Initialize session state keys when running directly
    if "roommates" not in st.session_state:
        st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"]
    if "expenses" not in st.session_state:
        st.session_state["expenses"] = {mate: 0.0 for mate in st.session_state["roommates"]}
    if "purchases" not in st.session_state:
        st.session_state["purchases"] = {mate: [] for mate in st.session_state["roommates"]}
    if "consumed" not in st.session_state:
        st.session_state["consumed"] = {mate: [] for mate in st.session_state["roommates"]}
    
    overview_page()