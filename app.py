import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()

st.set_page_config(
    page_title="Counter Example on Streamlit",
    page_icon="⚡",
    layout="centered" # "centered" constrains page content to a fixed width; "wide" uses the entire screen
)

# note that this Streamlit example is setup as a multi-page app
# making this file the "entrypoint file", or the first page the app will show to the user
# pages are easily added by creating .py files in a `pages/` directory relative to your entrypoint file
# to make this a single page app, simply remove the `pages/` directory
# more info: https://docs.streamlit.io/library/get-started/multipage-apps

st.title("⚡Counter Example on Streamlit")

st.header('Without st.session_state 👎')
count = 0
increment = st.button('Increment')
if increment:
    count += 1
st.write('Count = ', count)
st.markdown("""
Streamlit reruns your script from top to bottom every time you interact with your app.

Assigning the current state of the widgets (checkbox, text fields, etc.) to a variable in the process.

However, each reruns takes place in a blank slate: no variables are shared between runs.
""")

st.header('With st.session_state 👍')
if 'count' not in st.session_state:
    st.session_state.count = 0
increment_session_state = st.button('Increment Session State')
if increment_session_state:
    st.session_state.count += 1
reset_count = st.button('Reset Count')
if reset_count:
    st.session_state.count = 0
st.write('Count = ', st.session_state.count)
st.markdown("""
`st.session_state` is a special variable that persists across reruns of your script.

It is a dictionary that is initialized once when your script is first run, and can be accessed, updated, 
and cleared across reruns.
""")