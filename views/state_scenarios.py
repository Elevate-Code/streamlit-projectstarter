import time
import streamlit as st

from auth.rbac import require_page_access

# Check authentication first
require_page_access("views/state_scenarios.py")

def stream_data():
    LOREM_IPSUM = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
    incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
    nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
    """
    for word in LOREM_IPSUM.split():
        yield word + " "
        time.sleep(0.02)

st.title("🗃️ Streamlit Session State Examples")

st.write("""
Scenario where I want to make a request and receive a stream of data from a server. I also want the option to be able to click a button and edit the data in place.
""")

stream_btn = st.button("Stream Data")
editable_response_placeholder = st.empty()
if stream_btn:
    response = editable_response_placeholder.write_stream(stream_data())
    st.session_state["data"] = response

editable_response_placeholder.text_area(
    "Data",
    key='data'
)
st.button("Rerun")