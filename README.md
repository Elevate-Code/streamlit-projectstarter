## 🚨 Delete this top section after cloning 🚨

To get started with this template, follow all these steps:

1. On this GitHub repo page, in the top right corner above files, click the **Use this template** > **Create a new repo** button.
2. OR use `git clone https://github.com/Ecom-Analytics-Co/streamlit-projectstarter.git yourprojectname` to clone this repo to your local machine.
3. Edit the `requirements.txt` file to match the dependencies you need for your project.
4. Check out the [streamlit_tips.md](streamlit_tips.md) file for how to use the debugger with VS Code or PyCharm and other tips.
5. Run `python start_project.py` to create template .env files, then delete this script file as it is no longer needed.
6. ⚠️ Remove this entire section from your README.md file once you've cloned the repository and are ready to proceed with your project.

### Optional: Basic Authentication with `auth.py`

`auth.py` is provided for basic username-password authentication for a limited number of users. It's modular and can be removed if not needed.

1. Add user credentials to `.env` file in the format: `username='password'`
2. Add this code to the top of `app.py` and all other pages requiring authentication:
   ```python
   from auth import check_password
   if not check_password():
       st.stop()
    ```

**🚨 Delete this top section after cloning 🚨**

---

## Running & Developing the Project Locally

### .env file
Duplicate and rename the `.env.example` file to `.env` adding your own values.

### Initial Setup
Requires Python 3.8 or higher
- Create a virtual env using `python -m venv venv` or `python3.8 -m venv venv`
- Run `venv\Scripts\activate` to activate the virtual environment
- Run `pip install -r requirements.txt` to install all dependencies
- Run `streamlit run app.py` to start the server

### Subsequent Runs 🚀
- Run `venv\Scripts\activate` to activate the virtual environment
- Run `streamlit run app.py` to start the server
- (optionally) `pip install -r requirements.txt` if you encounter a `ModuleNotFoundError`

## Deploying to Railway.app
- Dashboard > New Project > Deploy from GitHub repo
- If you get a "Invalid service name" error create a blank service and then link the repo under Settings > Source Repo
- If needed, update project name
- Click on the service, under **Variables**:
    - Add `PORT` with value `8501`
- In the service, under **Settings**:
    - Environment > Domains, click `Generate Domain`, this will be the public URL, change if needed
    - Service > Service Name, change to "app" or similar
    - Service > Start Command, enter `streamlit run app.py`
- You should now be able to view the app at the public URL
- For debugging deployment issues, in the service, under **Deployments**:
    - Click on the latest deployment > `View Logs`
    - Check `Build Logs` and `Deploy Logs` for errors
