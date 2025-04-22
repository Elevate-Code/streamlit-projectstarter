# ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️ THIS IS OBSOLETE, NEEDS TO BE UPDATED ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
# ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️ THIS IS OBSOLETE, NEEDS TO BE UPDATED ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

import streamlit as st
from functools import wraps
from typing import Optional, List, Callable
import os

"""
Currently, in is_allowed_user(), we have this logic flow:
1. First check if the user is in the whitelist (allowed_users)
2. If not in whitelist, check if their domain is allowed (allowed_domains)
3. Access is granted if either condition is true

In the future, we could extend this to check a database instead of secrets.toml

To use role-based access in the future, we could do something like:
```
@require_auth(roles=["admin"])
def admin_only_page():
    st.write("Admin only content")

# Or directly in a page
check_auth(required_roles=["admin", "manager"])
```
"""

def get_env_list(env_var: str) -> list:
    """Convert comma-separated environment variable to list, returning empty list if not set."""
    return os.getenv(env_var, "").split(",") if os.getenv(env_var) else []

def is_allowed_user(email: str) -> bool:
    """Check if user is allowed based on email domain or specific whitelist."""
    if not email:
        return False

    # Get allowed domains and users from environment variables
    allowed_domains = get_env_list("STREAMLIT_AUTH_ALLOWED_DOMAINS")
    allowed_users = get_env_list("STREAMLIT_AUTH_ALLOWED_EMAILS")

    # Check whitelist first
    if email.lower() in (user.lower() for user in allowed_users):
        return True

    # Then check domain
    domain = email.split('@')[-1].lower()
    return domain in (d.lower() for d in allowed_domains)

def check_auth(required_roles: Optional[List[str]] = None) -> None:
    """Check authentication and optionally roles, stopping execution if unauthorized.

    Args:
        required_roles: Optional list of roles required to access the page/component
    """
    if not st.experimental_user.is_logged_in:
        with st.sidebar:
            st.button("🔐 Login with Google", on_click=st.login, use_container_width=True)
            st.warning("Please log in to continue")
        st.stop()

    # Check if user is allowed
    if not is_allowed_user(st.experimental_user.email):
        st.error("🚫 You are not authorized to access this application - please contact the admin")
        with st.sidebar:
            st.button("🚪 Logout", on_click=st.logout, use_container_width=True)
        st.stop()

    # Future role checking logic here
    # if required_roles and not has_required_roles(required_roles):
    #     st.error("You don't have permission to access this page")
    #     st.stop()

def render_user_info() -> None:
    """Render current user info and logout button in sidebar."""
    with st.sidebar:
        st.write(f"Logged in as: {st.experimental_user.get('email')}")
        st.button("🚪 Logout", on_click=st.logout, use_container_width=True)

def require_auth(func: Optional[Callable] = None, *, roles: Optional[List[str]] = None) -> Callable:
    """Decorator to require authentication and optionally specific roles.

    Args:
        func: The function to wrap
        roles: Optional list of required roles
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            check_auth(roles)
            return f(*args, **kwargs)
        return wrapper

    if func is None:
        return decorator
    return decorator(func)