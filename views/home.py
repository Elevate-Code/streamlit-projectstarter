import streamlit as st

st.success("👈 See various example apps in the sidebar")

st.title("🛬 App Landing Page")

st.info("""
Streamlit reruns your script from top to bottom every time you interact with your app.

Assigning the current state of the widgets (checkbox, text fields, etc.) to a variable in the process.

Remember that each reruns takes place in a blank slate: no variables are passed between runs.

`st.session_state` is a special variable that persists across reruns of your script.

It is a dictionary that is initialized once when your script is first run, and can be accessed, updated,
and cleared across reruns.
""", icon="ℹ️")

st.write("Example of using session state to persist variables across reruns:")

if 'count' not in st.session_state:
    st.session_state.count = 0

plus_one_btn_clicked = st.button('Add +1')

if plus_one_btn_clicked:
    st.session_state.count += 1

st.write('Count = ', st.session_state.count)