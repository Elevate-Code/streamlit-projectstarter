## Using the debugger with PyCharm

In the **Run/Debug Configuration** window, add a new `Python` configuration with the following settings:
- Confirm that the "Python interpreter" is set to the virtual environment you created and your "Working directory" is correct
- Select `module` from the "Run script or module" dropdown
- Enter `streamlit` in the "Module name" field
- Using the "Modify options" dropdown, select `Add option` > `Parameters`
- Enter `run app.py` in the "Parameters" field

Should now be able to run and run-in-debug the Streamlit app in PyCharm with a single click.

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

# Concurrency with Threading

For I/O-bound tasks like making multiple API calls in parallel, using threads is an effective way to improve performance and responsiveness in a Streamlit app. The recommended approach is to use `concurrent.futures.ThreadPoolExecutor`, which provides a high-level abstraction for managing a pool of worker threads. It is more elegant, concise, and has better exception handling than managing `threading.Thread` objects manually.

While `asyncio` is a modern approach for concurrency, it is complex to integrate with Streamlit. Streamlit runs its own async event loop, and trying to run another one typically results in a `RuntimeError`. Workarounds exist but add complexity, making `ThreadPoolExecutor` a more straightforward and maintainable choice for most use cases.

### The Golden Rule of Threading in Streamlit

**Never call any Streamlit functions from a background thread.** This includes `st.write`, `st.session_state`, `st.experimental_rerun`, or any other `st.*` command. Streamlit's API is not thread-safe and requires a `ScriptRunContext`, which is only available on the main thread.

Worker threads should perform their tasks (e.g., fetching data from an API) and return the results. The main thread can then collect these results and update the UI.

### Example: Parallel API Calls

Here is a practical example of using `ThreadPoolExecutor` to fetch data from multiple APIs concurrently. This pattern uses `st.spinner` to provide feedback to the user, handles exceptions for each thread gracefully, and updates the UI only from the main thread.

```python
import streamlit as st
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def api_call(name, duration):
    """A dummy function that simulates an API call."""
    print(f"Thread for {name}: starting...")
    time.sleep(duration)
    if name == "API B":
        raise ValueError(f"Error in {name}")
    print(f"Thread for {name}: finished.")
    return f"Result from {name}"

if st.button("Run parallel tasks"):
    apis = {"API A": 2, "API B": 1, "API C": 3}
    with st.spinner("Running tasks in parallel..."):
        with ThreadPoolExecutor(max_workers=len(apis)) as executor:
            # Dispatch all tasks and hold their Future objects
            future_to_api = {
                executor.submit(api_call, name, duration): name
                for name, duration in apis.items()
            }

            results = {}
            for future in as_completed(future_to_api):
                name = future_to_api[future]
                try:
                    # .result() blocks until the future is complete
                    # and raises any exception caught in the thread.
                    result = future.result()
                    results[name] = {"status": "success", "data": result}
                except Exception as e:
                    results[name] = {"status": "error", "data": str(e)}

    st.write("### All tasks completed!")
    st.json(results)
```

### Gotchas and Best Practices

- **Race Conditions**: Avoid having threads modify the same shared object. It is safer for each thread to work on its own data and return a result. If you must share data, use thread-safe data structures like `queue.Queue` or `threading.Lock`.
- **Preventing Reruns**: A user might click a button multiple times, potentially dispatching multiple sets of threads. To prevent this, use a session state flag to disable the button while tasks are running.

# Understanding Streamlit Session State

## Order of Execution

On session start (aka. first render), the default widget values are set using the optional `value`, `index` or `key` params.

Then, in response to events:

1. Callback function (on_change, on_click) gets executed first, updating session state.
2. The entire app is executed from top to bottom, updating session state.

## Persistence

values for widgets and vars nested in `if st.button` and

``` python
response = ""

if st.button("Make Request"):
    response = make_api_request() # '{"response": "an API response"}'

# shows the response from the API request, but only after the Make Request button is clicked
st.write(response)

if st.button("Other Button"):
    st.write(response) # will always be empty, because response is not persisted in session state
```


Every widget with a key is automatically added to Session State:

``` python
st.text_input("Your name", value="John Smith")

st.session_state.name # AttributeError: st.session_state has no attribute "name".
```

``` python
st.text_input("Your name", key="name", value="John Smith")

st.session_state.name # John Smith
```

However, widget values are not saved to session state if they are not visible on the page. Their values are deleted if they are not re-rendered in a rerun. This is why navigating to a different page and back will reset the values of widgets to the default values, even if it has a key.

The simplest way to persist a widget value across reruns and re-renders is to save its state to a custom variable.

The only way to intercept a rerun event is in a callback as callbacks are processed before the rerun. In the callback simply copy the widget value by its key into your own session state variable, which acts as a backing store for the widget value.

...



## st.button

Buttons do not retain state. When using `if st.button(): ...` the nested code should only be used for:
- Temporary messages that disappear on subsequent user actions.
- Once-per-click processes that **saves data to session state**, a file, or a database.

See also: [Button behavior and examples > When to use if st.button()](https://docs.streamlit.io/library/advanced-features/button-behavior-and-examples#when-to-use-if-stbutton)



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

## Persist Input Widget Values Across Page Navigation

``` python
import streamlit as st

# Initialize session state with default values on first render only.
if 'some_text' not in st.session_state:
    st.session_state.some_text = "ON RENDER"

# Text input widget whose value persists across reruns and page nav.
some_text = st.text_input(
    label="Persistent text_input",
    value=st.session_state.some_text,
    key='some_text_key',
    on_change=lambda: setattr(st.session_state, 'some_text', st.session_state.some_text_key)
)
st.write(f"You set some_text to: `{some_text}`")
```

For input widgets that have `index` instead of `value` to set the default value you would do something like this:

``` python
my_quality = st.radio(
    # ...
    index=('standard', 'hd').index(st.session_state.quality),
    key='quality_key',
    on_change=lambda: setattr(st.session_state, 'quality', st.session_state.quality_key)
)
```

For `st.text_area()` widgets, to keep the scroll position you cant use `value` param for some reason, so do this:

``` python
# Initialize session state with default values on first render only.
if 'some_text' not in st.session_state:
    st.session_state.some_text = "ON RENDER"
# Set the default value without using `value`
if 'some_text_key' not in st.session_state:
    st.session_state.some_text_key = st.session_state.some_text

# Stable text input widget whose value persists across reruns and page nav.
some_text = st.text_area(
    label="Persistent text_input",
    key='some_text_key',
    on_change=lambda: setattr(st.session_state, 'some_text', st.session_state.some_text_key)
)
st.write(f"You set some_text to: `{some_text}`")
```
