from openai import OpenAI
from dotenv import load_dotenv
import os


openai_client = OpenAI()


def stream_chat_completion(model, messages, temperature=1, max_tokens=2000):
    """
    Makes a request to OpenAI's chat model and streams the response message
    """
    stream = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        content = delta.content
        if content:
            yield content

def get_chat_completion(model, messages, temperature=1, max_tokens=2000):
    """
    Makes a request to OpenAI's chat model and returns the response message
    """
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content