import os
import streamlit as st
from dotenv import load_dotenv
from auth.rbac import require_page_access

# Load environment variables
load_dotenv(override=True)

# Get auth provider
auth_provider = os.getenv("STREAMLIT_AUTH_PROVIDER", "auth0")

# Check authentication first
require_page_access("views/home.py")

st.title("🛬 App Landing Page")


# Check if user is logged in
if hasattr(st, 'user') and st.user.is_logged_in:
    st.success(f"👋 Welcome back, **{st.user.email}**!")
    with st.expander("👤 User Details"):
        user_dict = st.user.to_dict()
        st.json(user_dict)
else:
    st.markdown("""
    This application [...]

    ### Access Required
    This system requires authentication. Please log in to continue.
    """)