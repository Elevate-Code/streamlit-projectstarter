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

# Check for and display RBAC warning if applicable
if st.session_state.get('rbac_using_defaults_due_to_no_persistent_db', False):
    st.warning(
        "**⚠️ RBAC Using Default/Temporary Settings:**\n\n"
        "The `DATABASE_URL` environment variable is not set. "
        "The application is using temporary, non-persistent settings for page access control, "
        "loaded from `get_default_page_access_config()` in `pages.py`.\n\n"
        "Any changes to access rules (e.g., via an admin panel) **will not be saved.**\n\n"
        "To enable persistent storage for Role-Based Access Control, configure `DATABASE_URL` (e.g., for PostgreSQL).",
        icon="💾"
    )

if pages:
    pg = st.navigation(pages)
    pg.run()
else:
    # If no pages are accessible, show a message
    st.warning("No pages are accessible. Please log in to continue.")