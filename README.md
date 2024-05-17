## 🚨 Delete this top section after cloning 🚨

To get started with this template, follow all these steps:

1. On this GitHub repo page, in the top right corner above files, click the **Use this template** > **Create a new repo** button.
2. OR use `git clone https://github.com/Ecom-Analytics-Co/streamlit-projectstarter.git yourprojectname` to clone this repo to your local machine.
3. Edit the `requirements.txt` file to match the dependencies you need for your project.
4. Check out the [streamlit_tips.md](streamlit_tips.md) file for how to use the debugger with VS Code or PyCharm and other tips.
5. Run `python start_project.py` to create template .env files, then delete this script file as it is no longer needed.
6. ⚠️ Remove this entire section from your README.md file once you've cloned the repository and are ready to proceed with your project.

<details>
<summary>
<b>🔽 Click to expand the steps for cloning and customizing the project</b>
</summary>
  
1. Clone the repository with a different name:
   ```
   git clone https://github.com/Elevate-Code/streamlit-projectstarter.git streamlit-new-project
   ```

2. Change into the cloned repository's directory:
   ```
   cd streamlit-new-project
   ```
   
3. ⚠️ Remove the remote connection to the original repository:
   ```
   git remote remove origin
   ```

   This step decouples `streamlit-new-project` from `streamlit-projectstarter` by removing the remote connection to the original repository.

4. Make the desired changes to get your project to its initial stage, such as deleting certain files and revising others.

5. Clear the git history and create a new initial commit:
   ```
   git checkout --orphan latest_branch
   git add -A
   git commit -am "Initial commit"
   git branch -D master
   git branch -m master
   ```
   This sequence of commands creates a new branch without any history, adds all the files, creates a new initial commit, deletes the old branch, and renames the new branch to "master".

6. Create a new private repository on your personal GitHub account. You can do this by visiting `https://github.com/new` and filling in the repository details. Make sure to set the visibility to "Private".

   (Optional) If you want to publish the repository under an organization account, create the new private repository on the organization's page instead.
   
   You can create the repository by visiting `https://github.com/organizations/{your-org-name}/repositories/new`.

8. Set the remote URL of your local repository to point to the new private repository:
   ```
   git remote add origin https://github.com/{path-copied-from-new-repo}.git
   ```

9. Push your local changes to the new private repository:
   ```
   git push -u origin master
   ```

   This will push your local changes to the new private repository under your personal account or the specified organization account.
</details>

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
