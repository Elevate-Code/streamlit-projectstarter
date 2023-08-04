import streamlit as st

st.title('Counter Example')

st.header('Without st.session_state 👎')
st.write('Streamlit reruns your script from top to bottom every time you interact with your app.')
st.write('Each reruns takes place in a blank slate: no variables are shared between runs.')

count = 0
increment = st.button('Increment')
if increment:
    count += 1
st.write('Count = ', count)

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