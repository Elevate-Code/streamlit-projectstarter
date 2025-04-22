import os

import streamlit as st
from dotenv import load_dotenv

from components.auth import check_auth

# Load environment variables
load_dotenv()

# Constants
# SOME_FILE_PATH = "hello.txt"

# Check authentication first (optional, see `auth.py`) - will stop execution if not authenticated
check_auth()

st.title("🔒 Authenticated")

st.write("You are authenticated and can see this page")