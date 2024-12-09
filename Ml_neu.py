import streamlit as st

st.title("Debugging Streamlit App")
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.write("User not logged in. Please log in.")
else:
    st.write("User logged in.")
