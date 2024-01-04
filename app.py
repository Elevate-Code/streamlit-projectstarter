import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI()

st.set_page_config(
    page_title="Streamlit OpenAI Completion",
    page_icon="🤖",
    layout="wide" # "centered" constrains page content to a fixed width; "wide" uses the entire screen
)

def stream_response(messages, message_placeholder):
    # note that you cant initialize widgets in functions
    response_content = ""
    for response in client.chat.completions.create(
            messages=messages,
            model='gpt-4-1106-preview',
            stream=True,
            max_tokens=2000,
            temperature=1.0
    ):
        content = getattr(response.choices[0].delta, 'content', "")
        response_content += str(content) if content is not None else ""
        message_placeholder.write(response_content + "▌")
    message_placeholder.write(response_content)
    return response_content

st.title("🤖 Streamlit OpenAI Chat Completion Demo")

st.info("""
Streamlit reruns your script from top to bottom every time you interact with your app.

Assigning the current state of the widgets (checkbox, text fields, etc.) to a variable in the process.

Remember that each reruns takes place in a blank slate: no variables are passed between runs.

`st.session_state` is a special variable that persists across reruns of your script.

It is a dictionary that is initialized once when your script is first run, and can be accessed, updated, 
and cleared across reruns.
""", icon="ℹ️")


if "messages" not in st.session_state:
    # Initialize the session state
    st.session_state["messages"] = []

# display previous messages
for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
# create empty position placeholders for new messages
user_placeholder = st.empty()
asst_placeholder = st.empty()

user_prompt = st.text_area("User Prompt")
send_btn_clicked = st.button('Send')
if send_btn_clicked:
    user_placeholder.chat_message("user").write(user_prompt)
    asst_placeholder = asst_placeholder.chat_message("assistant").empty()
    # send msg thread + user msg, stream response and update msg thread
    messages = st.session_state.messages
    messages.append({"role": "user", "content": user_prompt})
    response_content = stream_response(messages, asst_placeholder)
    messages.append({"role": "assistant", "content": response_content})

# clear chat and rerun
clear_btn_clicked = st.button('Clear Chat')
if clear_btn_clicked:
    st.session_state.messages = []
    st.rerun()

st.divider()

st.write("Example of using session state to persist variables across reruns:")
if 'count' not in st.session_state:
    st.session_state.count = 0
plus_one_btn_clicked = st.button('Add +1')
if plus_one_btn_clicked:
    st.session_state.count += 1
st.write('Count = ', st.session_state.count)