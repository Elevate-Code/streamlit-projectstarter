## Running & Developing the Project Locally

### .env file
Duplicate and rename the `.env.example` file to `.env` adding your own values.

### Initial Setup
Requires Python 3.8 or higher
- On this GitHub repo page above the file list, click `Use this template` > `Create a new repository`
- Create a virtual environment using `python -m venv venv`
- Run `venv\Scripts\activate` to activate the virtual environment
- Run `pip install -r requirements.txt` to install all dependencies
- Run `streamlit run app.py` to start the server