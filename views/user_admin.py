import os
import secrets
import requests

import pandas as pd
from dotenv import load_dotenv
import streamlit as st

from auth.rbac import (
    require_page_access,
    load_page_access_config,
    save_page_access_config,
    AVAILABLE_ROLES,
)
from pages import ALL_PAGES


load_dotenv(override=True)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_M2M_CLIENT_ID = os.getenv("AUTH0_M2M_CLIENT_ID")
AUTH0_M2M_CLIENT_SECRET = os.getenv("AUTH0_M2M_CLIENT_SECRET")
AUTH0_DATABASE_CONNECTION_NAME = os.getenv("AUTH0_DATABASE_CONNECTION_NAME")
AUTH0_TEAM_LOGIN_URL = os.getenv("AUTH0_TEAM_LOGIN_URL") # NEW – optional team dashboard URL

# Check authentication first
require_page_access("views/user_admin.py")

# Ensure essential environment variables are set
if not all([AUTH0_DOMAIN, AUTH0_M2M_CLIENT_ID, AUTH0_M2M_CLIENT_SECRET, AUTH0_DATABASE_CONNECTION_NAME]):
    st.error(
        "Missing one or more Auth0 environment variables: "
        "AUTH0_DOMAIN, AUTH0_M2M_CLIENT_ID, AUTH0_M2M_CLIENT_SECRET, AUTH0_DATABASE_CONNECTION_NAME. "
        "Please set them in your environment and ensure this page is protected."
    )
    st.stop()

st.title("Auth0 User Management")
st.caption(f"View users and manage invitations for the **{AUTH0_DATABASE_CONNECTION_NAME}** database connection.")

# --- Helper Functions ---

@st.cache_data(ttl=600, show_spinner=False) # Cache M2M token for 10 minutes
def fetch_m2m_token():
    """Fetches an M2M access token from Auth0."""
    try:
        response = requests.post(
            f'https://{AUTH0_DOMAIN}/oauth/token',
            json={
                "grant_type": "client_credentials",
                "client_id": AUTH0_M2M_CLIENT_ID,
                "client_secret": AUTH0_M2M_CLIENT_SECRET,
                "audience": f'https://{AUTH0_DOMAIN}/api/v2/'
            },
            headers={"content-type": "application/json"}
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if token:
            return token
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching M2M token: {e}")
    return None

def list_auth0_users(access_token):
    """Lists users from Auth0 and displays them in a dataframe."""
    if not access_token:
        st.error("M2M Access Token not available.")
        return False

    st.header("👥 Users")

    if AUTH0_DOMAIN:
        parts = AUTH0_DOMAIN.split('.')
        tenant = parts[0] if parts else ""
        region = parts[1] if len(parts) == 4 else "us"

    st.write(f"For advanced user management tasks, including :orange[**deleting**] users, please use the [Auth0 Dashboard ↗️](https://manage.auth0.com/dashboard/{region}/{tenant}/users).")

    # Fetch data if needed
    if st.session_state.get("force_user_list_refresh", True):
        try:
            response = requests.get(
                f'https://{AUTH0_DOMAIN}/api/v2/users',
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "per_page": 100,
                    "page": 0,
                    "include_totals": "true",
                    "fields": "email,user_id,name,last_login,logins_count,email_verified,app_metadata,identities",
                    "include_fields": "true",
                    # --- new filters ---
                    "search_engine": "v3",
                    "q": f'identities.connection:"{AUTH0_DATABASE_CONNECTION_NAME}"'
                }
            )
            response.raise_for_status()
            data = response.json()

            # Extract users from response
            if isinstance(data, list):
                users = data
            elif isinstance(data, dict) and 'users' in data:
                users = data['users']
                st.caption(f"Total users: {data.get('total', 'N/A')}")
            else:
                users = []

            st.session_state.auth0_users = users
            st.session_state.force_user_list_refresh = False

        except requests.exceptions.HTTPError as e:
            st.error(f"Error listing users: {e}")
            st.session_state.auth0_users = []
            return False

    # Prepare dataframe
    users_data = []
    for user in st.session_state.get("auth0_users", []):
        roles = user.get('app_metadata', {}).get('roles', [])
        invited = user.get('app_metadata', {}).get('invited', False)
        users_data.append({
            "Name": user.get('name', 'N/A'),
            "Email": user.get('email', 'N/A'),
            "Invited": invited,
            "Verified": user.get('email_verified', False),
            "Roles": ", ".join(roles) if roles else "None",
            "Last Login": user.get('last_login', 'N/A'),
            "Logins Count": user.get('logins_count', 0),
            "User ID": user.get('user_id')
        })

    if users_data:
        st.dataframe(
            users_data,
            use_container_width=True,
            key="user_selection",
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True
        )
    else:
        st.info("No users found.")

    return True

def update_user_roles(access_token, user_id, new_roles):
    """Updates a user's roles in Auth0."""
    try:
        response = requests.patch(
            f'https://{AUTH0_DOMAIN}/api/v2/users/{user_id}',
            json={"app_metadata": {"roles": new_roles}},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()
        st.success("Roles updated successfully.")
        return True
    except requests.exceptions.HTTPError as e:
        st.error(f"Error updating roles: {e}")
        return False

def trigger_password_email(email, connection, client_id):
    """Triggers Auth0 to send a password reset email."""
    try:
        response = requests.post(
            f'https://{AUTH0_DOMAIN}/dbconnections/change_password',
            json={
                "client_id": client_id,
                "email": email,
                "connection": connection
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        st.success("Password setup email sent.")
        return True
    except requests.exceptions.HTTPError as e:
        st.error(f"Error sending password email: {e}")
        return False

def create_user(access_token, email, connection, initial_roles=None):
    """Creates a new user in Auth0."""
    try:
        # Create user
        payload = {
            "email": email,
            "connection": connection,
            "password": secrets.token_urlsafe(48),
            "email_verified": False,
            "verify_email": False
        }

        # Construct app_metadata with "invited" flag and conditional "roles"
        payload["app_metadata"] = {
            "invited": True,
            **({"roles": initial_roles} if initial_roles else {})
        }

        response = requests.post(
            f'https://{AUTH0_DOMAIN}/api/v2/users',
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        response.raise_for_status()

        # Send password setup email
        client_id = os.getenv("STREAMLIT_AUTH_CLIENT_ID")
        if client_id:
            return trigger_password_email(email, connection, client_id)
        else:
            st.warning("User created but password email not sent. Missing STREAMLIT_AUTH_CLIENT_ID.")
            return False

    except requests.exceptions.HTTPError as e:
        st.error(f"Error creating user: {e}")
        if "user already exists" in str(e).lower():
            st.warning(f"User {email} may already exist.")
        return False

# --- Main Page Logic ---

# Initialize session state
if "auth0_users" not in st.session_state:
    st.session_state.auth0_users = []

# Main content
if m2m_token := fetch_m2m_token():

    # User list
    list_auth0_users(m2m_token)

    if st.button("Refresh Users"):
        st.session_state.force_user_list_refresh = True
        if "user_selection" in st.session_state:
            st.session_state.user_selection.selection.rows = []
        st.rerun()

    # Edit roles
    st.subheader("Edit User Roles")

    #TODO: currently the role is not updated user-side until they re-login; need to force logout somehow
    selection = st.session_state.get("user_selection")
    if selection and selection.selection.rows:
        idx = selection.selection.rows[0]
        if idx < len(st.session_state.get("auth0_users", [])):
            user = st.session_state.auth0_users[idx]

            with st.form(f"edit_roles_{user['user_id']}"):
                st.write(f"**{user.get('name', user['email'])}**")

                current_roles = user.get('app_metadata', {}).get('roles', [])
                new_roles = st.multiselect(
                    "Roles",
                    options=AVAILABLE_ROLES,
                    default=current_roles
                )

                if st.form_submit_button("Update Roles"):
                    if update_user_roles(m2m_token, user['user_id'], new_roles):
                        st.session_state.force_user_list_refresh = True
                        st.rerun()
    else:
        st.info("Select a user row in the Users table to edit their roles.")

    # Create new user
    st.subheader("Invite New User")
    st.markdown(f"Create a user in the **{AUTH0_DATABASE_CONNECTION_NAME}** connection and trigger Auth0 to send a password setup email.")


    with st.form("invite_user", clear_on_submit=True):
        email = st.text_input("Email Address")
        roles = st.multiselect("Initial Roles", options=AVAILABLE_ROLES)

        if st.form_submit_button("Create and Invite"):
            if email and AUTH0_DATABASE_CONNECTION_NAME:
                if create_user(m2m_token, email, AUTH0_DATABASE_CONNECTION_NAME, roles):
                    st.session_state.force_user_list_refresh = True
                    st.toast(f"Invitation sent to {email}.", icon="📩")
            elif not email:
                st.warning("Please enter an email address.")
            else:
                st.error("AUTH0_DATABASE_CONNECTION_NAME not configured.")

else:
    st.warning("M2M Access Token could not be fetched. User listing and management are unavailable.")
    st.info("Ensure the M2M application credentials are correctly set in the environment and have the required scopes (e.g., 'read:users', 'create:users', 'update:users_app_metadata').")

# Page Access Management Section (works without M2M token)
st.header("🔒 Page Access Management")
st.markdown("Configure which roles can access each page in the application.")

# Add this decorator to create an isolated fragment for page permissions
@st.fragment
def page_access_management_fragment():
    """Fragment for page access management to prevent full page reruns."""

    # Load current configuration
    config = load_page_access_config()

    # Create tabs for different management views
    tab1, tab2 = st.tabs(["Configure Access", "View Configuration"])

    with tab1:
        # Get list of pages from ALL_PAGES (the single source of truth)
        pages = [page["file"] for page in ALL_PAGES]

        st.markdown("### Page Permissions")
        st.caption("Define access rules for each page using the table below. Changes are saved upon clicking 'Save Configuration'.")

        # --- Prepare data for st.data_editor ---
        data_for_editor = []
        for page_path in pages:
            page_name = page_path.split("/")[-1].replace(".py", "").replace("_", " ").title()
            page_config_from_file = config["pages"].get(page_path, {})

            current_roles = page_config_from_file.get("roles", [])
            is_public = page_config_from_file.get("access") == "public"

            row = {
                "Page": page_name,
                "Path": page_path,
                "Public": is_public
            }

            for role in AVAILABLE_ROLES:
                role_column_name = role.title()
                # If page is public, roles don't apply
                if is_public:
                    row[role_column_name] = False
                else:
                    row[role_column_name] = role in current_roles
            data_for_editor.append(row)

        df_for_editor = pd.DataFrame(data_for_editor)

        # --- Configure st.data_editor columns and order ---
        page_permission_column_config = {
            "Page": st.column_config.TextColumn("Page Name", help="The display name of the page.", disabled=True),
            "Path": None, # Hidden from display
            "Public": st.column_config.CheckboxColumn("Public", help="Accessible by anyone, no login required."),
        }

        final_column_order = ["Page", "Public"]
        admin_role_key_actual_title_case = None
        other_role_columns_title_case = []

        for role in AVAILABLE_ROLES:
            role_title_case = role.title()
            page_permission_column_config[role_title_case] = st.column_config.CheckboxColumn(
                role_title_case,
                help=f"Allow users with the '{role}' role."
            )
            if role.lower() == "admin":
                admin_role_key_actual_title_case = role_title_case
            else:
                other_role_columns_title_case.append(role_title_case)

        if admin_role_key_actual_title_case:
            final_column_order.append(admin_role_key_actual_title_case)

        final_column_order.extend(sorted(other_role_columns_title_case))

        # --- Display st.data_editor ---
        edited_df = st.data_editor(
            df_for_editor,
            column_config=page_permission_column_config,
            column_order=final_column_order,
            hide_index=True,
            use_container_width=True,
            key="page_permissions_editor_state"
        )


        # Default access setting
        st.markdown("#### Default Access")
        st.caption("Fallback for pages without specific configuration")

        default_access = st.selectbox(
            "Default access level",
            options=["authenticated", "public", "deny"],
            index=["authenticated", "public", "deny"].index(config.get("default_access", "authenticated")),
            help="authenticated: Any logged-in user can access | public: No authentication required | deny: No access unless explicitly configured",
            key="default_access_selectbox"
        )

        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("💾 Save Configuration", type="primary", use_container_width=True):
                # First, validate protected page constraints
                validation_errors = []

                for _, row_data in edited_df.iterrows():
                    page_path = row_data["Path"]
                    is_public_edited = row_data["Public"]

                    # Check home page constraint
                    if page_path == "views/home.py" and not is_public_edited:
                        validation_errors.append("❌ Home page must remain public.")

                    # Check auth admin constraints
                    elif page_path == "views/auth_admin.py":
                        if is_public_edited:
                            validation_errors.append("❌ Auth Admin page cannot be made public.")
                        elif admin_role_key_actual_title_case and not row_data.get(admin_role_key_actual_title_case, False):
                            validation_errors.append(f"❌ Auth Admin page must be accessible by the '{admin_role_key_actual_title_case}' role.")

                # If validation errors exist, show them and stop
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                    st.stop()

                # Continue with the rest of the save process
                updated_config = {"version": config["version"], "default_access": default_access, "pages": {}}

                # Process data from the edited dataframe
                for _, row_data in edited_df.iterrows():
                    page_path = row_data["Path"]
                    is_public_edited = row_data["Public"]

                    if is_public_edited:
                        updated_config["pages"][page_path] = {"access": "public"}
                    else:
                        selected_roles = []
                        for role in AVAILABLE_ROLES:
                            role_column_name = role.title()
                            if role_column_name in row_data and row_data[role_column_name]:
                                selected_roles.append(role)

                        if selected_roles:
                            updated_config["pages"][page_path] = {"roles": selected_roles}
                        else:
                            updated_config["pages"][page_path] = {} # Uses default access

                if save_page_access_config(updated_config):
                    st.success("Page access configuration updated successfully.", icon="✅")
                else:
                    st.error("Failed to save configuration. Please check the logs.")
                st.rerun() # This will only rerun the fragment now!

    with tab2:
        # Display current configuration
        st.markdown("### Current Configuration")

        # Show as JSON
        st.json(config)

        # Show effective access summary
        st.markdown("### Access Summary")

        access_summary = []
        for page_path, page_config in config["pages"].items():
            page_name = page_path.split("/")[-1].replace(".py", "").replace("_", " ").title()

            if page_config.get("access") == "public":
                access_type = "🌐 Public"
            elif "roles" in page_config:
                roles = page_config["roles"]
                access_type = f"🔐 {', '.join(roles)}"
            else:
                access_type = f"📋 Default ({config.get('default_access', 'authenticated')})"

            access_summary.append({
                "Page": page_name,
                "Path": page_path,
                "Access": access_type
            })

        st.dataframe(access_summary, use_container_width=True, hide_index=True)
# Call the fragment function
page_access_management_fragment()


# Auth0 Dashboard links
st.header("🔐 Advanced Management")
if AUTH0_DOMAIN:
    parts = AUTH0_DOMAIN.split('.')
    tenant = parts[0] if parts else ""
    region = parts[1] if len(parts) == 4 else "us"

st.write(f"For advanced user management tasks, use the [Auth0 Dashboard ↗️](https://manage.auth0.com/dashboard/{region}/{tenant}/users) or navigate to **User Management → Users**.")
if AUTH0_TEAM_LOGIN_URL:
    st.markdown(
        f"The Auth0 account holder can view **all tenants** and manage **team members** here: "
        f"[{AUTH0_TEAM_LOGIN_URL}]({AUTH0_TEAM_LOGIN_URL})"
    )
st.markdown(
    "**NOTE:** Auth0 Actions, such as the 'Post-Login Invite Verification' trigger, "
    "are integral to the authentication flow and may require review during auth-flow troubleshooting or updates."
)