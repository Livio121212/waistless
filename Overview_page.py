import streamlit as st
import pandas as pd
import plotly.express as px

def ensure_roommate_entries():
    for mate in st.session_state["roommates"]:
        if mate not in st.session_state["expenses"]:
            st.session_state["expenses"][mate] = 0.0
        if mate not in st.session_state["purchases"]:
            st.session_state["purchases"][mate] = []
        if mate not in st.session_state["consumed"]:
            st.session_state["consumed"][mate] = []

# Main overview function
def overview_page():
    st.title("Flatmate Overview")

    ensure_roommate_entries()

    # Monthly Expenses Chart
    st.subheader("Total Expenses by Flatmate")
    expense_df = pd.DataFrame(list(st.session_state["expenses"].items()), columns=["Roommate", "Total Expenses (CHF)"])
    st.bar_chart(expense_df.set_index("Roommate"))

    # Purchases by Roommate
    st.subheader("Purchases Breakdown")
    purchase_data = []
    for mate, purchases in st.session_state["purchases"].items():
        for purchase in purchases:
            purchase["Roommate"] = mate
            purchase_data.append(purchase)

    if purchase_data:
        purchase_df = pd.DataFrame(purchase_data)
        fig = px.bar(purchase_df, x="Roommate", y="Price", color="Product", title="Purchases by Product")
        st.plotly_chart(fig)
    else:
        st.write("No purchase data available.")

    # Consumption Trends
    st.subheader("Consumption Trends Over Time")
    consumption_data = []
    for mate, consumptions in st.session_state["consumed"].items():
        for consumption in consumptions:
            consumption["Roommate"] = mate
            consumption_data.append(consumption)

    if consumption_data:
        consumption_df = pd.DataFrame(consumption_data)
        consumption_df["Date"] = pd.to_datetime(consumption_df["Date"])
        fig = px.line(consumption_df, x="Date", y="Price", color="Roommate", title="Consumption Trends Over Time")
        st.plotly_chart(fig)
    else:
        st.write("No consumption data available.")

# Call the function if running standalone (for testing)
if __name__ == "__main__":
    overview_page()