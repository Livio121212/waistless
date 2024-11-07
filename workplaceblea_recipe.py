import streamlit as st

# intiatlisierung 
if "inventory" not in st.session_state:
    st.session_state["inventory"] = {"Tomato": 5, "Banana,": 3} # Example roommates list
if "roommates" not in st.session_state:
    st.session_state["roommates"] = ["Livio", "Flurin", "Anderin"]  # Example roommates list
if "selected_user" not in st.session_state:
    st.session_state["selected_user"] = None

# Auswahl des aktuellen Mitbewohner
def select_user():
    st.title("Who are you")
    if st.session_state["roommates"]:
        selected_user = st.selectbox("Choose your name:", st.session_state["roommates"])
        st.session_state["selected_user"] = selected_user
        st.write(f"Hi, {selected_user}!")
    else:
        st.warning("No user was added.")

select_user()