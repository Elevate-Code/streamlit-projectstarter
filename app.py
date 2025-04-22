import os

import streamlit as st
from dotenv import load_dotenv

from components.auth import check_auth, render_user_info

# Load environment variables
load_dotenv()

# Constants
# SOME_FILE_PATH = "hello.txt"

st.set_page_config(
    page_title="Streamlit Landing Page App",
    page_icon="🛬",
    layout="wide" # "centered" constrains page content to a fixed width; "wide" uses the entire screen
)

# Check authentication first (optional, see `auth.py`) - will stop execution if not authenticated
# check_auth()

# Define navigation using st.Page
home = st.Page("views/home.py", title="Home", icon="🏠", default=True)
state_scenarios = st.Page("views/state_scenarios.py", title="State Scenarios", icon="🔁")
authenticated = st.Page("views/authenticated.py", title="Authenticated", icon="🔒")

# Set up the navigation
pg = st.navigation([home, state_scenarios, authenticated])

# render user info AFTER navigation setup
render_user_info()

# Run the selected page
pg.run()