## Using the debugger with PyCharm

In the **Run/Debug Configuration** window, add a new Python configuration with the following settings:
- Confirm that the "Python interpreter" is set to the virtual environment you created and your "Working directory" is correct
- Select `module` from the "Run script or module" dropdown
- Enter `streamlit` in the "Module name" field
- Using the "Modify options" dropdown, select `Add option` > `Parameters`
- Enter `run app.py` in the "Parameters" field

## Using the debugger with VS Code
Create a `.vscode` folder in the root of your project (if it doesn't already exist) and create a `launch.json` file inside of it.

Add the following configuration to your `launch.json` file:

```json
{
"configurations": [
    {
        "name": "Python:Streamlit",
        "type": "python",
        "request": "launch",
        "module": "streamlit",
        "args": [
            "run",
            "${file}"
        ]
    }
 ]
}
```

Once you've updated your launch.json file, you need to navigate to the Run tab on the left gutter of the VS Code app and specify that you want to use this config to debug the app.

# Common Gotchas

`st.button` does not retain state, use caution with what actions are nested inside of it `with st.button('Submit'):`.
See here: https://docs.streamlit.io/library/advanced-features/button-behavior-and-examples#when-to-use-if-stbutton

# Useful Patterns

## Auto Loading And Saving The Content Of `st.text_area` Locally

```python
import streamlit as st

HELLO_TEXT_PATH = "example/hello.txt"

# On first render, load previously saved Hello text_area content from file 
if "ss_hello_text" not in st.session_state:
    with open(HELLO_TEXT_PATH, "r") as file:
        st.session_state.ss_hello_text = file.read()

# Hello text_area, with the users input auto-saved to a file
hello_text = st.text_area(
    "Hello",
     key="ss_hello_text",
     on_change=lambda: open(HELLO_TEXT_PATH, "w").write(st.session_state.ss_hello_text)
)
```
