import os

import streamlit as st
from dotenv import load_dotenv

from auth.rbac import create_navigation_pages
from auth.auth import render_auth_sidebar
from pages import ALL_PAGES

# Load environment variables
load_dotenv(override=True)

# Constants
# SOME_FILE_PATH = "hello.txt"

st.set_page_config(
    page_icon="🛬", # use same icon for all pages
    page_title="My Streamlit App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Always render auth sidebar to ensure login/logout UI is available
render_auth_sidebar()

# Create navigation with only pages the current user can access.
pages = create_navigation_pages(ALL_PAGES)

if pages:
    pg = st.navigation(pages)
    pg.run()
else:
    # If no pages are accessible, show a message
    st.warning("No pages are accessible. Please log in to continue.")