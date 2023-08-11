import streamlit as st
import openai
from dotenv import load_dotenv
import os
load_dotenv()

st.set_page_config(
    page_title="Streamlit OpenAI Completion",
    page_icon="🤖",
    layout="wide" # "centered" constrains page content to a fixed width; "wide" uses the entire screen
)
st.title("🤖 Streamlit OpenAI Chat Completion Demo")

st.info("""
This example app is intended for prompt engineering: one question, one answer, no chat memory.

For a complete chat example, where the context of the chat history (previous question and answers) is 
maintained see this example: https://github.com/dataprofessor/openai-chatbot
""", icon="ℹ️")


system_message = st.text_area('System Prompt', "You are a helpful assistant.")
user_prompt = st.text_area('User Prompt', placeholder="Enter a user message here.")

with st.expander("⚙️ Options", expanded=True):
    model = st.radio("Model", ('gpt-3.5-turbo', 'gpt-4'), index=1, horizontal=True)
    max_tokens = st.number_input("Max Tokens", 500)
    temperature = st.number_input("Temperature", 0.8)


if 'completion_text' not in st.session_state:
    st.session_state['completion_text'] = ""
if st.button("Send ➡️"):
    with st.expander("Assistant Response", expanded=True):
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    stream=True,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        # {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_prompt}
                    ]
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.write(full_response + "▌")
            message_placeholder.write(full_response)
            st.session_state['completion_text'] = message_placeholder