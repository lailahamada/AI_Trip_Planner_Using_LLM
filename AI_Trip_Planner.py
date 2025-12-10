import os 
import streamlit as st
from groq import Groq
import datetime

# --- 1. Groq API Setup ---
try:
    # Read the API key from Streamlit Secrets.
    # The key must be defined in the Streamlit Cloud secrets configuration (e.g., secrets.toml).
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except KeyError:
    # Error handling if the secret key is missing.
    st.error("Groq API Key not found in Streamlit Secrets. Please configure it securely.")
    st.stop()

# --- 2. Streamlit Page Configuration ---
st.set_page_config(layout="wide")
st.title("AI Travel Planner 🌍")

# --- 3. Initialize chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are an AI travel planner that creates detailed itineraries and responds to follow-up questions and modifications."},
        {"role": "assistant", "content": "Hello! I am your AI Travel Planner. Fill out the form above to create your first itinerary."}
    ]

if "history_titles" not in st.session_state:
    st.session_state.history_titles = []

if "selected_history" not in st.session_state:
    st.session_state.selected_history = None

# --- Callback Functions (Defined at top level) ---

# Callback function to load the selected itinerary from history when a sidebar button is clicked
def select_trip_history(i):
    # Assistant message index = (i * 2) + 3
    assistant_index = (i * 2) + 3
    if assistant_index < len(st.session_state.messages):
        st.session_state.selected_history = st.session_state.messages[assistant_index]["content"]
    else:
        st.session_state.selected_history = "No data available."

# Callback function to clear the selected history view
def clear_selected_history():
    st.session_state.selected_history = None

# --- 4. Sidebar Trip History ---
with st.sidebar:
    st.header("Trip Segments History")
    
    if st.session_state.history_titles:
        for i, title in enumerate(st.session_state.history_titles):
            # Use on_click callback to trigger the history load
            st.button(
                title, 
                key=f"title_{i}",
                on_click=select_trip_history,
                args=(i,) # Pass the index of the trip to the callback function
            )

    if st.button("Clear All History"):
        # Reset history states
        st.session_state.messages = st.session_state.messages[:2]
        st.session_state.history_titles = []
        st.session_state.selected_history = None
        st.rerun() # Rerun is acceptable here as it resets the app state completely


# --- 5. Travel Planning Form ---
with st.form("travel_form"):
    col1, col2 = st.columns(2)

    with col1:
        starting_point = st.text_input("Starting Point (City or Landmark)", placeholder="E.g., New York")
        starting_date = st.date_input("Starting Date", value=datetime.date.today())
        num_travelers = st.number_input("Number of Travelers", min_value=1, value=1)
        budget = st.number_input("Budget", min_value=500)

    with col2:
        destinations = st.text_input("Destination(s), comma-separated", placeholder="E.g., Paris, London, Rome")
        ending_date = st.date_input(
            "Ending Date", 
            value=starting_date + datetime.timedelta(days=1), 
            min_value=starting_date
        )
        currency = st.selectbox("Currency", ["USD","INR","EUR","GBP","JPY","AUD","CAD","CNY"])
        trip_type = st.selectbox("Trip Type", ["Adventure","Leisure","Cultural","Romantic","Family"])

    submit_btn = st.form_submit_button("Get Travel Plan", type="primary")

# --- 6. Generate Travel Plan ---
if submit_btn:
    if not all([starting_point, destinations, starting_date, ending_date, currency, budget, trip_type]):
        st.error("Please fill all the fields")
    else:
        prompt = f"""
Create a detailed daily travel itinerary with the following information:

Starting from: {starting_point}
Destinations to visit: {destinations}
Trip start: {starting_date}
Trip end: {ending_date}
Number of travelers: {num_travelers}
Budget: {budget} {currency}
Travel style: {trip_type}

Provide a day-by-day plan including:
1. Transportation between locations
2. Accommodation suggestions
3. Key attractions each day
4. Estimated costs for main activities
5. Local cuisine recommendations
6. Practical tips
"""

        # Add user prompt
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Add Trip Title to History
        route_title = f"{starting_point} → {destinations} ({starting_date} → {ending_date})"
        st.session_state.history_titles.append(route_title)

        with st.spinner("Generating your AI travel plan..."):
            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=st.session_state.messages
            )
            content = resp.choices[0].message.content

            # Save assistant message
            st.session_state.messages.append({"role": "assistant", "content": content})

            st.success("Itinerary generated successfully!")
            st.markdown(content)


# --- 7. Follow-up Section ---
st.markdown("---")
st.header("Modify or Follow Up on the Plan 💬")

follow_up = st.chat_input("Do you want to modify something?")

if follow_up:
    st.session_state.messages.append({"role": "user", "content": follow_up})

    with st.spinner("Processing..."):
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            # Sending only the last few messages for context (System, Last Assistant, New User)
            messages=st.session_state.messages[-4:] 
            )

        
        content = resp.choices[0].message.content

        st.session_state.messages.append({"role": "assistant", "content": content})

        st.success("Plan updated.")
        st.markdown(content)


# --- 8. Show Selected Trip History ---
if st.session_state.selected_history:
    st.markdown("---")
    st.subheader("Selected Trip Segment")
    st.markdown(st.session_state.selected_history)

    # Use on_click callback
    st.button("Close", on_click=clear_selected_history)